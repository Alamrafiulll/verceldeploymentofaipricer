from dataclasses import dataclass

from app.db.models import StrategyMode


@dataclass
class OptimizerInput:
    list_price: float
    unit_cost: float
    quantity: int
    max_discount_percent: float
    margin_floor_percent: float
    candidate_step_percent: float
    probabilities: list[float]
    confidence: float
    strategy_mode: StrategyMode
    stock_age_days: int
    tolerance: float


def generate_candidate_prices(
    list_price: float,
    max_discount_percent: float,
    step_percent: float,
) -> list[float]:
    floor_price = list_price * (1 - max_discount_percent / 100)
    candidates: list[float] = []

    price = list_price
    while price >= floor_price:
        candidates.append(round(price, 2))
        price *= 1 - step_percent

    rounded = {
        round(list_price, 0),
        round(list_price * 0.95, 0),
        round(list_price * 0.9, 0),
        round(list_price * 0.85, 0),
    }
    for point in rounded:
        if floor_price <= point <= list_price:
            candidates.append(round(float(point), 2))

    return sorted(set(candidates))


def _objective_score(
    expected_profit: float,
    win_probability: float,
    stock_age_days: int,
    strategy_mode: StrategyMode,
) -> float:
    if strategy_mode == StrategyMode.clear_inventory:
        return expected_profit + (stock_age_days * 0.8 * win_probability)
    if strategy_mode == StrategyMode.market_expansion:
        return expected_profit * 0.8 + (win_probability * 1000)
    return expected_profit


def optimize_expected_profit(data: OptimizerInput, candidate_prices: list[float]) -> dict:
    if len(candidate_prices) != len(data.probabilities):
        raise ValueError("Candidate price and probability lengths must match")

    points = []
    for price, win_probability in zip(candidate_prices, data.probabilities):
        margin_percent = ((price - data.unit_cost) / price) * 100 if price > 0 else 0
        allowed = margin_percent >= data.margin_floor_percent
        expected_profit = (price - data.unit_cost) * data.quantity * win_probability
        objective = _objective_score(
            expected_profit,
            win_probability,
            data.stock_age_days,
            data.strategy_mode,
        )
        discount_percent = ((data.list_price - price) / data.list_price) * 100

        points.append(
            {
                "price": round(price, 2),
                "discount_percent": round(discount_percent, 2),
                "margin_percent": round(margin_percent, 2),
                "win_probability": round(win_probability, 4),
                "expected_profit": round(expected_profit, 2),
                "objective": round(objective, 2),
                "allowed": allowed,
            }
        )

    allowed_points = [p for p in points if p["allowed"]]
    if not allowed_points:
        raise ValueError("No candidate price satisfies margin floor")

    best = max(allowed_points, key=lambda p: p["objective"])

    max_expected_profit = max(p["expected_profit"] for p in allowed_points)
    threshold = max_expected_profit * data.tolerance

    sorted_points = sorted(allowed_points, key=lambda p: p["price"])
    best_idx = next(i for i, p in enumerate(sorted_points) if p["price"] == best["price"])

    left = best_idx
    while left > 0 and sorted_points[left - 1]["expected_profit"] >= threshold:
        left -= 1

    right = best_idx
    while right < len(sorted_points) - 1 and sorted_points[right + 1]["expected_profit"] >= threshold:
        right += 1

    band_low = sorted_points[left]["price"]
    band_high = sorted_points[right]["price"]

    return {
        "best": best,
        "band_low": band_low,
        "band_high": band_high,
        "suggested_discount_low": round(((data.list_price - band_high) / data.list_price) * 100, 2),
        "suggested_discount_high": round(((data.list_price - band_low) / data.list_price) * 100, 2),
        "confidence": round(data.confidence, 4),
        "points": points,
    }
