import json
import logging
import time
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = logging.getLogger("app")


class ExplanationResponse(BaseModel):
    short_reason: str = Field(min_length=5)
    top_drivers: list[str] = Field(default_factory=list)
    negotiation_tips: list[str] = Field(default_factory=list)
    approval_justification_suggestion: str | None = None
    executive_summary: str | None = None


class FoundryClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def _is_azure_openai_endpoint(endpoint_url: str) -> bool:
        host = urlparse(endpoint_url).netloc.lower()
        return "openai.azure.com" in host

    def _build_headers(self, endpoint_url: str, request_id: str) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "x-request-id": request_id,
        }
        if self._is_azure_openai_endpoint(endpoint_url):
            headers["api-key"] = self.settings.foundry_api_key or ""
        else:
            headers["Authorization"] = f"Bearer {self.settings.foundry_api_key}"
        return headers

    def _fallback(self, payload: dict[str, Any]) -> dict[str, Any]:
        best_price = payload.get("best_price")
        margin = payload.get("margin_percent")
        win = payload.get("win_probability")
        strategy_mode = payload.get("strategy_mode")
        risk_level = payload.get("risk_level")
        return {
            "short_reason": (
                f"Price {best_price:.2f} balances win probability {win:.1%} "
                f"and margin {margin:.2f}% under {strategy_mode}."
            ),
            "top_drivers": [
                f"Strategy mode: {strategy_mode}",
                f"Risk level assessed as {risk_level}",
                f"Inventory age is {payload.get('stock_age_days')} days",
            ],
            "negotiation_tips": [
                "Anchor at band high and trade down only for volume commitments.",
                "Use inventory age and delivery certainty as negotiation levers.",
                "Escalate quickly if customer asks beyond safe discount range.",
            ],
            "approval_justification_suggestion": "Requested price improves strategic account retention while preserving floor margin.",
            "executive_summary": "Recommendation follows policy and maximizes expected profit in the allowed band.",
        }

    @retry(wait=wait_exponential(multiplier=0.5, min=1, max=4), stop=stop_after_attempt(3), reraise=True)
    def _call_foundry(self, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        endpoint_url = self.settings.foundry_endpoint_url or ""
        headers = self._build_headers(endpoint_url=endpoint_url, request_id=request_id)
        system_prompt = (
            "You are a pricing strategist assistant. Do not change any numbers. "
            "Return strict JSON only with keys: short_reason, top_drivers, negotiation_tips, "
            "approval_justification_suggestion, executive_summary."
        )
        user_content = json.dumps(payload, ensure_ascii=True)
        if "/responses" in endpoint_url:
            body = {
                "model": self.settings.foundry_model_name,
                "instructions": system_prompt,
                "input": user_content,
                "temperature": 0.1,
            }
        else:
            body = {
                "model": self.settings.foundry_model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.1,
            }
        started = time.perf_counter()
        with httpx.Client(timeout=12.0) as client:
            response = client.post(endpoint_url, json=body, headers=headers)
            response.raise_for_status()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                {
                    "event": "foundry_explanation_call",
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "status": response.status_code,
                }
            )
            return response.json()

    @staticmethod
    def _extract_text_from_response(data: dict[str, Any]) -> str | None:
        if isinstance(data.get("output_text"), str):
            return data["output_text"]

        if isinstance(data.get("output"), list):
            text_parts: list[str] = []
            for block in data["output"]:
                if not isinstance(block, dict):
                    continue
                if isinstance(block.get("text"), str):
                    text_parts.append(block["text"])
                content_blocks = block.get("content")
                if isinstance(content_blocks, list):
                    for item in content_blocks:
                        if not isinstance(item, dict):
                            continue
                        if isinstance(item.get("text"), str):
                            text_parts.append(item["text"])
            if text_parts:
                return "".join(text_parts)

        return None

    def _parse_response(self, data: dict[str, Any]) -> dict[str, Any]:
        content: str | None = self._extract_text_from_response(data)
        if isinstance(data.get("choices"), list) and data["choices"]:
            message = data["choices"][0].get("message", {})
            raw_content = message.get("content")
            if isinstance(raw_content, str):
                content = raw_content
            elif isinstance(raw_content, list):
                text_parts = []
                for block in raw_content:
                    if isinstance(block, dict) and isinstance(block.get("text"), str):
                        text_parts.append(block["text"])
                content = "".join(text_parts) if text_parts else None

        if not content and "content" in data:
            raw_content = data["content"]
            if isinstance(raw_content, str):
                content = raw_content
            elif isinstance(raw_content, list):
                text_parts = []
                for block in raw_content:
                    if isinstance(block, dict) and isinstance(block.get("text"), str):
                        text_parts.append(block["text"])
                content = "".join(text_parts) if text_parts else None

        if not content:
            raise ValueError("Missing content from Foundry response")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Foundry response was not valid JSON") from exc

        validated = ExplanationResponse.model_validate(parsed)
        return validated.model_dump()

    def generate_explanation(self, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        if not self.settings.foundry_endpoint_url or not self.settings.foundry_api_key:
            return self._fallback(payload)

        try:
            raw = self._call_foundry(payload=payload, request_id=request_id)
            return self._parse_response(raw)
        except (httpx.HTTPError, ValidationError, ValueError) as exc:
            logger.exception(
                {
                    "event": "foundry_explanation_fallback",
                    "request_id": request_id,
                    "error": str(exc),
                }
            )
            return self._fallback(payload)
