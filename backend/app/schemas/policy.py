from datetime import datetime
import uuid
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.models import (
    CampaignRuleType,
    CampaignStatus,
    ContractStatus,
    PolicyClauseType,
    PolicyDocumentStatus,
    PolicyDocumentType,
    PriceBookChannel,
)


class PolicyUploadRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    doc_type: PolicyDocumentType
    text: str = Field(min_length=5)
    source_uri: str | None = Field(default=None, max_length=1024)
    source_uploaded_file_id: str | None = None
    effective_start: datetime | None = None
    effective_end: datetime | None = None
    status: PolicyDocumentStatus = PolicyDocumentStatus.draft
    auto_create_campaign: bool = True


class PolicyClauseOut(BaseModel):
    id: uuid.UUID
    clause_type: PolicyClauseType
    structured_json: dict
    raw_text: str
    confidence: float
    policy_source_reference: str | None = None

    model_config = {"from_attributes": True}


class PolicyDocumentOut(BaseModel):
    id: uuid.UUID
    title: str
    doc_type: PolicyDocumentType
    source_uri: str | None
    file_hash: str
    uploaded_by_user_id: uuid.UUID
    source_uploaded_file_id: uuid.UUID | None = None
    uploaded_at: datetime
    effective_start: datetime | None
    effective_end: datetime | None
    auto_create_campaign: bool = False
    review_notes: str | None = None
    reviewed_by_user_id: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    status: PolicyDocumentStatus
    review_status: str | None = None
    clause_count: int = 0
    average_clause_confidence: float = 0.0
    policy_source_reference: str | None = None
    next_step: str | None = None
    clauses: list[PolicyClauseOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PolicyReviewAction(str, Enum):
    save_draft = "save_draft"
    activate = "activate"
    archive = "archive"


class PolicyClauseReviewInput(BaseModel):
    clause_type: PolicyClauseType
    structured_json: dict = Field(default_factory=dict)
    raw_text: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class PolicyReviewUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    source_uri: str | None = Field(default=None, max_length=1024)
    effective_start: datetime | None = None
    effective_end: datetime | None = None
    auto_create_campaign: bool | None = None
    review_notes: str | None = None
    clauses: list[PolicyClauseReviewInput] | None = None
    action: PolicyReviewAction = PolicyReviewAction.save_draft

    model_config = {"extra": "forbid"}


class PriceBookItemInput(BaseModel):
    product_id: str
    list_price: float = Field(gt=0)
    notes: str | None = None


class PriceBookUploadRequest(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    channel: PriceBookChannel
    currency: str = Field(default="RM", min_length=1, max_length=16)
    source_document_id: str | None = None
    effective_start: datetime | None = None
    effective_end: datetime | None = None
    items: list[PriceBookItemInput] = Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class PriceBookItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    list_price: float
    notes: str | None

    model_config = {"from_attributes": True}


class PriceBookOut(BaseModel):
    id: uuid.UUID
    name: str
    channel: PriceBookChannel
    currency: str
    effective_start: datetime | None
    effective_end: datetime | None
    source_document_id: uuid.UUID | None
    uploaded_by_user_id: uuid.UUID | None
    uploaded_by_name: str | None = None
    uploaded_by_email: str | None = None
    created_at: datetime
    items: list[PriceBookItemOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class CampaignRuleCreateRequest(BaseModel):
    rule_type: CampaignRuleType
    eligibility_json: dict = Field(default_factory=dict)
    exclusion_json: dict = Field(default_factory=dict)
    entitlement_json: dict = Field(default_factory=dict)


class CampaignCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    source_document_id: str
    effective_start: datetime | None = None
    effective_end: datetime | None = None
    status: CampaignStatus = CampaignStatus.active


class CampaignRuleOut(BaseModel):
    id: uuid.UUID
    rule_type: CampaignRuleType
    eligibility_json: dict
    exclusion_json: dict
    entitlement_json: dict

    model_config = {"from_attributes": True}


class CampaignOut(BaseModel):
    id: uuid.UUID
    name: str
    source_document_id: uuid.UUID
    effective_start: datetime | None
    effective_end: datetime | None
    status: CampaignStatus
    rules: list[CampaignRuleOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RebateProgramOut(BaseModel):
    id: uuid.UUID
    name: str
    channel: str | None
    tier_rates_json: dict
    mdf_percent: float
    display_incentive_percent: float
    manager_discretion_warning: str | None
    retroactive_incentive: bool
    program_meta_json: dict
    effective_start: datetime | None
    effective_end: datetime | None
    source_document_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContractLineInput(BaseModel):
    product_id: str | None = None
    sku: str | None = None
    floor_price: float = Field(gt=0)
    ceiling_price: float = Field(gt=0)
    discount_cap_percent: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def validate_identifiers_and_bounds(self) -> "ContractLineInput":
        if not self.product_id and not self.sku:
            raise ValueError("Each contract line requires product_id or sku")
        if self.floor_price > self.ceiling_price:
            raise ValueError("Contract floor price cannot exceed ceiling price")
        return self


class ContractUploadRequest(BaseModel):
    customer_id: str
    name: str = Field(min_length=3, max_length=255)
    source_document_id: str | None = None
    source_uploaded_file_id: str | None = None
    effective_start: datetime | None = None
    effective_end: datetime | None = None
    status: ContractStatus = ContractStatus.active
    text: str | None = None
    lines: list[ContractLineInput] = Field(default_factory=list)


class ContractLineOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    floor_price: float
    ceiling_price: float
    discount_cap_percent: float | None

    model_config = {"from_attributes": True}


class ContractOut(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str | None = None
    name: str
    effective_start: datetime | None
    effective_end: datetime | None
    status: ContractStatus
    source_document_id: uuid.UUID | None
    source_uploaded_file_id: uuid.UUID | None
    contract_source_reference: str | None = None
    created_at: datetime
    lines: list[ContractLineOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
