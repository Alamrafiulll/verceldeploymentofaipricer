import uuid
import logging

from sqlalchemy.orm import Session

from app.db.models import Product
from app.services.ml_service import predict_price
from app.services.recommendation_trace_service import create_ai_recommendation_trace

logger = logging.getLogger("app")

# Channel multipliers for pricing adjustments
CHANNEL_MULTIPLIERS = {
    "direct": 1.0,
    "distributor": 0.92,
    "project": 0.88,
}


def _build_rationale(
    product: Product,
    predicted_price: float,
    margin: float,
    discount_percent: float,
    channel: str,
) -> str:
    """Generate a Smart 'Why' Rationale for the recommendation."""
    parts = []

    # Price positioning
    price_vs_list = ((float(product.list_price) - predicted_price) / float(product.list_price)) * 100
    if price_vs_list > 0:
        parts.append(
            f"Recommended {price_vs_list:.1f}% below list price (RM {float(product.list_price):.2f}) "
            f"to optimize for the '{channel}' channel."
        )
    else:
        parts.append(f"Recommended at list price for the '{channel}' channel.")

    # Margin commentary
    if margin >= 25:
        parts.append(f"Strong margin of {margin:.1f}% ensures healthy profitability.")
    elif margin >= 15:
        parts.append(f"Moderate margin of {margin:.1f}% balances competitiveness and profit.")
    elif margin >= 10:
        parts.append(f"Thin margin of {margin:.1f}% — consider holding firm on price.")
    else:
        parts.append(f"⚠️ Low margin of {margin:.1f}% — risk of unprofitable deal. Review urgently.")

    # Discount impact
    if discount_percent > 8:
        parts.append(
            f"The {discount_percent:.1f}% discount scenario reflects competitive pressure. "
            "Consider volume-based justification."
        )

    # Channel-specific advice
    if channel == "distributor":
        parts.append("Distributor pricing applies a 8% channel discount from list price.")
    elif channel == "project":
        parts.append("Project pricing applies a 12% channel discount for bulk/contract deals.")

    return " ".join(parts)


def generate_price(
    product_id: uuid.UUID | str,
    discount_percent: float,
    db: Session,
    actor_user_id: str | None = None,
    channel: str = "direct",
) -> dict | None:
    if isinstance(product_id, str):
        try:
            product_id = uuid.UUID(product_id)
        except ValueError:
            return None

    product = db.get(Product, product_id)
    if not product:
        return None

    channel_multiplier = CHANNEL_MULTIPLIERS.get(channel, 1.0)

    payload = {
        "cost": float(product.unit_cost),
        "current_price": float(product.list_price) * channel_multiplier,
        "category": product.category,
        "discount_percent": float(discount_percent),
    }
    prediction = predict_price(payload)
    predicted_price = float(prediction["recommended_price"])
    confidence = float(prediction["confidence"])
    model_version = str(prediction.get("model_version", "deterministic-fallback-v1"))

    # Apply channel multiplier to the predicted price
    predicted_price = round(predicted_price * channel_multiplier, 2)

    margin = ((predicted_price - float(product.unit_cost)) / predicted_price) * 100 if predicted_price else 0

    # Build smart rationale
    rationale = _build_rationale(product, predicted_price, margin, discount_percent, channel)

    # Simple explanation (backward compatible)
    if discount_percent > 8:
        explanation = "Higher discount scenario considered due to competitive pressure."
    elif margin < 10:
        explanation = "Low margin warning. Consider adjusting price upward."
    else:
        explanation = "Price optimized from historical behavior and current product economics."

    create_ai_recommendation_trace(
        db=db,
        product_id=product.id,
        recommended_price=predicted_price,
        confidence=confidence,
        model_version=model_version,
        quote_id=None,
    )
    db.commit()

    return {
        "product_id": str(product.id),
        "predicted_price": round(predicted_price, 2),
        "confidence": round(confidence, 4),
        "explanation": explanation,
        "model_version": model_version,
        "margin_percent": round(margin, 2),
        "rationale": rationale,
        "channel": channel,
        "unit_cost": round(float(product.unit_cost), 2),
        "list_price": round(float(product.list_price), 2),
    }

