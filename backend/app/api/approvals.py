import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, require_roles
from app.db.models import AIRecommendation, Approval, ApprovalStatus, Quote, QuoteItem, RoleEnum, User
from app.schemas.approval import ApprovalContextOut, ApprovalDecisionRequest, ApprovalOut, SimilarCaseOut
from app.services.finance_engine import compute_true_margin
from app.services.market_comparison_engine import analyze_product_market_position
from app.services.policy_enforcement import evaluate_quote_policies
from app.services.pricing_service import pricing_service

router = APIRouter()


@router.get("", response_model=list[ApprovalOut])
def list_approvals(
    status: str = Query(default="pending"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.approver, RoleEnum.admin)),
) -> list[Approval]:
    stmt = select(Approval)
    if status:
        try:
            parsed_status = ApprovalStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid approval status") from exc
        stmt = stmt.where(Approval.status == parsed_status)
    stmt = stmt.order_by(Approval.created_at.desc())
    return list(db.scalars(stmt).all())


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
def approve(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.approver, RoleEnum.admin)),
) -> Approval:
    try:
        return pricing_service.decide_approval(
            db=db,
            approval_id=approval_id,
            actor_user_id=str(user.id),
            approve=True,
            decision_reason=payload.decision_reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
def reject(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.approver, RoleEnum.admin)),
) -> Approval:
    try:
        return pricing_service.decide_approval(
            db=db,
            approval_id=approval_id,
            actor_user_id=str(user.id),
            approve=False,
            decision_reason=payload.decision_reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{approval_id}/context", response_model=ApprovalContextOut)
def approval_context(
    approval_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.approver, RoleEnum.admin)),
) -> ApprovalContextOut:
    try:
        parsed_approval_id = uuid.UUID(approval_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid approval id") from exc

    approval = db.scalar(select(Approval).where(Approval.id == parsed_approval_id))
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    quote = db.scalar(
        select(Quote)
        .where(Quote.id == approval.quote_id)
        .options(selectinload(Quote.items).joinedload(QuoteItem.product), selectinload(Quote.recommendations), selectinload(Quote.customer))
    )
    if not quote or not quote.items:
        raise HTTPException(status_code=404, detail="Quote not found for approval")

    item = quote.items[0]
    policy_check = evaluate_quote_policies(db=db, quote=quote, actor_user_id=None, price_override=approval.requested_price)
    current_finance = compute_true_margin(db=db, quote_id=str(quote.id), proposed_price=None, actor_user_id=None)
    requested_finance = compute_true_margin(
        db=db,
        quote_id=str(quote.id),
        proposed_price=float(approval.requested_price) if approval.requested_price is not None else None,
        actor_user_id=None,
    )
    market_summary = analyze_product_market_position(db=db, product_id=str(item.product_id))

    similar_case_rows = list(
        db.scalars(
            select(AIRecommendation)
            .where(AIRecommendation.product_id == item.product_id)
            .order_by(AIRecommendation.timestamp.desc())
            .limit(6)
        ).all()
    )
    similar_cases = [
        SimilarCaseOut(
            recommendation_id=str(row.id),
            quote_id=str(row.quote_id) if row.quote_id else None,
            recommended_price=float(row.recommended_price),
            win_probability=float(row.win_probability) if row.win_probability is not None else None,
            confidence=float(row.confidence),
            approval_status=row.approval_status.value,
            risk_level=row.risk_level,
            value_positioning_label=row.value_positioning_label,
            timestamp=row.timestamp,
        )
        for row in similar_case_rows
    ]

    ai_recommendation_summary = None
    if quote.recommendations:
        latest = sorted(quote.recommendations, key=lambda row: row.created_at)[-1]
        optimizer = latest.optimizer_outputs_json or {}
        ai_recommendation_summary = {
            "model_version": latest.model_version,
            "recommended_price": optimizer.get("best", {}).get("price"),
            "recommended_price_low": optimizer.get("band_low"),
            "recommended_price_high": optimizer.get("band_high"),
            "confidence": optimizer.get("confidence"),
        }

    recommended_action = "Approve only if the business case justifies the leakage and policy impact."
    if requested_finance.net_margin_percent >= 12 and not policy_check["violations"]:
        recommended_action = "Approve if the requested price aligns with account strategy and approval authority."
    elif policy_check["violations"]:
        recommended_action = "Review policy source references and exception risk before deciding."

    return ApprovalContextOut(
        approval=approval,
        quote_summary={
            "quote_id": str(quote.id),
            "customer_name": quote.customer.name if quote.customer else None,
            "channel": quote.channel,
            "status": quote.status.value,
            "product_name": item.product.name if item.product else None,
            "product_id": str(item.product_id),
            "quantity": item.quantity,
        },
        ai_recommendation_summary=ai_recommendation_summary,
        current_finance={
            "proposed_price": float(current_finance.proposed_price),
            "net_margin_percent": float(current_finance.net_margin_percent),
            "net_margin_amount": float(current_finance.net_margin_amount),
            "leakage_amount": float(current_finance.leakage_amount),
        },
        requested_finance={
            "proposed_price": float(requested_finance.proposed_price),
            "net_margin_percent": float(requested_finance.net_margin_percent),
            "net_margin_amount": float(requested_finance.net_margin_amount),
            "leakage_amount": float(requested_finance.leakage_amount),
            "leakage_reasons": requested_finance.leakage_reasons_json,
        },
        policy_check=policy_check,
        market_comparison_summary=(
            {
                "market_comparison_summary": market_summary.market_comparison_summary,
                "recommended_strategy": market_summary.recommended_strategy,
                "value_positioning_label": market_summary.value_positioning_label,
                "value_score": market_summary.value_score,
            }
            if market_summary
            else None
        ),
        similar_cases=similar_cases,
        recommended_action=recommended_action,
    )
