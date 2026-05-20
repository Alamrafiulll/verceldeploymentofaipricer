from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.db.models import QuoteStatus, RiskLevel, StrategyMode


class QuoteItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    requested_price: float | None = Field(default=None, gt=0)
    requested_discount: float | None = Field(default=None, ge=0, le=100)
    delivery_date: date | None = None


class QuoteCreateRequest(BaseModel):
    customer_id: str
    channel: str
    strategy_mode: StrategyMode = StrategyMode.maximize_profit
    item: QuoteItemCreate


class QuoteListItem(BaseModel):
    id: str
    customer_name: str
    channel: str
    strategy_mode: StrategyMode
    status: QuoteStatus
    created_at: datetime
    updated_at: datetime


class CandidatePoint(BaseModel):
    price: float
    discount_percent: float
    margin_percent: float
    win_probability: float
    expected_profit: float
    allowed: bool


class RecommendationResponse(BaseModel):
    quote_id: str
    band_low: float
    band_high: float
    best_price: float
    suggested_discount_low: float
    suggested_discount_high: float
    win_probability: float
    expected_profit: float
    margin_percent: float
    confidence: float
    risk_level: RiskLevel
    safe_band: Literal["green", "yellow", "red"]
    explanation: dict
    explanation_levels: dict | None = None
    candidates: list[CandidatePoint]
    safe_price_range: dict | None = None
    true_margin_snapshot_summary: dict | None = None
    policy_entitlements_summary: list[dict] | None = None
    pricebook_compliance_summary: dict | None = None
    contract_pricing_summary: dict | None = None
    campaign_summary: dict | None = None
    campaign_evaluations: list[dict] | None = None
    market_comparison_summary: dict | None = None
    value_positioning_label: str | None = None
    next_best_action: str | None = None


class SaveQuoteDraftRequest(BaseModel):
    requested_price: float = Field(gt=0)
    strategy_mode: StrategyMode | None = None


class FinalizeQuoteRequest(BaseModel):
    final_price: float = Field(gt=0)
    reason: str | None = None


class RequestApprovalRequest(BaseModel):
    requested_price: float = Field(gt=0)
    requested_discount: float | None = Field(default=None, ge=0, le=100)
    justification: str = Field(min_length=3)


class QuoteDetailResponse(BaseModel):
    id: str
    created_by_user_id: str
    customer_id: str
    customer_name: str
    channel: str
    strategy_mode: StrategyMode
    status: QuoteStatus
    item: dict
    latest_recommendation: dict | None
    pricebook_compliance_summary: dict | None = None
    contract_pricing_summary: dict | None = None
    market_comparison_summary: dict | None = None
    created_at: datetime
    updated_at: datetime


class PolicyViolation(BaseModel):
    severity: Literal["low", "medium", "high"]
    code: str
    message: str
    source_document_id: str | None = None
    clause_id: str | None = None


class PolicyEntitlement(BaseModel):
    campaign_id: str
    campaign_name: str
    rule_type: str
    sku_codes: list[str]
    quantity: int
    source_document_id: str | None = None
    eligibility_status: str | None = None
    estimated_campaign_cost: float | None = None
    summary: str | None = None
    next_action: str | None = None
    discount_percent: float | None = None
    discount_amount: float | None = None
    bundle_skus: list[str] = Field(default_factory=list)


class QuotePolicyCheckResponse(BaseModel):
    quote_id: str
    checked_at: datetime
    pricebook_compliance_summary: dict | None = None
    contract_pricing_summary: dict | None = None
    campaign_summary: dict | None = None
    campaign_evaluations: list[dict] | None = None
    market_comparison_summary: dict | None = None
    recommended_action: str | None = None
    violations: list[PolicyViolation]
    entitlements: list[PolicyEntitlement]


class SimulateFinanceRequest(BaseModel):
    proposed_price: float = Field(gt=0)


class QuoteFinanceSnapshotResponse(BaseModel):
    quote_id: str
    proposed_price: float
    list_revenue_total: float
    discounted_revenue_total: float
    revenue_total: float
    cogs_total: float
    rebate_amount: float
    gift_cost_amount: float
    bundle_cost_amount: float
    promotion_allocation_amount: float
    campaign_cost_amount: float
    freight_amount: float
    fees_amount: float
    mdf_amount: float
    contract_effect_amount: float
    list_margin_amount: float
    price_discount_amount: float
    gross_margin_amount: float
    net_margin_amount: float
    net_margin_percent: float
    leakage_amount: float
    leakage_reasons_json: list[dict]
    leakage_flags_json: dict
    rebate_summary: dict | None = None
    contract_pricing_summary: dict | None = None
    created_at: datetime


class NegotiationLadderStep(BaseModel):
    step: int
    target_price: float
    message: str


class NegotiationAssistantResponse(BaseModel):
    quote_id: str
    strategy_summary: str
    concession_ladder: list[NegotiationLadderStep]
    guardrails: list[str]
    must_not_do: list[str]
    policy_refs: list[str]
