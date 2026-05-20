import pytest

from app.core.config import Settings
from app.services.foundry_gpt_client import FoundryClient
from app.services.openai_client import OpenAIResponsesClient, extract_text_from_model_response, parse_json_text


def test_gpt_response_validation_accepts_valid_payload():
    client = FoundryClient()
    data = {
        "choices": [
            {
                "message": {
                    "content": '{"short_reason":"Margin and win tradeoff","top_drivers":["driver1","driver2","driver3"],"negotiation_tips":["tip1","tip2","tip3"],"approval_justification_suggestion":"Keep strategic account","executive_summary":"Policy aligned"}'
                }
            }
        ]
    }
    parsed = client._parse_response(data)
    assert parsed["short_reason"]
    assert len(parsed["top_drivers"]) >= 3


def test_gpt_response_validation_rejects_invalid_json():
    client = FoundryClient()
    with pytest.raises(ValueError):
        client._parse_response({"choices": [{"message": {"content": "not-json"}}]})


def test_gpt_response_validation_accepts_responses_api_shape():
    client = FoundryClient()
    data = {
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": '{"short_reason":"Works with responses API","top_drivers":["driver1","driver2","driver3"],"negotiation_tips":["tip1","tip2","tip3"]}',
                    }
                ],
            }
        ]
    }
    parsed = client._parse_response(data)
    assert parsed["short_reason"] == "Works with responses API"


def test_gpt_client_uses_api_key_for_azure_endpoint():
    client = FoundryClient()
    headers = client._build_headers(
        endpoint_url="https://example.openai.azure.com/openai/responses?api-version=2025-04-01-preview",
        request_id="req-1",
    )
    assert "api-key" in headers
    assert "Authorization" not in headers


def test_openai_client_uses_bearer_header():
    settings = Settings(openai_api_key="test-key", openai_model="gpt-5.4-mini")
    client = OpenAIResponsesClient(settings)
    headers = client._build_headers(request_id="req-1")
    assert headers["Authorization"] == "Bearer test-key"
    assert headers["x-request-id"] == "req-1"


def test_openai_json_parser_accepts_fenced_json():
    parsed = parse_json_text('```json\n{"ok": true}\n```')
    assert parsed == {"ok": True}


def test_ollama_provider_is_enabled_without_api_key():
    settings = Settings(ai_provider="ollama", openai_api_key=None, ollama_model="llama3.1:8b")
    client = OpenAIResponsesClient(settings)
    assert client.enabled
    assert client.model_name == "llama3.1:8b"
    assert settings.active_ai_provider == "ollama_local"


def test_model_response_parser_accepts_ollama_chat_shape():
    content = extract_text_from_model_response({"message": {"content": '{"ok": true}'}})
    assert content == '{"ok": true}'


def test_gemini_provider_is_enabled_with_api_key():
    settings = Settings(ai_provider="gemini", gemini_api_key="test-key", gemini_model="gemini-1.5-flash")
    client = OpenAIResponsesClient(settings)
    assert client.enabled
    assert client.model_name == "gemini-1.5-flash"
    assert settings.active_ai_provider == "gemini"


def test_gemini_schema_sanitizer():
    from app.services.openai_client import sanitize_schema_for_gemini
    raw_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "short_reason": {"type": "string"},
            "executive_summary": {"type": ["string", "null"]},
        },
    }
    sanitized = sanitize_schema_for_gemini(raw_schema)
    assert "additionalProperties" not in sanitized
    assert sanitized["properties"]["executive_summary"]["type"] == "string"


