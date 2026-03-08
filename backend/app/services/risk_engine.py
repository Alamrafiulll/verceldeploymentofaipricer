from dataclasses import dataclass

from app.db.models import RiskLevel


@dataclass
class RiskInputs:
    margin_percent: float
    margin_floor_percent: float
    discount_percent: float
    ai_discount_center: float
    stock_age_days: int
    customer_tier: str
    confidence: float
    manager_override_rate: float


def score_risk(inputs: RiskInputs) -> RiskLevel:
    score = 0

    margin_buffer = inputs.margin_percent - inputs.margin_floor_percent
    if margin_buffer < 1:
        score += 3
    elif margin_buffer < 3:
        score += 2

    discount_deviation = inputs.discount_percent - inputs.ai_discount_center
    if discount_deviation > 6:
        score += 3
    elif discount_deviation > 3:
        score += 2

    if inputs.stock_age_days > 180:
        score += 2
    elif inputs.stock_age_days > 120:
        score += 1

    tier_weight = {"strategic": 0, "core": 1, "growth": 2}.get(inputs.customer_tier, 1)
    score += tier_weight

    if inputs.confidence < 0.45:
        score += 2
    elif inputs.confidence < 0.6:
        score += 1

    if inputs.manager_override_rate > 0.4:
        score += 2
    elif inputs.manager_override_rate > 0.25:
        score += 1

    if score >= 9:
        return RiskLevel.high
    if score >= 5:
        return RiskLevel.medium
    return RiskLevel.low


def requires_approval(
    risk_level: RiskLevel,
    chosen_price: float,
    band_low: float,
    band_high: float,
    margin_percent: float,
    margin_floor_percent: float,
    approval_buffer: float,
) -> bool:
    outside_band = chosen_price < band_low or chosen_price > band_high
    below_buffer = margin_percent < (margin_floor_percent + approval_buffer)
    return risk_level == RiskLevel.high or outside_band or below_buffer
