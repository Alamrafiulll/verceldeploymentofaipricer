from app.db.models import StrategyMode
from app.services.optimization_engine import (
    OptimizerInput,
    generate_candidate_prices,
    optimize_expected_profit,
)


def test_candidate_generation_has_bounds_and_uniques():
    candidates = generate_candidate_prices(list_price=100.0, max_discount_percent=10, step_percent=0.01)
    assert candidates
    assert min(candidates) >= 90.0
    assert max(candidates) <= 100.0
    assert len(candidates) == len(set(candidates))


def test_optimizer_respects_margin_floor_and_picks_best_allowed():
    candidates = [90.0, 95.0, 100.0]
    probs = [0.95, 0.7, 0.5]

    result = optimize_expected_profit(
        OptimizerInput(
            list_price=100.0,
            unit_cost=88.0,
            quantity=10,
            max_discount_percent=12,
            margin_floor_percent=8.0,
            candidate_step_percent=0.01,
            probabilities=probs,
            confidence=0.7,
            strategy_mode=StrategyMode.maximize_profit,
            stock_age_days=90,
            tolerance=0.98,
        ),
        candidates,
    )

    assert result["best"]["price"] in [95.0, 100.0]
    assert result["best"]["margin_percent"] >= 8.0


def test_band_is_contiguous_near_peak():
    candidates = [90.0, 92.0, 94.0, 96.0, 98.0]
    probs = [0.9, 0.85, 0.78, 0.62, 0.48]

    result = optimize_expected_profit(
        OptimizerInput(
            list_price=100.0,
            unit_cost=70.0,
            quantity=25,
            max_discount_percent=15,
            margin_floor_percent=12,
            candidate_step_percent=0.01,
            probabilities=probs,
            confidence=0.75,
            strategy_mode=StrategyMode.maximize_profit,
            stock_age_days=50,
            tolerance=0.97,
        ),
        candidates,
    )

    assert result["band_low"] <= result["best"]["price"] <= result["band_high"]

