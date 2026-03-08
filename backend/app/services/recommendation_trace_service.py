import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AIRecommendation, ApprovalStatus


def create_ai_recommendation_trace(
    db: Session,
    *,
    product_id: uuid.UUID,
    recommended_price: float,
    confidence: float,
    model_version: str,
    recommended_price_low: float | None = None,
    recommended_price_high: float | None = None,
    win_probability: float | None = None,
    model_provider: str | None = None,
    fallback_used: bool = False,
    explanation_json: dict | None = None,
    source_rule_ids: list[str] | None = None,
    source_document_ids: list[str] | None = None,
    finance_snapshot_id: uuid.UUID | None = None,
    risk_level: str | None = None,
    competitor_comparison_summary: dict | None = None,
    value_positioning_label: str | None = None,
    quote_id: uuid.UUID | None = None,
) -> AIRecommendation:
    trace = AIRecommendation(
        quote_id=quote_id,
        product_id=product_id,
        recommended_price=round(float(recommended_price), 2),
        recommended_price_low=round(float(recommended_price_low), 2) if recommended_price_low is not None else None,
        recommended_price_high=round(float(recommended_price_high), 2) if recommended_price_high is not None else None,
        confidence=float(confidence),
        win_probability=float(win_probability) if win_probability is not None else None,
        model_version=model_version,
        model_provider=model_provider,
        fallback_used=fallback_used,
        explanation_json=explanation_json or {},
        source_rule_ids_json=source_rule_ids or [],
        source_document_ids_json=source_document_ids or [],
        finance_snapshot_id=finance_snapshot_id,
        risk_level=risk_level,
        competitor_comparison_summary_json=competitor_comparison_summary or {},
        value_positioning_label=value_positioning_label,
        approval_status=ApprovalStatus.pending,
    )
    db.add(trace)
    return trace


def update_quote_trace_status(
    db: Session,
    *,
    quote_id: uuid.UUID,
    approval_status: ApprovalStatus,
    approved_by_user_id: uuid.UUID | None,
) -> int:
    traces = list(
        db.scalars(
            select(AIRecommendation).where(
                AIRecommendation.quote_id == quote_id,
                AIRecommendation.approval_status == ApprovalStatus.pending,
            )
        ).all()
    )
    for trace in traces:
        trace.approval_status = approval_status
        trace.approved_by_user_id = approved_by_user_id
    return len(traces)
