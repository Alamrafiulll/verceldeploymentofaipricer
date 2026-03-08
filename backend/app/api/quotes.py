import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.deps import get_current_user, get_db, require_roles
from app.db.models import Quote, QuoteFinanceSnapshot, QuoteItem, QuoteStatus, RoleEnum, User
from app.schemas.quote import (
    FinalizeQuoteRequest,
    NegotiationAssistantResponse,
    QuoteFinanceSnapshotResponse,
    QuoteCreateRequest,
    QuoteDetailResponse,
    QuoteListItem,
    QuotePolicyCheckResponse,
    RecommendationResponse,
    RequestApprovalRequest,
    SimulateFinanceRequest,
)
from app.services.audit_logger import log_audit
from app.services.contract_engine import evaluate_contract_pricing
from app.services.finance_engine import compute_true_margin
from app.services.market_comparison_engine import analyze_product_market_position
from app.services.model_run_logger import log_model_run
from app.services.negotiation_assistant import generate_negotiation_guidance
from app.services.policy_enforcement import evaluate_quote_policies
from app.services.pricebook_enforcement import evaluate_pricebook_compliance
from app.services.pricing_service import pricing_service

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_quote(
    payload: QuoteCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin)),
) -> dict:
    quote = Quote(
        created_by_user_id=user.id,
        customer_id=uuid.UUID(payload.customer_id),
        channel=payload.channel,
        strategy_mode=payload.strategy_mode,
        status=QuoteStatus.draft,
    )
    db.add(quote)
    db.flush()

    item = QuoteItem(
        quote_id=quote.id,
        product_id=uuid.UUID(payload.item.product_id),
        quantity=payload.item.quantity,
        requested_price=payload.item.requested_price,
        requested_discount=payload.item.requested_discount,
    )
    db.add(item)

    log_audit(
        db=db,
        actor_user_id=str(user.id),
        action="quote_created",
        entity_type="quote",
        entity_id=str(quote.id),
        new_json=payload.model_dump(mode="json"),
    )
    db.commit()

    return {"id": str(quote.id), "status": quote.status.value}


@router.get("", response_model=list[QuoteListItem])
def list_quotes(
    mine: bool = Query(default=True),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin, RoleEnum.approver)),
) -> list[QuoteListItem]:
    stmt = select(Quote).options(joinedload(Quote.customer)).order_by(Quote.created_at.desc())
    if mine and user.role == RoleEnum.sales:
        stmt = stmt.where(Quote.created_by_user_id == user.id)

    rows = db.scalars(stmt).all()
    return [
        QuoteListItem(
            id=str(q.id),
            customer_name=q.customer.name,
            channel=q.channel,
            strategy_mode=q.strategy_mode,
            status=q.status,
            created_at=q.created_at,
            updated_at=q.updated_at,
        )
        for q in rows
    ]


def _authorize_quote_view(quote: Quote, user: User) -> None:
    if user.role in {RoleEnum.admin, RoleEnum.approver, RoleEnum.executive}:
        return
    if user.role == RoleEnum.sales and quote.created_by_user_id == user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/{quote_id}", response_model=QuoteDetailResponse)
