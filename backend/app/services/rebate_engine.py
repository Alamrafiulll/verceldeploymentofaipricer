from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RebateProgram


def _sortable_timestamp(value: datetime | None) -> float:
    if value is None:
        return 0.0
    normalized = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return normalized.timestamp()


def _is_effective(
    as_of: datetime,
    effective_start: datetime | None,
    effective_end: datetime | None,
) -> bool:
    start = effective_start
    end = effective_end
    if start and start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if start and as_of < start:
        return False
    if end and as_of > end:
        return False
    return True


def estimate_rebate_components(
    db: Session,
    quote_channel: str,
    customer_tier: str,
    revenue_total: float,
    as_of: datetime | None = None,
) -> dict:
    check_time = as_of or datetime.now(timezone.utc)
    programs = list(db.scalars(select(RebateProgram)).all())
    applicable = [
        program
        for program in programs
        if (program.channel is None or program.channel == quote_channel)
        and _is_effective(check_time, program.effective_start, program.effective_end)
    ]

    if not applicable:
        return {
            "program_id": None,
            "program_name": None,
            "source_document_id": None,
            "rebate_rate_percent": 0.0,
            "retroactive_rebate_percent": 0.0,
            "manager_discretion_percent": 0.0,
            "display_incentive_percent": 0.0,
            "mdf_percent": 0.0,
            "rebate_amount": 0.0,
            "mdf_amount": 0.0,
            "retroactive_rebate_amount": 0.0,
            "manager_discretion_amount": 0.0,
            "display_incentive_amount": 0.0,
            "manager_discretion_warning": None,
            "retroactive_incentive": False,
        }

    applicable.sort(
        key=lambda program: (
            0 if program.channel == quote_channel else 1,
            -_sortable_timestamp(program.effective_start),
            -_sortable_timestamp(program.created_at),
        )
    )
    best = applicable[0]
    tier_rates = best.tier_rates_json or {}
    rebate_rate = float(
        tier_rates.get(customer_tier)
        or tier_rates.get(customer_tier.lower())
        or tier_rates.get("default")
        or tier_rates.get("all")
        or 0
    )
    meta = best.program_meta_json or {}
    retroactive_rebate_percent = float(meta.get("retroactive_rate_percent") or 0)
    manager_discretion_percent = float(meta.get("manager_discretion_percent") or 0)
    display_incentive_percent = float(best.display_incentive_percent or 0)
    mdf_percent = float(best.mdf_percent or 0)
    rebate_amount = revenue_total * rebate_rate / 100
    retroactive_rebate_amount = revenue_total * retroactive_rebate_percent / 100
    manager_discretion_amount = revenue_total * manager_discretion_percent / 100
    display_incentive_amount = revenue_total * display_incentive_percent / 100
    mdf_amount = revenue_total * mdf_percent / 100
    standard_rebate_amount = rebate_amount
    standard_mdf_amount = mdf_amount
    return {
        "program_id": str(best.id),
        "program_name": best.name,
        "source_document_id": str(best.source_document_id) if best.source_document_id else None,
        "rebate_rate_percent": rebate_rate,
        "retroactive_rebate_percent": retroactive_rebate_percent,
        "manager_discretion_percent": manager_discretion_percent,
        "display_incentive_percent": display_incentive_percent,
        "mdf_percent": mdf_percent,
        "standard_rebate_amount": standard_rebate_amount,
        "standard_mdf_amount": standard_mdf_amount,
        "rebate_amount": standard_rebate_amount + retroactive_rebate_amount + manager_discretion_amount,
        "mdf_amount": standard_mdf_amount + display_incentive_amount,
        "retroactive_rebate_amount": retroactive_rebate_amount,
        "manager_discretion_amount": manager_discretion_amount,
        "display_incentive_amount": display_incentive_amount,
        "manager_discretion_warning": best.manager_discretion_warning,
        "retroactive_incentive": bool(best.retroactive_incentive),
    }
