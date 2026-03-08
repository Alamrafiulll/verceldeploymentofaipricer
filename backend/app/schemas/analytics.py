from pydantic import BaseModel


class KpiResponse(BaseModel):
    average_margin_percent: float
    average_decision_time_hours: float
    override_rate: float
    approval_rate: float
    win_rate_proxy: float
    aging_inventory_addressed_value: float
    pricing_health_score: float
    average_leakage_amount: float
    recommendation_acceptance_rate: float


class SeriesPoint(BaseModel):
    label: str
    value: float


class OverrideRow(BaseModel):
    quote_id: str
    sales_manager: str
    ai_price: float
    final_price: float
    reason: str | None


class SalesManagerBehaviorRow(BaseModel):
    sales_manager: str
    override_frequency: float
    avg_discount_vs_ai: float
    avg_margin_percent: float
