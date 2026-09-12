import json

import pytest

from backend.main import build_prompt, redact_text, validate_analysis


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
