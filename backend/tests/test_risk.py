from app.db.models import RiskLevel
from app.services.risk_engine import RiskInputs, requires_approval, score_risk


def test_risk_scoring_high_when_multiple_flags_triggered():
    risk = score_risk(
        RiskInputs(
            margin_percent=9,
            margin_floor_percent=10,
            discount_percent=18,
            ai_discount_center=9,
            stock_age_days=220,
            customer_tier="growth",
            confidence=0.42,
            manager_override_rate=0.5,
        )
    )
    assert risk == RiskLevel.high


def test_approval_gating_blocks_outside_band_and_high_risk():
    assert requires_approval(
        risk_level=RiskLevel.high,
        chosen_price=100,
        band_low=95,
        band_high=105,
        margin_percent=15,
        margin_floor_percent=10,
        approval_buffer=2,
    )

    assert requires_approval(
        risk_level=RiskLevel.low,
        chosen_price=90,
        band_low=95,
        band_high=105,
        margin_percent=15,
        margin_floor_percent=10,
        approval_buffer=2,
    )

