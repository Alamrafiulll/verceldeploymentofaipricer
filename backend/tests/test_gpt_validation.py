import pytest

from app.services.foundry_gpt_client import FoundryClient


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