def get_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuoteDetailResponse:
    quote = db.scalar(
        select(Quote)
        .where(Quote.id == uuid.UUID(quote_id))
        .options(selectinload(Quote.items), joinedload(Quote.customer), selectinload(Quote.recommendations))
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    _authorize_quote_view(quote, user)

    item = quote.items[0]
    latest = sorted(quote.recommendations, key=lambda r: r.created_at)[-1] if quote.recommendations else None
    market_summary = analyze_product_market_position(db=db, product_id=str(item.product_id))

    return QuoteDetailResponse(
        id=str(quote.id),
        created_by_user_id=str(quote.created_by_user_id),
        customer_id=str(quote.customer_id),
        customer_name=quote.customer.name,
        channel=quote.channel,
        strategy_mode=quote.strategy_mode,
        status=quote.status,
        item={
            "id": str(item.id),
            "product_id": str(item.product_id),
            "quantity": item.quantity,
            "requested_price": float(item.requested_price) if item.requested_price is not None else None,
            "requested_discount": float(item.requested_discount) if item.requested_discount is not None else None,
            "recommended_price": float(item.recommended_price) if item.recommended_price is not None else None,
            "recommended_band_low": float(item.recommended_band_low) if item.recommended_band_low is not None else None,
            "recommended_band_high": float(item.recommended_band_high) if item.recommended_band_high is not None else None,
            "final_price": float(item.final_price) if item.final_price is not None else None,
            "final_discount": float(item.final_discount) if item.final_discount is not None else None,
            "margin_percent": float(item.margin_percent) if item.margin_percent is not None else None,
            "expected_profit": float(item.expected_profit) if item.expected_profit is not None else None,
            "win_probability": float(item.win_probability) if item.win_probability is not None else None,
            "confidence": float(item.confidence) if item.confidence is not None else None,
            "risk_level": item.risk_level.value if item.risk_level else None,
        },
        latest_recommendation=(
            {
                "foundry": latest.foundry_outputs_json,
                "optimizer": latest.optimizer_outputs_json,
                "gpt": latest.gpt_outputs_json,
                "model_version": latest.model_version,
            }
            if latest
            else None
        ),
        pricebook_compliance_summary=evaluate_pricebook_compliance(db=db, quote=quote),
        contract_pricing_summary=evaluate_contract_pricing(db=db, quote=quote),
        market_comparison_summary=(
            {
                "market_comparison_summary": market_summary.market_comparison_summary,
                "value_positioning_label": market_summary.value_positioning_label,
                "recommended_strategy": market_summary.recommended_strategy,
                "value_score": market_summary.value_score,
                "competitor_count": market_summary.competitor_count,
            }
            if market_summary
            else None
        ),
        created_at=quote.created_at,
        updated_at=quote.updated_at,
    )


@router.post("/{quote_id}/recommend", response_model=RecommendationResponse)
def recommend_quote(
    quote_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin)),
) -> RecommendationResponse:
    quote = db.scalar(select(Quote).where(Quote.id == uuid.UUID(quote_id)))
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if user.role == RoleEnum.sales and quote.created_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        return pricing_service.recommend(
            db=db,
            quote_id=quote_id,
            actor_user_id=str(user.id),
            request_id=getattr(request.state, "request_id", "n/a"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{quote_id}/policy-check", response_model=QuotePolicyCheckResponse)
def policy_check(
    quote_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuotePolicyCheckResponse:
    quote = db.scalar(
        select(Quote)
        .where(Quote.id == uuid.UUID(quote_id))
        .options(selectinload(Quote.items).joinedload(QuoteItem.product))
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    _authorize_quote_view(quote, user)
    result = evaluate_quote_policies(db=db, quote=quote, actor_user_id=str(user.id))
    db.commit()
    return QuotePolicyCheckResponse(**result)


def _snapshot_to_response(snapshot: QuoteFinanceSnapshot) -> QuoteFinanceSnapshotResponse:
    return QuoteFinanceSnapshotResponse(
        quote_id=str(snapshot.quote_id),
        proposed_price=float(snapshot.proposed_price),
        list_revenue_total=float(snapshot.list_revenue_total),
        discounted_revenue_total=float(snapshot.revenue_total),
        revenue_total=float(snapshot.revenue_total),
        cogs_total=float(snapshot.cogs_total),
        rebate_amount=float(snapshot.rebate_amount),
        gift_cost_amount=float(snapshot.gift_cost_amount),
        bundle_cost_amount=float(snapshot.bundle_cost_amount),
        promotion_allocation_amount=float(snapshot.promotion_allocation_amount),
        campaign_cost_amount=float(snapshot.campaign_cost_amount),
        freight_amount=float(snapshot.freight_amount),
        fees_amount=float(snapshot.fees_amount),
        mdf_amount=float(snapshot.mdf_amount),
        contract_effect_amount=float(snapshot.contract_effect_amount),
        list_margin_amount=float(snapshot.list_margin_amount),
        price_discount_amount=float(snapshot.price_discount_amount),
        gross_margin_amount=float(snapshot.gross_margin_amount),
        net_margin_amount=float(snapshot.net_margin_amount),
        net_margin_percent=float(snapshot.net_margin_percent),
        leakage_amount=float(snapshot.leakage_amount),
        leakage_reasons_json=list(snapshot.leakage_reasons_json or []),
        leakage_flags_json=snapshot.leakage_flags_json,
        rebate_summary=snapshot.leakage_flags_json.get("rebate_summary"),
        contract_pricing_summary=snapshot.leakage_flags_json.get("contract_summary"),
        created_at=snapshot.created_at,
    )


@router.get("/{quote_id}/finance", response_model=QuoteFinanceSnapshotResponse)
def get_quote_finance(
    quote_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuoteFinanceSnapshotResponse:
    quote = db.scalar(select(Quote).where(Quote.id == uuid.UUID(quote_id)))
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    _authorize_quote_view(quote, user)

    snapshot = db.scalar(select(QuoteFinanceSnapshot).where(QuoteFinanceSnapshot.quote_id == quote.id))
    if not snapshot:
        snapshot = compute_true_margin(
            db=db,
            quote_id=quote_id,
            proposed_price=None,
            actor_user_id=str(user.id),
        )
    return _snapshot_to_response(snapshot)


@router.post("/{quote_id}/simulate-finance", response_model=QuoteFinanceSnapshotResponse)
def simulate_quote_finance(
    quote_id: str,
    payload: SimulateFinanceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuoteFinanceSnapshotResponse:
    quote = db.scalar(select(Quote).where(Quote.id == uuid.UUID(quote_id)))
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    _authorize_quote_view(quote, user)

    snapshot = compute_true_margin(
        db=db,
        quote_id=quote_id,
        proposed_price=payload.proposed_price,
        actor_user_id=str(user.id),
    )
    return _snapshot_to_response(snapshot)


@router.get("/{quote_id}/negotiation-assistant", response_model=NegotiationAssistantResponse)
def negotiation_assistant(
    quote_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NegotiationAssistantResponse:
    quote = db.scalar(
        select(Quote)
        .where(Quote.id == uuid.UUID(quote_id))
        .options(selectinload(Quote.items).joinedload(QuoteItem.product))
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    _authorize_quote_view(quote, user)

    item = quote.items[0]
    best_price = float(item.recommended_price or item.requested_price or item.final_price or item.product.list_price)
    band_low = float(item.recommended_band_low or best_price)
    band_high = float(item.recommended_band_high or best_price)

    policy_result = evaluate_quote_policies(db=db, quote=quote, actor_user_id=None)
    finance_snapshot = db.scalar(select(QuoteFinanceSnapshot).where(QuoteFinanceSnapshot.quote_id == quote.id))
    if not finance_snapshot:
        finance_snapshot = compute_true_margin(
            db=db,
            quote_id=quote_id,
            proposed_price=best_price,
            actor_user_id=str(user.id),
        )

    policy_refs = [
        violation["source_document_id"]
        for violation in policy_result["violations"]
        if violation.get("source_document_id")
    ]
    context = {
        "quote_id": quote_id,
        "band_low": band_low,
        "band_high": band_high,
        "best_price": best_price,
        "risk_level": item.risk_level.value if item.risk_level else "medium",
        "net_margin_percent": float(finance_snapshot.net_margin_percent),
        "policy_refs": sorted(set(policy_refs)),
    }
    output = generate_negotiation_guidance(
        context=context,
        request_id=getattr(request.state, "request_id", "negotiation-assistant"),
    )
    log_model_run(
        db=db,
        run_type="negotiation_assistant",
        model_name="foundry_negotiation_assistant",
        status="completed",
        request_id=getattr(request.state, "request_id", "negotiation-assistant"),
        meta_json={"ladder_steps": len(output.get("concession_ladder", []))},
    )

    log_audit(
        db=db,
        actor_user_id=str(user.id),
        action="negotiation_assistant_generated",
        entity_type="quote",
        entity_id=quote_id,
        new_json={"band_low": band_low, "band_high": band_high},
    )
    db.commit()
    return NegotiationAssistantResponse(quote_id=quote_id, **output)


@router.post("/{quote_id}/finalize")
def finalize_quote(
    quote_id: str,
    payload: FinalizeQuoteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin)),
) -> dict:
    quote = db.scalar(select(Quote).where(Quote.id == uuid.UUID(quote_id)))
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if user.role == RoleEnum.sales and quote.created_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        updated = pricing_service.finalize_quote(
            db=db,
            quote_id=quote_id,
            actor_user_id=str(user.id),
            final_price=payload.final_price,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"id": str(updated.id), "status": updated.status.value}


@router.post("/{quote_id}/request-approval")
def request_approval(
    quote_id: str,
    payload: RequestApprovalRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.sales, RoleEnum.admin)),
) -> dict:
    quote = db.scalar(select(Quote).where(Quote.id == uuid.UUID(quote_id)).options(selectinload(Quote.items)))
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if user.role == RoleEnum.sales and quote.created_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        approval = pricing_service.request_approval(
            db=db,
            quote_id=quote_id,
            actor_user_id=str(user.id),
            requested_price=payload.requested_price,
            requested_discount=payload.requested_discount,
            justification=payload.justification,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"approval_id": str(approval.id), "status": approval.status.value}
