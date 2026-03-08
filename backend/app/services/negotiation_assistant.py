import json
import logging
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import get_settings

logger = logging.getLogger("app")


class NegotiationStepModel(BaseModel):
    step: int = Field(ge=1, le=5)
    target_price: float = Field(gt=0)
    message: str = Field(min_length=3)


class NegotiationResponseModel(BaseModel):
    strategy_summary: str = Field(min_length=5)
    concession_ladder: list[NegotiationStepModel] = Field(default_factory=list, min_length=1)
    guardrails: list[str] = Field(default_factory=list)
    must_not_do: list[str] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)


def _is_azure_openai_endpoint(endpoint_url: str) -> bool:
    host = urlparse(endpoint_url).netloc.lower()
    return "openai.azure.com" in host


def _extract_text_from_response(data: dict[str, Any]) -> str | None:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    if isinstance(data.get("output"), list):
        text_parts: list[str] = []
        for block in data["output"]:
            if not isinstance(block, dict):
                continue
            content = block.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        text_parts.append(item["text"])
        if text_parts:
            return "".join(text_parts)
    if isinstance(data.get("choices"), list) and data["choices"]:
        message = data["choices"][0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
    return None


def _fallback(context: dict[str, Any]) -> dict[str, Any]:
    band_low = float(context["band_low"])
    band_high = float(context["band_high"])
    best_price = float(context["best_price"])
    mid_price = round((best_price + band_low) / 2, 2)
    return {
        "strategy_summary": (
            f"Start at RM {band_high:.2f}, anchor value, and protect floor at RM {band_low:.2f}."
        ),
        "concession_ladder": [
            {"step": 1, "target_price": round(band_high, 2), "message": "Anchor with premium position."},
            {"step": 2, "target_price": round(best_price, 2), "message": "Trade price for confirmed volume."},
            {"step": 3, "target_price": round(mid_price, 2), "message": "Offer limited-time concession with payment terms."},
            {"step": 4, "target_price": round(band_low, 2), "message": "Final floor aligned to margin and policy guardrails."},
        ],
        "guardrails": [
            f"Do not go below RM {band_low:.2f}.",
            "Keep discounts within approved policy and contract boundaries.",
            "Escalate to approval workflow for out-of-band requests.",
        ],
        "must_not_do": [
            "Do not promise pricing outside approved range.",
            "Do not remove campaign exclusions.",
            "Do not commit rebates not in active programs.",
        ],
        "policy_refs": context.get("policy_refs", []),
    }


def generate_negotiation_guidance(context: dict[str, Any], request_id: str) -> dict[str, Any]:
    settings = get_settings()
    fallback = _fallback(context)
    endpoint = settings.foundry_endpoint_url
    api_key = settings.foundry_api_key
    if not endpoint or not api_key:
        return fallback

    headers = {"Content-Type": "application/json", "x-request-id": request_id}
    if _is_azure_openai_endpoint(endpoint):
        headers["api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"

    schema_hint = {
        "strategy_summary": "string",
        "concession_ladder": [{"step": 1, "target_price": 1000.0, "message": "string"}],
        "guardrails": ["string"],
        "must_not_do": ["string"],
        "policy_refs": ["string"],
    }
    system_prompt = (
        "You are an enterprise negotiation copilot. Return strict JSON only. "
        "Use only numeric values provided in context. Do not invent numbers. "
        f"Schema: {json.dumps(schema_hint, ensure_ascii=True)}"
    )
    user_content = json.dumps(context, ensure_ascii=True)

    if "/responses" in endpoint:
        body = {
            "model": settings.foundry_model_name,
            "instructions": system_prompt,
            "input": user_content,
            "temperature": 0.1,
        }
    else:
        body = {
            "model": settings.foundry_model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
        }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(endpoint, json=body, headers=headers)
            response.raise_for_status()
            content = _extract_text_from_response(response.json())
            if not content:
                return fallback
            parsed = json.loads(content)
            validated = NegotiationResponseModel.model_validate(parsed)

            band_low = float(context["band_low"])
            band_high = float(context["band_high"])
            for step in validated.concession_ladder:
                if step.target_price < band_low or step.target_price > band_high:
                    raise ValueError("Negotiation ladder target out of allowed range")
            return validated.model_dump()
    except (httpx.HTTPError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        logger.exception(
            {
                "event": "negotiation_assistant_fallback",
                "request_id": request_id,
                "error": str(exc),
            }
        )
        return fallback
