from datetime import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.db.models import ApprovalStatus, RoleEnum, UserAccountStatus, UserApprovalStatus


class RuleUpsertRequest(BaseModel):
    channel: str
    category: str
    margin_floor_percent: float = Field(ge=0, le=100)
    max_discount_percent: float = Field(ge=0, le=100)
    approval_required_below_margin_buffer: float = Field(ge=0, le=100)


class UserCreateRequest(BaseModel):
    name: str
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6)
    role: RoleEnum
    account_status: UserAccountStatus = UserAccountStatus.active

    @field_validator("email")
    @classmethod
    def validate_email_like(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email:
            raise ValueError("Invalid email format")
        local, _, domain = email.partition("@")
        if not local or not domain:
            raise ValueError("Invalid email format")
        return email


class AuditLogOut(BaseModel):
    id: str
    actor_user_id: str | None
    action: str
    entity_type: str
    entity_id: str
    old_json: dict | None
    new_json: dict | None
    reason: str | None
    model_version: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PendingUserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: RoleEnum
    approval_status: UserApprovalStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class UserApprovalDecisionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: RoleEnum
    approval_status: UserApprovalStatus
    account_status: UserAccountStatus
    approved_by_user_id: uuid.UUID | None
    approved_at: datetime | None
    approval_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserStatusUpdateRequest(BaseModel):
    account_status: UserAccountStatus


class AdminResetPasswordRequest(BaseModel):
    new_password: str | None = Field(default=None, min_length=6, max_length=128)


class AdminResetPasswordResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    message: str


class ModelRunOut(BaseModel):
    id: uuid.UUID
    run_type: str
    model_name: str
    model_version: str | None
    model_provider: str | None
    request_id: str | None
    status: str
    fallback_used: bool
    latency_ms: float | None
    input_hash: str | None
    related_quote_id: uuid.UUID | None
    related_product_id: uuid.UUID | None
    related_recommendation_id: uuid.UUID | None
    meta_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class AIRecommendationOut(BaseModel):
    id: uuid.UUID
    quote_id: uuid.UUID | None
    product_id: uuid.UUID
    recommended_price: float
    recommended_price_low: float | None
    recommended_price_high: float | None
    confidence: float
    win_probability: float | None
    model_version: str
    model_provider: str | None
    fallback_used: bool
    explanation_json: dict
    source_rule_ids_json: list
    source_document_ids_json: list
    finance_snapshot_id: uuid.UUID | None
    risk_level: str | None
    competitor_comparison_summary_json: dict
    value_positioning_label: str | None
    approved_by_user_id: uuid.UUID | None
    approval_status: ApprovalStatus
    timestamp: datetime

    model_config = {"from_attributes": True}


class GovernanceSummaryOut(BaseModel):
    pending_upload_reviews: int
    pending_policy_reviews: int
    active_pricebooks: int
    active_campaigns: int
    active_contracts: int
    active_rebate_programs: int
    model_run_failures: int
    ai_trace_count: int
    unmatched_competitor_records: int
    average_policy_confidence: float


class ReviewQueueItemOut(BaseModel):
    item_type: str
    item_id: str
    label: str
    status: str
    source_reference: str | None = None
    uploaded_at: datetime | None = None
    next_step: str | None = None


class DataQualityOut(BaseModel):
    upload_parse_failures: int
    uploads_needing_review: int
    reviews_pending_activation: int
    unmatched_competitor_records: int
    recommendations_with_fallback: int
    model_run_failures: int
    average_clause_confidence: float


class EnterpriseReadinessCheckOut(BaseModel):
    id: str
    category: str
    label: str
    status: Literal["pass", "warning", "fail"]
    detail: str
    action: str | None = None


class EnterpriseReadinessOut(BaseModel):
    score: int
    status: Literal["enterprise_ready", "attention_needed", "not_ready"]
    summary: str
    categories: dict[str, float]
    checks: list[EnterpriseReadinessCheckOut]
