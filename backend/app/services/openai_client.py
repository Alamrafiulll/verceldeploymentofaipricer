import json
import logging
import time
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings

logger = logging.getLogger("app")


class OpenAIResponseError(ValueError):
    pass


def extract_text_from_model_response(data: dict[str, Any]) -> str | None:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]

    if isinstance(data.get("response"), str):
        return data["response"]

    if isinstance(data.get("message"), dict) and isinstance(data["message"].get("content"), str):
        return data["message"]["content"]

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

    if isinstance(data.get("choices"), list) and data["choices"]:
        message = data["choices"][0].get("message", {})
        raw_content = message.get("content")
        if isinstance(raw_content, str):
            return raw_content
        if isinstance(raw_content, list):
            text_parts = [
                block["text"]
                for block in raw_content
                if isinstance(block, dict) and isinstance(block.get("text"), str)
            ]
            if text_parts:
                return "".join(text_parts)

    if "content" in data:
        raw_content = data["content"]
        if isinstance(raw_content, str):
            return raw_content
        if isinstance(raw_content, list):
            text_parts = [
                block["text"]
                for block in raw_content
                if isinstance(block, dict) and isinstance(block.get("text"), str)
            ]
            if text_parts:
                return "".join(text_parts)

    return None


def parse_json_text(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise OpenAIResponseError("Model response was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise OpenAIResponseError("Model response JSON must be an object")
    return parsed


def sanitize_schema_for_gemini(schema: dict[str, Any]) -> dict[str, Any]:
    import copy
    schema_copy = copy.deepcopy(schema)

    def walk(obj: Any):
        if not isinstance(obj, dict):
            return
        if "type" in obj:
            t = obj["type"]
            if isinstance(t, list):
                non_null = [x for x in t if x != "null"]
                obj["type"] = non_null[0] if non_null else "string"
        if "additionalProperties" in obj:
            del obj["additionalProperties"]
        for val in obj.values():
            if isinstance(val, dict):
                walk(val)
            elif isinstance(val, list):
                for item in val:
                    walk(item)

    walk(schema_copy)
    return schema_copy


class OpenAIResponsesClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return (
            self.settings.openai_enabled
            or self.settings.ollama_enabled
            or self.settings.gemini_enabled
        )

    @property
    def model_name(self) -> str:
        if self.settings.ollama_enabled:
            return self.settings.effective_ollama_model_name
        if self.settings.gemini_enabled:
            return self.settings.effective_gemini_model_name
        return self.settings.effective_openai_model_name

    def _endpoint(self) -> str:
        return f"{self.settings.openai_base_url.rstrip('/')}/responses"

    def _ollama_endpoint(self) -> str:
        return f"{self.settings.ollama_base_url.rstrip('/')}/api/chat"

    def _build_headers(self, request_id: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
            "x-request-id": request_id,
        }

    def _ensure_ollama_available(self) -> None:
        try:
            timeout = httpx.Timeout(1.0, connect=0.5)
            with httpx.Client(timeout=timeout) as client:
                response = client.get(f"{self.settings.ollama_base_url.rstrip('/')}/api/tags")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OpenAIResponseError("Ollama is not running locally") from exc

    def _create_ollama_json(
        self,
        *,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        request_id: str,
        temperature: float | None,
        timeout: float | None,
    ) -> dict[str, Any]:
        self._ensure_ollama_available()
        schema_prompt = (
            f"{instructions}\n"
            "Return one JSON object only. Do not include markdown fences or explanatory text.\n"
            f"JSON schema name: {schema_name}\n"
            f"JSON schema: {json.dumps(schema, ensure_ascii=True)}"
        )
        body: dict[str, Any] = {
            "model": self.settings.effective_ollama_model_name,
            "messages": [
                {"role": "system", "content": schema_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=True)},
            ],
            "format": "json",
            "stream": False,
            "options": {},
        }
        if temperature is not None:
            body["options"]["temperature"] = temperature

        started = time.perf_counter()
        with httpx.Client(timeout=timeout or self.settings.ollama_timeout_seconds) as client:
            response = client.post(self._ollama_endpoint(), json=body, headers={"x-request-id": request_id})
            response.raise_for_status()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                {
                    "event": "ollama_json_call",
                    "request_id": request_id,
                    "model": self.settings.effective_ollama_model_name,
                    "schema_name": schema_name,
                    "duration_ms": duration_ms,
                    "status": response.status_code,
                }
            )
            text = extract_text_from_model_response(response.json())
            if not text:
                raise OpenAIResponseError("Missing content from Ollama response")
            return parse_json_text(text)

    @retry(wait=wait_exponential(multiplier=0.5, min=1, max=4), stop=stop_after_attempt(3), reraise=True)
    def _create_openai_json(
        self,
        *,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        request_id: str,
        temperature: float | None = 0.1,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        if not self.settings.openai_enabled:
            raise OpenAIResponseError("OPENAI_API_KEY is not configured")

        body: dict[str, Any] = {
            "model": self.model_name,
            "instructions": instructions,
            "input": json.dumps(payload, ensure_ascii=True),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                }
            },
        }
        if temperature is not None:
            body["temperature"] = temperature

        started = time.perf_counter()
        with httpx.Client(timeout=timeout or self.settings.openai_timeout_seconds) as client:
            response = client.post(self._endpoint(), json=body, headers=self._build_headers(request_id))
            response.raise_for_status()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                {
                    "event": "openai_responses_call",
                    "request_id": request_id,
                    "model": self.model_name,
                    "duration_ms": duration_ms,
                    "status": response.status_code,
                }
            )
            text = extract_text_from_model_response(response.json())
            if not text:
                raise OpenAIResponseError("Missing content from OpenAI response")
            return parse_json_text(text)

    @retry(wait=wait_exponential(multiplier=0.5, min=1, max=4), stop=stop_after_attempt(3), reraise=True)
    def _create_gemini_json(
        self,
        *,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        request_id: str,
        temperature: float | None = 0.1,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            raise OpenAIResponseError("GEMINI_API_KEY is not configured")

        model = self.settings.effective_gemini_model_name
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.settings.gemini_api_key}"

        prompt = (
            f"{instructions}\n"
            "Return a valid JSON object matching the requested schema.\n"
            f"Input features/data: {json.dumps(payload, ensure_ascii=True)}"
        )

        sanitized_schema = sanitize_schema_for_gemini(schema)

        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": sanitized_schema,
            }
        }
        if temperature is not None:
            body["generationConfig"]["temperature"] = temperature

        started = time.perf_counter()
        with httpx.Client(timeout=timeout or self.settings.gemini_timeout_seconds) as client:
            response = client.post(url, json=body, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                {
                    "event": "gemini_json_call",
                    "request_id": request_id,
                    "model": model,
                    "duration_ms": duration_ms,
                    "status": response.status_code,
                }
            )
            resp_data = response.json()
            try:
                text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as exc:
                raise OpenAIResponseError("Missing content from Gemini response") from exc
            
            if not text:
                raise OpenAIResponseError("Gemini returned empty text")
            return parse_json_text(text)

    def create_json(
        self,
        *,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        request_id: str,
        temperature: float | None = 0.1,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        if self.settings.gemini_enabled:
            return self._create_gemini_json(
                instructions=instructions,
                payload=payload,
                schema_name=schema_name,
                schema=schema,
                request_id=request_id,
                temperature=temperature,
                timeout=timeout,
            )
        if self.settings.ollama_enabled:
            return self._create_ollama_json(
                instructions=instructions,
                payload=payload,
                schema_name=schema_name,
                schema=schema,
                request_id=request_id,
                temperature=temperature,
                timeout=timeout,
            )
        return self._create_openai_json(
            instructions=instructions,
            payload=payload,
            schema_name=schema_name,
            schema=schema,
            request_id=request_id,
            temperature=temperature,
            timeout=timeout,
        )
