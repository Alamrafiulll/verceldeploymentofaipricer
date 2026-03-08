import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import FreightAndFeesPolicy, Quote, QuoteFinanceSnapshot, QuoteItem
from app.services.audit_logger import log_audit
from app.services.campaign_engine import evaluate_campaigns
from app.services.contract_engine import apply_contract_pricing, evaluate_contract_pricing, resolve_applicable_contracts
from app.services.leakage_rules import build_leakage_summary
from app.services.policy_enforcement import evaluate_quote_policies
from app.services.rebate_engine import estimate_rebate_components


def _resolve_active_freight_policy(db: Session, channel: str) -> FreightAndFeesPolicy | None:
    rows = list(db.scalars(select(FreightAndFeesPolicy).where(FreightAndFeesPolicy.channel == channel)).all())
    if not rows:
        return None
    now = datetime.now(timezone.utc)
    for row in rows:
        start = row.effective_start
        end = row.effective_end
        if start and start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if start and now < start:
            continue
        if end and now > end:
            continue
        return row
    return rows[0]


def _load_quote(db: Session, quote_id: str) -> Quote:
    quote = db.scalar(
        select(Quote)
        .where(Quote.id == uuid.UUID(quote_id))
        .options(selectinload(Quote.items).joinedload(QuoteItem.product), selectinload(Quote.customer))
    )
    if not quote:
        raise ValueError("Quote not found")
    if not quote.items:
        raise ValueError("Quote has no items")
    return quote


def _to_float(value: float | None) -> float | None:
    return float(value) if value is not None else None


