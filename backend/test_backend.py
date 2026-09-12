import json

import pytest

from backend.main import build_prompt, get_llm_config, normalize_analysis_payload, redact_text, validate_analysis


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Herr Mustermann, Tel: 07131-56-2044, PLZ 74072", "Herr [PERSON], Tel: [PHONE], PLZ [ZIP]"),
        ("Kfz-Kennzeichen ABC123, VIN WBA1234567890", "Kfz-Kennzeichen [LICENSE_PLATE], VIN [VIN]"),
    ],
)
def test_redact_text_masks_common_pii(text, expected):
    redacted = redact_text(text)
    assert expected in redacted


def test_validate_analysis_accepts_schema_compliant_object():
    payload = {
        "detected_language": "de",
        "sender": "Stadt Heilbronn",
        "letter_type": "vehicle registration notice",
        "requires_action": True,
        "summary": "You need to update your address.",
        "deadline": {
            "date": "2026-10-12",
            "raw_text": "bis spätestens 12.10.2026",
            "is_relative_to_receipt": False,
            "confidence": "high",
        },
        "required_actions": [{"action": "Bring your documents.", "confidence": "high"}],
        "consequences_if_missed": "Further enforcement may follow.",
        "overall_confidence": "high",
    }
    assert validate_analysis(payload) is True


def test_validate_analysis_rejects_missing_required_field():
    payload = {
        "detected_language": "de",
        "sender": "Stadt Heilbronn",
        "letter_type": "vehicle registration notice",
        "requires_action": True,
        "summary": "You need to update your address.",
        "deadline": {
            "date": "2026-10-12",
            "raw_text": "bis spätestens 12.10.2026",
            "is_relative_to_receipt": False,
            "confidence": "high",
        },
        "required_actions": [{"action": "Bring your documents.", "confidence": "high"}],
        "overall_confidence": "high",
    }
    assert validate_analysis(payload) is False


def test_build_prompt_includes_target_language_and_letter_text():
    prompt = build_prompt("en", "Hello world")
    assert "Target language for the response: en" in prompt
    assert "Hello world" in prompt
    assert "schema-v2.json" in prompt


def test_redact_text_keeps_dates_unchanged():
    text = "Deadline: 12.10.2026. Please answer by 31.08.2026."
    redacted = redact_text(text)
    assert "12.10.2026" in redacted
    assert "31.08.2026" in redacted
    assert "[DOB]" not in redacted


def test_get_llm_config_uses_anthropic_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-key")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-5")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = get_llm_config()

    assert config["provider"] == "anthropic"
    assert config["api_key"] == "anthropic-test-key"
    assert config["api_base"] == "https://api.anthropic.com"
    assert config["model"] == "claude-opus-5"


def test_normalize_analysis_payload_fixes_common_llm_mismatches():
    payload = {
        "detected_language": "de",
        "sender": {"name": "Stadt Heilbronn"},
        "letter_type": {"category": "official notice"},
        "requires_action": "yes",
        "summary": "You need to do something.",
        "deadline": {
            "date": "2026-10-12",
            "raw_text": "by 12.10.2026",
            "is_relative_to_receipt": "false",
            "confidence": "high",
        },
        "required_actions": [{"action": "Bring paper", "priority": "high"}],
        "consequences_if_missed": None,
        "confidence": "high",
    }

    normalized = normalize_analysis_payload(payload)

    assert normalized["sender"] == "Stadt Heilbronn"
    assert normalized["letter_type"] == "official notice"
    assert normalized["requires_action"] is True
    assert normalized["required_actions"][0]["confidence"] == "high"
    assert "priority" not in normalized["required_actions"][0]
    assert normalized["overall_confidence"] == "high"


def test_analyze_with_llm_handles_anthropic_thinking_block(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-5")

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "content": [
                    {"type": "thinking", "thinking": "ignore this"},
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "detected_language": "en",
                                "sender": "Example Sender",
                                "letter_type": "official notice",
                                "requires_action": True,
                                "summary": "This is a valid summary.",
                                "deadline": {
                                    "date": "2026-10-12",
                                    "raw_text": "until 12.10.2026",
                                    "is_relative_to_receipt": False,
                                    "confidence": "high",
                                },
                                "required_actions": [{"action": "Review the letter.", "confidence": "high"}],
                                "consequences_if_missed": "Further action may follow.",
                                "overall_confidence": "high",
                            }
                        ),
                    },
                ]
            }

    monkeypatch.setattr("backend.main.requests.post", lambda *args, **kwargs: FakeResponse())

    result = __import__("backend.main", fromlist=["analyze_with_llm"]).analyze_with_llm("hello")

    assert result["detected_language"] == "en"
    assert result["summary"] == "This is a valid summary."
