import logging
import time
import json
from typing import Any
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.feature_builder import build_scoring_rows

logger = logging.getLogger("app")


class FoundryScoringClient:
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

    @retry(wait=wait_exponential(multiplier=0.5, min=1, max=4), stop=stop_after_attempt(3), reraise=True)
    def _call_foundry(self, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        endpoint_url = self.settings.foundry_scoring_endpoint_url or ""
        headers = self._build_headers(endpoint_url=endpoint_url, request_id=request_id)
        started = time.perf_counter()
        
        # Construct Chat Completion Payload if it's Azure OpenAI
        if self._is_azure_openai_endpoint(endpoint_url):
            # Transform the raw feature payload into a Prompt for the LLM
            features = payload.get("features", {})
            candidate_prices = payload.get("candidate_prices", [])
            
            system_prompt = (
                "You are an AI Pricing Assistant. Your task is to predict the 'win probability' "
                "for a set of candidate prices based on deal features. "
                "Return ONLY a valid JSON object with the following structure: "
                "{'probabilities': [float, float, ...], 'confidence': float, 'model_version': 'gpt-5.1-chat'}. "
                "The probabilities list must correspond 1-to-1 with the candidate prices."
            )
            
            user_prompt = (
                f"Deal Features: {json.dumps(features)}\n"
                f"Candidate Prices: {candidate_prices}\n"
                "Analyze these inputs and provide win probabilities for each price."
            )
            
            chat_payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            
            # Use chat_payload for the request
            request_payload = chat_payload
        else:
            # Fallback for other endpoints (legacy/custom)
            request_payload = payload

        with httpx.Client(timeout=30.0) as client:
            response = client.post(endpoint_url, json=request_payload, headers=headers)
            response.raise_for_status()
            
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                {
                    "event": "foundry_scoring_call",
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "status": response.status_code,
                }
            )
            
            data = response.json()
            
            # If it's Azure OpenAI, extract the JSON from the content
            if self._is_azure_openai_endpoint(endpoint_url):
                try:
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                except (KeyError, json.JSONDecodeError) as e:
                    logger.error(f"Failed to parse LLM response: {data}")
                    raise ValueError("Invalid LLM response format") from e
            
            return data

    @staticmethod
    def _deterministic_fallback(
        features: dict,
        candidate_prices: list[float],
        rows: list[dict],
    ) -> tuple[list[float], float, str, list[dict]]:
        """Generate realistic win probabilities using a deterministic heuristic
        when Azure OpenAI scoring is unavailable."""
        list_price = float(features.get("list_price", candidate_prices[-1] if candidate_prices else 1))
        probabilities = []
        for price in candidate_prices:
            discount_pct = ((list_price - price) / list_price) * 100 if list_price > 0 else 0
            # Higher discounts → higher win probability (capped at 0.95)
            prob = min(0.95, 0.40 + discount_pct * 0.025)
            probabilities.append(round(max(0.05, prob), 4))
        confidence = 0.55
        model_version = "deterministic-fallback-v1"
        logger.info(
            {
                "event": "foundry_scoring_deterministic_fallback",
                "num_candidates": len(candidate_prices),
            }
        )
        return probabilities, confidence, model_version, rows

    def score_win_probability(
        self,
        features: dict,
        candidate_prices: list[float],
        request_id: str,
    ) -> tuple[list[float], float, str, list[dict]]:
        list_price = float(features["list_price"])
        rows = build_scoring_rows(features, list_price, candidate_prices)

        if self.settings.foundry_scoring_endpoint_url and self.settings.foundry_api_key:
            payload = {
                "features": features,
                "candidate_prices": candidate_prices,
                "rows": rows,
            }
            try:
                data = self._call_foundry(payload, request_id=request_id)
                probs = [float(x) for x in data.get("probabilities", [])]
                confidence = float(data.get("confidence", 0.65))
                # Ensure we have a prob for each price
                if len(probs) != len(candidate_prices):
                    # Fallback if LLM messes up counts
                    logger.warning(f"LLM returned {len(probs)} probs for {len(candidate_prices)} prices. Using default.")
                    probs = [0.5] * len(candidate_prices)
                
                model_version = data.get("model_version", self.settings.win_model_version)
                if not model_version or model_version == "xgb-v1":
                     model_version = "gpt-5.1-chat"

                return probs, confidence, model_version, rows
            except Exception as exc:
                logger.exception(
                    {
                        "event": "foundry_scoring_error",
                        "request_id": request_id,
                        "error": str(exc),
                    }
                )
                return self._deterministic_fallback(features, candidate_prices, rows)

        return self._deterministic_fallback(features, candidate_prices, rows)
