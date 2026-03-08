import uuid
from datetime import datetime

from pydantic import BaseModel


class ApprovalDecisionRequest(BaseModel):
    decision_reason: str


class ApprovalOut(BaseModel):
    id: uuid.UUID
    quote_id: uuid.UUID
    requested_by_user_id: uuid.UUID
    approver_user_id: uuid.UUID | None
    requested_price: float | None
    requested_discount: float | None
    status: str
    request_justification: str
    decision_reason: str | None
    created_at: datetime
    decided_at: datetime | None

    model_config = {"from_attributes": True}


class SimilarCaseOut(BaseModel):
    recommendation_id: str
    quote_id: str | None = None
    recommended_price: float
    win_probability: float | None = None
    confidence: float
    approval_status: str
    risk_level: str | None = None
    value_positioning_label: str | None = None
    timestamp: datetime


class ApprovalContextOut(BaseModel):
    approval: ApprovalOut
    quote_summary: dict
    ai_recommendation_summary: dict | None = None
    current_finance: dict | None = None
    requested_finance: dict | None = None
    policy_check: dict | None = None
    market_comparison_summary: dict | None = None
    similar_cases: list[SimilarCaseOut]
    recommended_action: str
