import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger("app")


def predict_price(payload: dict[str, Any]) -> dict[str, float | str]:
    """
    Lightweight ML scoring helper for sandbox pricing endpoint.
    If AZURE_ENDPOINT/AZURE_API_KEY are not configured or call fails,
    falls back to deterministic local estimate.
    """
    settings = get_settings()

    azure_endpoint = getattr(settings, "azure_endpoint", None)
    azure_api_key = getattr(settings, "azure_api_key", None)

    cost = float(payload.get("cost", 0))
    current_price = float(payload.get("current_price", 0))

    if azure_endpoint and azure_api_key:
        headers = {
            "Authorization": f"Bearer {azure_api_key}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(azure_endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                recommended_price = float(
                    data.get("recommended_price", data.get("predicted_price", current_price or cost))
                )
                confidence = float(data.get("confidence", 0.75))
                model_version = str(data.get("model_version") or settings.win_model_version)
                return {
                    "recommended_price": round(recommended_price, 2),
                    "confidence": round(max(0.0, min(confidence, 1.0)), 4),
                    "model_version": model_version,
                }
        except Exception as exc:
            logger.exception({"event": "sandbox_ml_fallback", "error": str(exc)})

    # deterministic fallback
    baseline = max(cost * 1.15, current_price)
    confidence = 0.62
    return {
        "recommended_price": round(baseline, 2),
        "confidence": confidence,
        "model_version": "deterministic-fallback-v1",
    }
