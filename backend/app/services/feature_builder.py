import json
from hashlib import sha256

from app.db.models import Customer, Product, StrategyMode

TIER_SCORE = {"strategic": 0.25, "core": 0.55, "growth": 0.8}
CHANNEL_SCORE = {"direct": 0.25, "distributor": 0.5, "project": 0.75, "retail": 0.9}
CATEGORY_SCORE = {"cement": 0.3, "steel": 0.5, "roofing": 0.65, "finishes": 0.8}
STRATEGY_SCORE = {
    StrategyMode.maximize_profit.value: 0.2,
    StrategyMode.clear_inventory.value: 0.6,
    StrategyMode.market_expansion.value: 0.9,
}
ELASTICITY_SCORE = {"low_sensitivity": 0.25, "medium_sensitivity": 0.55, "high_sensitivity": 0.85}

FEATURE_SCHEMA = [
    "customer_tier_score",
    "channel_score",
    "category_score",
    "quantity",
    "discount_percent",
    "stock_age_days",
    "stock_on_hand",
    "days_to_delivery",
    "strategy_score",
    "elasticity_score",
]


def classify_elasticity(historical_discount_tolerance: float) -> str:
    if historical_discount_tolerance <= 5:
        return "low_sensitivity"
    if historical_discount_tolerance <= 12:
        return "medium_sensitivity"
    return "high_sensitivity"


def build_feature_context(
    customer: Customer,
    product: Product,
    channel: str,
    quantity: int,
    stock_age_days: int,
    stock_on_hand: int,
    days_to_delivery: int | None,
    strategy_mode: StrategyMode,
    historical_discount_tolerance: float,
) -> dict:
    elasticity = classify_elasticity(historical_discount_tolerance)
    return {
        "customer_tier": customer.tier.value,
        "channel": channel,
        "product_category": product.category,
        "quantity": quantity,
        "stock_age_days": stock_age_days,
        "stock_on_hand": stock_on_hand,
        "days_to_delivery": days_to_delivery or 14,
        "strategy_mode": strategy_mode.value,
        "historical_discount_tolerance": historical_discount_tolerance,
        "elasticity_label": elasticity,
    }


def hash_features(features: dict) -> str:
    encoded = json.dumps(features, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def build_scoring_rows(base_context: dict, list_price: float, candidate_prices: list[float]) -> list[dict]:
    rows: list[dict] = []
    for price in candidate_prices:
        discount_percent = ((list_price - price) / list_price) * 100
        rows.append(
            {
                "customer_tier_score": TIER_SCORE.get(base_context["customer_tier"], 0.55),
                "channel_score": CHANNEL_SCORE.get(base_context["channel"], 0.5),
                "category_score": CATEGORY_SCORE.get(base_context["product_category"].lower(), 0.5),
                "quantity": float(base_context["quantity"]),
                "discount_percent": round(discount_percent, 4),
                "stock_age_days": float(base_context["stock_age_days"]),
                "stock_on_hand": float(base_context["stock_on_hand"]),
                "days_to_delivery": float(base_context["days_to_delivery"]),
                "strategy_score": STRATEGY_SCORE.get(base_context["strategy_mode"], 0.2),
                "elasticity_score": ELASTICITY_SCORE.get(base_context["elasticity_label"], 0.55),
            }
        )
    return rows
