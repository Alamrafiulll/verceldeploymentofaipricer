from collections import defaultdict
from datetime import timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.deps import get_db, require_roles
from app.db.models import Campaign, ProductValueProfile, Quote, QuoteFinanceSnapshot, QuoteItem, QuoteStatus, RoleEnum, User
from app.schemas.analytics import KpiResponse, OverrideRow, SalesManagerBehaviorRow, SeriesPoint
from app.services.policy_enforcement import evaluate_quote_policies

router = APIRouter()


def _load_quotes(db: Session) -> list[Quote]:
    return list(
        db.scalars(
            select(Quote)
            .options(
                selectinload(Quote.items).joinedload(QuoteItem.product),
                joinedload(Quote.created_by),
                selectinload(Quote.recommendations),
            )
            .order_by(Quote.created_at.desc())
        ).all()
    )


@router.get("/kpis", response_model=KpiResponse)
def kpis(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> KpiResponse:
    quotes = _load_quotes(db)
    finalized = [q for q in quotes if q.status == QuoteStatus.finalized and q.items]
    approved = [q for q in quotes if q.status == QuoteStatus.approved]
    recommended = [q for q in quotes if q.status in {QuoteStatus.recommended, QuoteStatus.finalized, QuoteStatus.approved}]

    margins = [float(q.items[0].margin_percent or 0) for q in finalized if q.items[0].margin_percent is not None]
    avg_margin = sum(margins) / len(margins) if margins else 0.0

    durations = []
    for q in finalized:
        start = q.created_at
        end = q.updated_at
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        durations.append((end - start).total_seconds() / 3600)
    avg_decision_time = sum(durations) / len(durations) if durations else 0.0

    overrides = [
        q
        for q in finalized
        if q.items[0].final_price is not None
        and q.items[0].recommended_price is not None
        and abs(float(q.items[0].final_price) - float(q.items[0].recommended_price)) > 0.01
    ]

    win_rate_proxy = len(finalized) / len(recommended) if recommended else 0.0
    aging_inventory_addressed = sum(
        float((q.items[0].final_price or 0) * q.items[0].quantity)
        for q in finalized
        if q.items[0].product and getattr(q.items[0].product, "category", "")
    )
    finance_snapshots = list(db.scalars(select(QuoteFinanceSnapshot)).all())
    avg_leakage_amount = (
        sum(float(snapshot.leakage_amount) for snapshot in finance_snapshots) / len(finance_snapshots)
        if finance_snapshots
        else 0.0
    )
    recommendation_acceptance_rate = (
        max(0.0, 1 - (len(overrides) / len(finalized)))
        if finalized
        else 0.0
    )
    pricing_health_score = max(
        0.0,
        min(
            100.0,
            50.0
            + avg_margin
            + recommendation_acceptance_rate * 25
            - (avg_leakage_amount / 25 if avg_leakage_amount else 0)
            - (max(avg_decision_time - 24, 0) / 2),
        ),
    )

    return KpiResponse(
        average_margin_percent=round(avg_margin, 2),
        average_decision_time_hours=round(avg_decision_time, 2),
        override_rate=round((len(overrides) / len(finalized)) if finalized else 0.0, 4),
        approval_rate=round((len(approved) / len(quotes)) if quotes else 0.0, 4),
        win_rate_proxy=round(win_rate_proxy, 4),
        aging_inventory_addressed_value=round(aging_inventory_addressed, 2),
        pricing_health_score=round(pricing_health_score, 2),
        average_leakage_amount=round(avg_leakage_amount, 2),
        recommendation_acceptance_rate=round(recommendation_acceptance_rate, 4),
    )


@router.get("/discount-distribution", response_model=list[SeriesPoint])
def discount_distribution(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    quotes = _load_quotes(db)
    by_channel: dict[str, list[float]] = defaultdict(list)
    for q in quotes:
        if not q.items:
            continue
        discount = q.items[0].final_discount or q.items[0].recommended_discount_low
        if discount is None:
            continue
        by_channel[q.channel].append(float(discount))

    return [
        SeriesPoint(label=channel, value=round(sum(values) / len(values), 2))
        for channel, values in sorted(by_channel.items())
    ]


@router.get("/margin-by-category", response_model=list[SeriesPoint])
def margin_by_category(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    quotes = _load_quotes(db)
    by_category: dict[str, list[float]] = defaultdict(list)
    for q in quotes:
        if not q.items:
            continue
        item = q.items[0]
        if item.margin_percent is None or item.product is None:
            continue
        by_category[item.product.category].append(float(item.margin_percent))

    return [
        SeriesPoint(label=category, value=round(sum(values) / len(values), 2))
        for category, values in sorted(by_category.items())
    ]


@router.get("/overrides", response_model=list[OverrideRow])
def overrides(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[OverrideRow]:
    quotes = _load_quotes(db)
    rows: list[OverrideRow] = []
    for q in quotes:
        if not q.items:
            continue
        item = q.items[0]
        if item.final_price is None or item.recommended_price is None:
            continue
        if abs(float(item.final_price) - float(item.recommended_price)) <= 0.01:
            continue
        reason = None
        if q.recommendations:
            reason = q.recommendations[-1].gpt_outputs_json.get("approval_justification_suggestion")
        rows.append(
            OverrideRow(
                quote_id=str(q.id),
                sales_manager=q.created_by.name if q.created_by else "Unknown",
                ai_price=float(item.recommended_price),
                final_price=float(item.final_price),
                reason=reason,
            )
        )
    return rows


@router.get("/sales-manager-behavior", response_model=list[SalesManagerBehaviorRow])
def sales_manager_behavior(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SalesManagerBehaviorRow]:
    quotes = _load_quotes(db)
    by_manager: dict[str, list[Quote]] = defaultdict(list)
    for q in quotes:
        if q.created_by and q.created_by.role == RoleEnum.sales:
            by_manager[q.created_by.name].append(q)

    rows: list[SalesManagerBehaviorRow] = []
    for manager, manager_quotes in sorted(by_manager.items()):
        finalized = [q for q in manager_quotes if q.status == QuoteStatus.finalized and q.items]
        if not finalized:
            continue

        override_count = 0
        discount_vs_ai = []
        margins = []

        for q in finalized:
            item = q.items[0]
            if item.final_price is not None and item.recommended_price is not None and abs(float(item.final_price) - float(item.recommended_price)) > 0.01:
                override_count += 1
            if item.final_discount is not None and item.recommended_discount_low is not None and item.recommended_discount_high is not None:
                ai_center = (float(item.recommended_discount_low) + float(item.recommended_discount_high)) / 2
                discount_vs_ai.append(float(item.final_discount) - ai_center)
            if item.margin_percent is not None:
                margins.append(float(item.margin_percent))

        rows.append(
            SalesManagerBehaviorRow(
                sales_manager=manager,
                override_frequency=round(override_count / len(finalized), 4),
                avg_discount_vs_ai=round(sum(discount_vs_ai) / len(discount_vs_ai), 2) if discount_vs_ai else 0.0,
                avg_margin_percent=round(sum(margins) / len(margins), 2) if margins else 0.0,
            )
        )

    return rows


@router.get("/inventory-impact", response_model=list[SeriesPoint])
def inventory_impact(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    quotes = _load_quotes(db)
    values: dict[str, float] = defaultdict(float)
    for q in quotes:
        if not q.items:
            continue
        item = q.items[0]
        if item.final_price is None or item.product is None:
            continue
        values[item.product.sku] += float(item.final_price) * item.quantity

    top = sorted(values.items(), key=lambda x: x[1], reverse=True)[:10]
    return [SeriesPoint(label=sku, value=round(value, 2)) for sku, value in top]


@router.get("/leakage-over-time", response_model=list[SeriesPoint])
def leakage_over_time(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    snapshots = list(
        db.scalars(select(QuoteFinanceSnapshot).order_by(QuoteFinanceSnapshot.created_at.asc())).all()
    )
    by_day: dict[str, float] = defaultdict(float)
    for snapshot in snapshots:
        day = snapshot.created_at.date().isoformat()
        by_day[day] += float(snapshot.leakage_amount)
    return [SeriesPoint(label=day, value=value) for day, value in sorted(by_day.items())]


@router.get("/top-violation-codes", response_model=list[SeriesPoint])
def top_violation_codes(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    snapshots = list(db.scalars(select(QuoteFinanceSnapshot)).all())
    counts: dict[str, float] = defaultdict(float)
    for snapshot in snapshots:
        flags = snapshot.leakage_flags_json.get("flags", []) if snapshot.leakage_flags_json else []
        for flag in flags:
            code = flag.get("code", "unknown")
            counts[code] += 1
    top = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]
    return [SeriesPoint(label=code, value=value) for code, value in top]


@router.get("/margin-waterfall", response_model=list[SeriesPoint])
def margin_waterfall(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    snapshots = list(db.scalars(select(QuoteFinanceSnapshot)).all())
    if not snapshots:
        return [
            SeriesPoint(label="gross_margin_pct", value=0),
            SeriesPoint(label="net_margin_pct", value=0),
        ]

    list_margin_pcts = []
    gross_margin_pcts = []
    net_margin_pcts = []
    for snapshot in snapshots:
        revenue = float(snapshot.revenue_total)
        if revenue <= 0:
            continue
        list_revenue = float(snapshot.list_revenue_total or snapshot.revenue_total)
        if list_revenue > 0:
            list_margin_pcts.append(float(snapshot.list_margin_amount) / list_revenue * 100)
        gross_margin_pcts.append(float(snapshot.gross_margin_amount) / revenue * 100)
        net_margin_pcts.append(float(snapshot.net_margin_amount) / revenue * 100)

    return [
        SeriesPoint(
            label="list_margin_pct",
            value=round(sum(list_margin_pcts) / len(list_margin_pcts), 2) if list_margin_pcts else 0,
        ),
        SeriesPoint(
            label="gross_margin_pct",
            value=round(sum(gross_margin_pcts) / len(gross_margin_pcts), 2) if gross_margin_pcts else 0,
        ),
        SeriesPoint(
            label="net_margin_pct",
            value=round(sum(net_margin_pcts) / len(net_margin_pcts), 2) if net_margin_pcts else 0,
        ),
    ]


@router.get("/campaign-performance", response_model=list[SeriesPoint])
def campaign_performance(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    quotes = list(
        db.scalars(select(Quote).options(selectinload(Quote.items).joinedload(QuoteItem.product))).all()
    )
    campaigns = {str(campaign.id): campaign.name for campaign in db.scalars(select(Campaign)).all()}

    uptake: dict[str, float] = defaultdict(float)
    for quote in quotes:
        if not quote.items:
            continue
        result = evaluate_quote_policies(db=db, quote=quote, actor_user_id=None)
        for entitlement in result["entitlements"]:
            campaign_id = entitlement["campaign_id"]
            uptake[campaign_id] += float(entitlement.get("estimated_campaign_cost") or 1)

    rows = []
    for campaign_id, value in sorted(uptake.items(), key=lambda item: item[1], reverse=True):
        rows.append(SeriesPoint(label=campaigns.get(campaign_id, campaign_id), value=value))
    return rows


@router.get("/leakage-sources", response_model=list[SeriesPoint])
def leakage_sources(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    snapshots = list(db.scalars(select(QuoteFinanceSnapshot)).all())
    totals: dict[str, float] = defaultdict(float)
    for snapshot in snapshots:
        for reason in snapshot.leakage_reasons_json or []:
            label = str(reason.get("label") or reason.get("code") or "Unknown")
            totals[label] += float(reason.get("amount") or 0)
    top = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:10]
    return [SeriesPoint(label=label, value=round(value, 2)) for label, value in top]


@router.get("/competitor-positioning", response_model=list[SeriesPoint])
def competitor_positioning(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    profiles = list(db.scalars(select(ProductValueProfile)).all())
    counts: dict[str, float] = defaultdict(float)
    for profile in profiles:
        label = profile.positioning_label or "unclassified"
        counts[label] += 1
    return [SeriesPoint(label=label, value=value) for label, value in sorted(counts.items())]


@router.get("/category-profitability", response_model=list[SeriesPoint])
def category_profitability(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    snapshots = list(
        db.scalars(
            select(QuoteFinanceSnapshot)
            .options(joinedload(QuoteFinanceSnapshot.quote).selectinload(Quote.items).joinedload(QuoteItem.product))
        ).all()
    )
    totals: dict[str, float] = defaultdict(float)
    for snapshot in snapshots:
        quote = snapshot.quote
        if not quote or not quote.items or not quote.items[0].product:
            continue
        totals[quote.items[0].product.category] += float(snapshot.net_margin_amount)
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    return [SeriesPoint(label=label, value=round(value, 2)) for label, value in ranked]


@router.get("/approval-turnaround", response_model=list[SeriesPoint])
def approval_turnaround(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    quotes = _load_quotes(db)
    by_channel: dict[str, list[float]] = defaultdict(list)
    for quote in quotes:
        if quote.status not in {QuoteStatus.approved, QuoteStatus.rejected, QuoteStatus.finalized}:
            continue
        start = quote.created_at if quote.created_at.tzinfo else quote.created_at.replace(tzinfo=timezone.utc)
        end = quote.updated_at if quote.updated_at.tzinfo else quote.updated_at.replace(tzinfo=timezone.utc)
        by_channel[quote.channel].append((end - start).total_seconds() / 3600)
    return [
        SeriesPoint(label=channel, value=round(sum(values) / len(values), 2))
        for channel, values in sorted(by_channel.items())
        if values
    ]


@router.get("/recommendation-acceptance", response_model=list[SeriesPoint])
def recommendation_acceptance(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.executive, RoleEnum.admin, RoleEnum.approver)),
) -> list[SeriesPoint]:
    quotes = _load_quotes(db)
    accepted = 0
    overridden = 0
    pending = 0
    for quote in quotes:
        if not quote.items:
            continue
        item = quote.items[0]
        if item.final_price is None or item.recommended_price is None:
            pending += 1
            continue
        if abs(float(item.final_price) - float(item.recommended_price)) <= 0.01:
            accepted += 1
        else:
            overridden += 1
    return [
        SeriesPoint(label="accepted", value=accepted),
        SeriesPoint(label="overridden", value=overridden),
        SeriesPoint(label="pending", value=pending),
    ]