def compute_true_margin(
    db: Session,
    quote_id: str,
    proposed_price: float | None,
    actor_user_id: str | None = None,
) -> QuoteFinanceSnapshot:
    quote = _load_quote(db, quote_id)
    item = quote.items[0]
    product = item.product

    resolved_price = (
        proposed_price
        or _to_float(item.final_price)
        or _to_float(item.requested_price)
        or _to_float(item.recommended_price)
        or float(product.list_price)
    )
    quantity = item.quantity
    list_revenue_total = float(product.list_price) * quantity
    revenue_total = resolved_price * quantity
    cogs_total = float(product.unit_cost) * quantity
    list_margin_amount = list_revenue_total - cogs_total
    price_discount_amount = max(0.0, list_revenue_total - revenue_total)
    gross_margin_amount = revenue_total - cogs_total

    contracts = resolve_applicable_contracts(db=db, customer_id=str(quote.customer_id))
    contract_bounds = apply_contract_pricing(contracts=contracts, product_id=str(product.id))
    contract_summary = evaluate_contract_pricing(
        db=db,
        quote=quote,
        price_override=resolved_price,
    )

    rebate = estimate_rebate_components(
        db=db,
        quote_channel=quote.channel,
        customer_tier=quote.customer.tier.value,
        revenue_total=revenue_total,
    )
    campaign_result = evaluate_campaigns(
        db=db,
        quote=quote,
        price_override=resolved_price,
    )
    freight_policy = _resolve_active_freight_policy(db=db, channel=quote.channel)
    freight_percent = float(freight_policy.freight_percent) if freight_policy else 0.0
    fees_percent = float(freight_policy.fees_percent) if freight_policy else 0.0
    freight_amount = revenue_total * freight_percent / 100
    fees_amount = revenue_total * fees_percent / 100
    gift_cost_amount = float(campaign_result.get("gift_cost_amount") or 0)
    bundle_cost_amount = float(campaign_result.get("bundle_cost_amount") or 0)
    promotion_allocation_amount = float(campaign_result.get("promotion_allocation_amount") or 0)
    contract_effect_amount = 0.0
    ceiling_price = contract_summary.get("ceiling_price")
    if ceiling_price is not None:
        contract_effect_amount = max(0.0, (float(product.list_price) - float(ceiling_price)) * quantity)

    net_margin_amount = (
        list_margin_amount
        - price_discount_amount
        - rebate["rebate_amount"]
        - campaign_result["campaign_cost_amount"]
        - rebate["mdf_amount"]
        - freight_amount
        - fees_amount
    )
    net_margin_percent = (net_margin_amount / revenue_total * 100) if revenue_total else 0

    policy_result = evaluate_quote_policies(
        db=db,
        quote=quote,
        actor_user_id=None,
        price_override=resolved_price,
    )
    leakage_summary = build_leakage_summary(
        proposed_price=resolved_price,
        list_price=float(product.list_price),
        quantity=quantity,
        pricebook_summary=policy_result["pricebook_compliance_summary"],
        contract_summary=contract_summary,
        rebate_summary=rebate,
        gift_cost_amount=gift_cost_amount,
        bundle_cost_amount=bundle_cost_amount,
        promotion_allocation_amount=promotion_allocation_amount,
        freight_amount=freight_amount,
        fees_amount=fees_amount,
        mdf_amount=float(rebate["mdf_amount"]),
        net_margin_amount=net_margin_amount,
        policy_violations=policy_result["violations"],
    )

    snapshot = db.scalar(select(QuoteFinanceSnapshot).where(QuoteFinanceSnapshot.quote_id == quote.id))
    if not snapshot:
        snapshot = QuoteFinanceSnapshot(
            quote_id=quote.id,
            proposed_price=resolved_price,
            list_revenue_total=list_revenue_total,
            revenue_total=revenue_total,
            cogs_total=cogs_total,
            rebate_amount=rebate["rebate_amount"],
            gift_cost_amount=gift_cost_amount,
            bundle_cost_amount=bundle_cost_amount,
            promotion_allocation_amount=promotion_allocation_amount,
            campaign_cost_amount=campaign_result["campaign_cost_amount"],
            freight_amount=freight_amount,
            fees_amount=fees_amount,
            mdf_amount=rebate["mdf_amount"],
            contract_effect_amount=contract_effect_amount,
            list_margin_amount=list_margin_amount,
            price_discount_amount=price_discount_amount,
            gross_margin_amount=gross_margin_amount,
            net_margin_amount=net_margin_amount,
            net_margin_percent=net_margin_percent,
            leakage_amount=leakage_summary["leakage_amount"],
            leakage_reasons_json=leakage_summary["leakage_reasons"],
            leakage_flags_json={
                "flags": leakage_summary["flags"],
                "contract_bounds": contract_bounds,
                "contract_summary": contract_summary,
                "policy_violations": policy_result["violations"],
                "rebate_summary": rebate,
                "campaign_summary": campaign_result["campaign_summary"],
                "campaign_evaluations": campaign_result["campaign_evaluations"],
                "leakage_amount": leakage_summary["leakage_amount"],
                "leakage_reasons": leakage_summary["leakage_reasons"],
            },
        )
        db.add(snapshot)
    else:
        snapshot.proposed_price = resolved_price
        snapshot.list_revenue_total = list_revenue_total
        snapshot.revenue_total = revenue_total
        snapshot.cogs_total = cogs_total
        snapshot.rebate_amount = rebate["rebate_amount"]
        snapshot.gift_cost_amount = gift_cost_amount
        snapshot.bundle_cost_amount = bundle_cost_amount
        snapshot.promotion_allocation_amount = promotion_allocation_amount
        snapshot.campaign_cost_amount = campaign_result["campaign_cost_amount"]
        snapshot.freight_amount = freight_amount
        snapshot.fees_amount = fees_amount
        snapshot.mdf_amount = rebate["mdf_amount"]
        snapshot.contract_effect_amount = contract_effect_amount
        snapshot.list_margin_amount = list_margin_amount
        snapshot.price_discount_amount = price_discount_amount
        snapshot.gross_margin_amount = gross_margin_amount
        snapshot.net_margin_amount = net_margin_amount
        snapshot.net_margin_percent = net_margin_percent
        snapshot.leakage_amount = leakage_summary["leakage_amount"]
        snapshot.leakage_reasons_json = leakage_summary["leakage_reasons"]
        snapshot.leakage_flags_json = {
            "flags": leakage_summary["flags"],
            "contract_bounds": contract_bounds,
            "contract_summary": contract_summary,
            "policy_violations": policy_result["violations"],
            "rebate_summary": rebate,
            "campaign_summary": campaign_result["campaign_summary"],
            "campaign_evaluations": campaign_result["campaign_evaluations"],
            "leakage_amount": leakage_summary["leakage_amount"],
            "leakage_reasons": leakage_summary["leakage_reasons"],
        }

    log_audit(
        db=db,
        actor_user_id=actor_user_id,
        action="finance_simulated",
        entity_type="quote",
        entity_id=str(quote.id),
        new_json={
            "proposed_price": resolved_price,
            "net_margin_percent": round(net_margin_percent, 2),
            "rebate_amount": round(rebate["rebate_amount"], 2),
            "display_incentive_amount": round(rebate["display_incentive_amount"], 2),
            "campaign_cost_amount": round(campaign_result["campaign_cost_amount"], 2),
            "leakage_amount": round(leakage_summary["leakage_amount"], 2),
        },
    )

    db.commit()
    db.refresh(snapshot)
    return snapshot
