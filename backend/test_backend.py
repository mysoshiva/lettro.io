import asyncio
import io
import json
from types import SimpleNamespace

import pytest

from backend.main import (
    build_prompt,
    detect_document_type,
    extract_text_from_document,
    get_llm_config,
    normalize_analysis_payload,
    redact_text,
    validate_analysis,
    validate_upload_batch,
)


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


def test_get_llm_config_uses_ollama_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("OPENAI_MODEL", "llama3.1")

    config = get_llm_config()

    assert config["provider"] == "openai"
    assert config["api_key"] == "ollama"
    assert config["api_base"] == "http://localhost:11434/v1"
    assert config["model"] == "llama3.1"


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


def test_normalize_analysis_payload_handles_real_local_model_output_shape():
    payload = {
        "sender": "[NAME]",
        "letter_type": "notification",
        "deadline": {
            "date": "2027-10-12",
            "is_relative_to_receipt": None,
            "confidence": "medium",
            "raw_text": "bis spätestens 12.10.2026",
        },
        "required_actions": [{"action": "update registration documents", "confidence": "high"}],
        "consequences_if_missed": "If you do not update your address within the specified deadline, we will take disciplinary measures, including filing a fine notice with the relevant authorities.",
        "confidence": "medium",
        "sender_address": "[ADDRESS]",
        "target_language": "en",
    }

    normalized = normalize_analysis_payload(payload)

    assert normalized["detected_language"] == "und"
    assert normalized["deadline"]["is_relative_to_receipt"] is False
    assert normalized["overall_confidence"] == "medium"
    assert "target_language" not in normalized
    assert "sender_address" not in normalized


def test_extract_json_from_llm_response_recovers_plural_deadline_key_and_truncated_string():
    response = '{"sender":"Bürgeramt Stadt Heilbronn","letter_type":"Notice","deadlines":{"date":"2026-10-12","is_relative_to_receipt":false,"raw_text":"b'
    parsed = __import__("backend.main", fromlist=["extract_json_from_llm_response"]).extract_json_from_llm_response(response)

    assert parsed["sender"] == "Bürgeramt Stadt Heilbronn"
    assert parsed["deadline"]["date"] == "2026-10-12"
    assert parsed["deadline"]["raw_text"] == "b"


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


@pytest.mark.parametrize(
    "filename, content_type, expected",
    [
        ("scan.png", "image/png", "image"),
        ("letter.jpg", "image/jpeg", "image"),
        ("letter.pdf", "application/pdf", "pdf"),
        ("LETTER.PDF", "application/octet-stream", "pdf"),
    ],
)
def test_detect_document_type_handles_supported_attachments(filename, content_type, expected):
    assert detect_document_type(filename, content_type) == expected


def test_extract_text_from_document_handles_pdf_bytes(monkeypatch):
    class FakePage:
        def extract_text(self):
            return "This is a PDF letter."

    class FakeReader:
        def __init__(self, stream):
            self.stream = stream

        @property
        def pages(self):
            return [FakePage()]

    class FakeUploadFile:
        filename = "letter.pdf"

        async def read(self):
            return b"%PDF-1.4\n%fake"

    monkeypatch.setattr("backend.main.PdfReader", FakeReader)

    text = asyncio.run(extract_text_from_document(FakeUploadFile()))

    assert text == "This is a PDF letter."


def test_validate_upload_batch_enforces_file_count_and_size_limits():
    files = [SimpleNamespace(filename=f"doc-{i}.pdf", content_type="application/pdf", size=2 * 1024 * 1024) for i in range(31)]

    with pytest.raises(ValueError, match="30"):
        validate_upload_batch(files)

    files = [SimpleNamespace(filename="letter.pdf", content_type="application/pdf", size=20 * 1024 * 1024)]
    with pytest.raises(ValueError, match="20 MB"):
        validate_upload_batch(files)


def test_validate_upload_batch_rejects_unsupported_mime_types():
    files = [SimpleNamespace(filename="notes.exe", content_type="application/x-msdownload", size=1024)]

    with pytest.raises(ValueError, match="supported"):
        validate_upload_batch(files)


def test_extract_text_from_document_falls_back_to_ocr_for_rasterized_pdf(monkeypatch):
    class EmptyPage:
        def extract_text(self):
            return ""

    class FakeReader:
        def __init__(self, stream):
            self.stream = stream

        @property
        def pages(self):
            return [EmptyPage()]

    class FakePixmap:
        def tobytes(self, format):
            return b"png-bytes"

    class FakePageWithPixmap:
        def get_pixmap(self, dpi):
            assert dpi == 300
            return FakePixmap()

    class FakePdfDoc:
        def __init__(self, stream, filetype):
            self.stream = stream
            self.filetype = filetype

        def __iter__(self):
            return iter([FakePageWithPixmap()])

        def close(self):
            pass

    class FakeUploadFile:
        filename = "scanned.pdf"
        content_type = "application/pdf"

        async def read(self):
            return b"%PDF-1.4\n%fake"

    async def fake_ocr(contents):
        return "OCR text from rasterized PDF"

    monkeypatch.setattr("backend.main.PdfReader", FakeReader)
    monkeypatch.setattr("backend.main.fitz", SimpleNamespace(open=lambda stream, filetype: FakePdfDoc(stream, filetype)))
    monkeypatch.setattr("backend.main.extract_text_from_image", fake_ocr)

    text = asyncio.run(extract_text_from_document(FakeUploadFile()))

    assert text == "OCR text from rasterized PDF"
