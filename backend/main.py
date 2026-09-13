from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import io
import json
import os
import re
import sqlite3
from datetime import datetime
from typing import Any, Optional

import requests
import pytesseract
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from jsonschema import ValidationError, validate
from PIL import Image
from pydantic import BaseModel

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - dependency is installed in app runtime
    PdfReader = None

try:
    import pymupdf as fitz  # rasterizes scanned/image-only PDF pages for OCR
except ImportError:  # pragma: no cover - dependency is installed in app runtime
    fitz = None

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "schema" / "schema-v2.json"
PROMPT_PATH = BASE_DIR / "prompts" / "prompt-v2.md"
TEST_LETTERS_DIR = BASE_DIR / "test-letters"

MAX_FILES_PER_BATCH = 30
MAX_TOTAL_UPLOAD_BYTES = 20 * 1024 * 1024
SUPPORTED_UPLOAD_TYPES = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "webp",
    "tif",
    "tiff",
}
SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/tiff",
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db() -> None:
    conn = sqlite3.connect("lettro.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT,
            analysis TEXT,
            target_language TEXT,
            timestamp DATETIME
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


class AnalysisRequest(BaseModel):
    text: str
    target_language: str = "en"
    analysis: Optional[str] = None


def load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
        return json.load(schema_file)


def redact_text(text: str) -> str:
    redacted = text or ""
    redacted = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL]", redacted)

    date_map: dict[str, str] = {}

    def replace_date(match: re.Match[str]) -> str:
        value = match.group(0)
        placeholder = f"__DATE_{len(date_map)}__"
        date_map[placeholder] = value
        return placeholder

    redacted = re.sub(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", replace_date, redacted)
    redacted = re.sub(r"(?<![A-Z0-9])(?:\+?\d[\d\s().-]{7,}\d)(?![A-Z0-9])", "[PHONE]", redacted)
    redacted = re.sub(r"\b\d{5}\b", "[ZIP]", redacted)
    redacted = re.sub(r"\bVIN\s+[A-HJ-NPR-Z0-9]{10,17}\b", "VIN [VIN]", redacted)
    redacted = re.sub(r"(?<![A-Z0-9])(?:[A-ZÄÖÜ]{1,3}-?\d{1,4})(?![A-Z0-9])", "[LICENSE_PLATE]", redacted)
    redacted = re.sub(r"\b(?:Herr|Frau|Herrn|Frauen|Sehr geehrter Herr|Sehr geehrte Frau)\s+[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*\b", "Herr [PERSON]", redacted)
    redacted = re.sub(r"\b(?:Login|Benutzername|User|PIN)\s*[:=]?\s*[A-Z0-9]+\b", "[LOGIN]", redacted)

    for placeholder, original in date_map.items():
        redacted = redacted.replace(placeholder, original)

    return redacted


def build_prompt(target_language: str, ocr_text: str) -> str:
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
    user_template = f"""

Target language for the response: {target_language}

Letter text:
{ocr_text}
"""
    return f"{prompt_text}\n{user_template}"


def extract_sample_text(markdown_text: str) -> str:
    match = re.search(
        r"## (?:Input|Letter text).*?\n(.*?)(?:\n## Expected output|\Z)",
        markdown_text,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        raise ValueError("Could not find sample input section in test letter file.")
    return match.group(1).strip()


def list_sample_letters() -> list[str]:
    return sorted(
        p.name for p in TEST_LETTERS_DIR.glob("*.md") if p.name.lower() != "readme.md"
    )


def normalize_analysis_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)

    for key in ["target_language", "sender_address", "sender_email", "sender_phone"]:
        normalized.pop(key, None)

    if "deadline" not in normalized and "deadlines" in normalized:
        normalized["deadline"] = normalized.pop("deadlines")

    if "detected_language" not in normalized:
        detected = normalized.get("language") or normalized.get("target_language") or "und"
        normalized["detected_language"] = detected if isinstance(detected, str) else "und"

    sender = normalized.get("sender")
    if isinstance(sender, dict):
        candidate = sender.get("name") or sender.get("organization") or sender.get("value")
        normalized["sender"] = candidate
    elif sender is None:
        normalized["sender"] = None

    letter_type = normalized.get("letter_type")
    if isinstance(letter_type, dict):
        candidate = letter_type.get("name") or letter_type.get("category") or letter_type.get("value")
        normalized["letter_type"] = candidate

    if "requires_action" not in normalized:
        required_actions = normalized.get("required_actions") or []
        consequences = normalized.get("consequences_if_missed")
        normalized["requires_action"] = bool(required_actions) or bool(consequences)
    elif not isinstance(normalized["requires_action"], bool):
        value = normalized["requires_action"]
        normalized["requires_action"] = str(value).strip().lower() in {"true", "yes", "y", "1"}

    deadline = normalized.get("deadline")
    if not isinstance(deadline, dict):
        deadline = {
            "date": None,
            "raw_text": None,
            "is_relative_to_receipt": False,
            "confidence": "low",
        }
        normalized["deadline"] = deadline

    deadline_value = deadline.get("is_relative_to_receipt")
    if deadline_value is None:
        deadline["is_relative_to_receipt"] = False
    elif not isinstance(deadline_value, bool):
        deadline["is_relative_to_receipt"] = str(deadline_value).strip().lower() in {"true", "yes", "y", "1"}

    if deadline.get("date") is not None and not isinstance(deadline.get("date"), str):
        deadline["date"] = str(deadline["date"])
    if deadline.get("raw_text") is not None and not isinstance(deadline.get("raw_text"), str):
        deadline["raw_text"] = str(deadline["raw_text"])
    if deadline.get("confidence") not in {"high", "medium", "low"}:
        deadline["confidence"] = "low"

    if "summary" not in normalized or not isinstance(normalized.get("summary"), str):
        sender_text = normalized.get("sender") or "the sender"
        letter_type_text = normalized.get("letter_type") or "letter"
        normalized["summary"] = f"This is a {letter_type_text.lower()} from {sender_text} in the reader's language."

    required_actions = normalized.get("required_actions")
    if isinstance(required_actions, list):
        normalized["required_actions"] = []
        for item in required_actions:
            if not isinstance(item, dict):
                continue
            action = item.get("action") or item.get("summary") or item.get("text")
            confidence = item.get("confidence") or item.get("priority") or "medium"
            if not action:
                continue
            normalized["required_actions"].append({
                "action": action,
                "confidence": confidence if confidence in {"high", "medium", "low"} else "medium",
            })
    else:
        normalized["required_actions"] = []

    if "consequences_if_missed" not in normalized or normalized.get("consequences_if_missed") is None:
        normalized["consequences_if_missed"] = None

    if "overall_confidence" not in normalized and "confidence" in normalized:
        normalized["overall_confidence"] = normalized["confidence"]
    if normalized.get("overall_confidence") not in {"high", "medium", "low"}:
        normalized["overall_confidence"] = "medium"

    return normalized


def validate_analysis(payload: dict[str, Any]) -> bool:
    schema = load_schema()
    try:
        validate(instance=payload, schema=schema)
        return True
    except ValidationError:
        return False


def detect_document_type(filename: str, content_type: Optional[str] = None) -> str:
    lowered_name = (filename or "").lower()
    mime_type = (content_type or "").lower()

    if lowered_name.endswith(".pdf") or "pdf" in mime_type:
        return "pdf"
    return "image"


def get_supported_upload_summary() -> str:
    return ".pdf, .png, .jpg, .jpeg, .webp, .tif, .tiff"


def is_supported_upload(filename: str, content_type: Optional[str] = None) -> bool:
    lowered_name = (filename or "").lower()
    mime_type = (content_type or "").lower()
    extension = lowered_name.rsplit(".", 1)[-1] if "." in lowered_name else ""
    is_supported_ext = extension in SUPPORTED_UPLOAD_TYPES
    is_supported_mime = mime_type in SUPPORTED_MIME_TYPES or mime_type.startswith("image/") and mime_type.split("/")[-1] in {"png", "jpeg", "jpg", "webp", "tiff", "tif"}
    return is_supported_ext or is_supported_mime


def validate_upload_batch(files: list[Any]) -> list[Any]:
    if files is None:
        raise ValueError("No files selected.")

    if len(files) > MAX_FILES_PER_BATCH:
        raise ValueError(f"You can upload up to {MAX_FILES_PER_BATCH} files at once.")

    total_size = 0
    for file in files:
        size = getattr(file, "size", None)
        if size is None:
            size = len(getattr(file, "read", lambda: b"")()) if hasattr(file, "read") else 0
        total_size += int(size or 0)

    if total_size >= MAX_TOTAL_UPLOAD_BYTES:
        raise ValueError(f"Total upload size exceeds {MAX_TOTAL_UPLOAD_BYTES / (1024 * 1024):.0f} MB limit.")

    unsupported = []
    for file in files:
        filename = getattr(file, "filename", "") or ""
        mime_type = getattr(file, "content_type", "") or ""
        if not is_supported_upload(filename, mime_type):
            unsupported.append(filename or "unknown file")

    if unsupported:
        raise ValueError(
            "Unsupported file format(s): " + ", ".join(sorted(set(unsupported))) + ". Supported types: " + get_supported_upload_summary() + "."
        )

    return files


async def extract_text_from_image(contents: bytes) -> str:
    if not contents:
        raise ValueError("Uploaded file is empty.")

    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as exc:  # pragma: no cover - image decode failure path
        raise ValueError(f"Could not open uploaded image: {exc}") from exc

    if os.system("which tesseract >/dev/null 2>&1") != 0:
        raise RuntimeError("Tesseract is not installed on this machine.")

    text = pytesseract.image_to_string(image, lang="eng+deu")
    return text.strip()


async def extract_text_from_document(file: UploadFile) -> str:
    contents = await file.read()
    if not contents:
        raise ValueError("Uploaded file is empty.")

    content_type = getattr(file, "content_type", None)
    document_type = detect_document_type(file.filename or "", content_type)
    if document_type == "pdf":
        if PdfReader is None:
            raise RuntimeError("PDF support requires the pypdf package to be installed.")

        reader = PdfReader(io.BytesIO(contents))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text.strip())

        text = "\n".join(pages).strip()
        if text:
            return text

        # No embedded text layer — this is very common with phone-scanned PDFs.
        # Rasterize each page and OCR it using the same path as images.
        if fitz is None:
            raise RuntimeError("Scanned-PDF support requires the pymupdf package to be installed.")

        ocr_pages = []
        pdf_doc = fitz.open(stream=contents, filetype="pdf")
        try:
            for page in pdf_doc:
                pixmap = page.get_pixmap(dpi=300)
                page_image_bytes = pixmap.tobytes("png")
                page_text = await extract_text_from_image(page_image_bytes)
                if page_text.strip():
                    ocr_pages.append(page_text.strip())
        finally:
            pdf_doc.close()

        ocr_text = "\n".join(ocr_pages).strip()
        if not ocr_text:
            raise ValueError("Could not extract any readable text from the uploaded PDF.")
        return ocr_text

    return await extract_text_from_image(contents)


def extract_json_from_llm_response(raw_response: str) -> dict[str, Any]:
    cleaned = raw_response.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    if not cleaned:
        raise ValueError("LLM returned an empty response.")

    def repair_incomplete_json(text: str) -> str:
        repaired = text.strip()
        repaired = repaired.replace('"deadlines"', '"deadline"')
        if not repaired.startswith("{"):
            start = repaired.find("{")
            if start >= 0:
                repaired = repaired[start:]
            else:
                return repaired

        in_string = False
        escaped = False
        stack: list[str] = []  # tracks open braces/brackets in actual nesting order

        for ch in repaired:
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == '{':
                stack.append('}')
            elif ch == '[':
                stack.append(']')
            elif ch in '}]' and stack:
                stack.pop()

        if in_string:
            repaired += '"'
        # Close in reverse (LIFO) order — the innermost open structure
        # must be closed first, which a pair of independent brace/bracket
        # counters can't guarantee once an object is truncated inside an
        # array (e.g. inside `required_actions: [{...`).
        while stack:
            repaired += stack.pop()

        repaired = re.sub(r',\s*([}\]])', r'\1', repaired)
        return repaired

    def find_first_balanced_object(text: str) -> Optional[str]:
        """Return the exact substring of the first complete top-level
        {...} object, discarding anything before or after it. This is
        what handles small local models that append trailing chatter
        after an otherwise perfectly valid JSON object — something the
        brace-padding repair below can't fix, since there's nothing
        missing to pad, there's extra content to discard instead."""
        start = text.find("{")
        if start < 0:
            return None

        in_string = False
        escaped = False
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        return None  # never closed — genuinely truncated, not just trailing garbage

    candidates = [cleaned]
    exact_object = find_first_balanced_object(cleaned)
    if exact_object:
        candidates.insert(0, exact_object)
    if "{" in cleaned:
        start = cleaned.find("{")
        payload = cleaned[start:]
        candidates.append(payload)
        candidates.append(repair_incomplete_json(payload))

    for candidate in list(dict.fromkeys(candidates)):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

        repaired = repair_incomplete_json(candidate)
        try:
            parsed = json.loads(repaired)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    raise ValueError(f"LLM response was not valid JSON: {cleaned[:200]}")


def extract_text_from_anthropic_response(body: dict[str, Any]) -> str:
    content = body.get("content")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_blocks = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and block.get("text"):
                text_blocks.append(block["text"])
        if text_blocks:
            return "\n".join(text_blocks)

    raise ValueError("Anthropic response did not contain any text output.")


def get_llm_config() -> dict[str, str]:
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if provider == "anthropic" or (not provider and anthropic_key):
        api_key = anthropic_key
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set. Configure your Anthropic API key to enable LLM analysis.")
        return {
            "provider": "anthropic",
            "api_key": api_key,
            "api_base": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            "model": os.getenv("ANTHROPIC_MODEL", "claude-opus-5"),
        }

    if provider in {"", "openai", "ollama"}:
        if provider == "ollama":
            api_key = openai_key or "ollama"
        elif provider == "" and not openai_key:
            # Nothing explicitly configured — default to a local Ollama
            # instance rather than failing outright. This makes "just
            # install Ollama and pull a model" work with zero .env setup.
            provider = "ollama"
            api_key = "ollama"
        else:
            api_key = openai_key
            if not api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not set. Configure an OpenAI-compatible API key to enable LLM analysis."
                )
        return {
            "provider": "openai",
            "api_key": api_key,
            "api_base": os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1" if provider == "ollama" else "https://api.openai.com/v1"),
            "model": os.getenv("OPENAI_MODEL", "llama3.2:3b" if provider == "ollama" else "gpt-4o-mini"),
        }

    raise RuntimeError(f"Unsupported LLM provider: {provider}. Use 'openai' or 'anthropic'.")


def get_llm_status() -> dict[str, Any]:
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "")
    model = os.getenv("OPENAI_MODEL", "llama3.2:3b")

    if provider == "anthropic" or (not provider and anthropic_key):
        return {
            "provider": "anthropic",
            "kind": "cloud",
            "available": True,
            "model": os.getenv("ANTHROPIC_MODEL", "claude-opus-5"),
            "message": "Anthropic configured",
        }

    defaulting_to_ollama = provider == "" and not anthropic_key and not openai_key and not base_url
    if provider == "ollama" or defaulting_to_ollama or (base_url and "localhost:11434" in base_url):
        ollama_base = base_url.rsplit("/v1", 1)[0] if base_url else "http://localhost:11434"
        try:
            response = requests.get(f"{ollama_base}/api/tags", timeout=5)
            if response.status_code == 200:
                body = response.json()
                models = [item.get("name") for item in body.get("models", []) if isinstance(item, dict)]
                return {
                    "provider": "ollama",
                    "kind": "local",
                    "available": True,
                    "model": model,
                    "models": models,
                    "message": "Local model ready",
                }
            return {
                "provider": "ollama",
                "kind": "local",
                "available": False,
                "model": model,
                "message": "Ollama is reachable but no model is available yet",
            }
        except Exception as exc:
            return {
                "provider": "ollama",
                "kind": "local",
                "available": False,
                "model": model,
                "message": f"Ollama not reachable: {exc}",
            }

    if provider in {"", "openai"} and not openai_key and not base_url:
        return {
            "provider": "openai",
            "kind": "cloud",
            "available": False,
            "model": "not configured",
            "message": "No model configured",
        }

    return {
        "provider": "openai",
        "kind": "cloud",
        "available": True,
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "message": "Cloud model configured",
    }


def analyze_with_llm(prompt: str) -> dict[str, Any]:
    config = get_llm_config()
    api_key = config["api_key"]
    api_base = config["api_base"]
    model = config["model"]
    provider = config["provider"]

    if provider == "anthropic":
        response = requests.post(
            f"{api_base.rstrip('/')}/v1/messages",
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=180,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"LLM request failed: {response.status_code} {response.text}")
        body = response.json()
        raw_content = extract_text_from_anthropic_response(body)
        return extract_json_from_llm_response(raw_content)

    response = requests.post(
        f"{api_base.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 4096,
        },
        timeout=180,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"LLM request failed: {response.status_code} {response.text}")

    body = response.json()
    raw_content = body["choices"][0]["message"]["content"]
    return extract_json_from_llm_response(raw_content)


@app.post("/ocr")
async def ocr(files: list[UploadFile] = File(...)):
    try:
        validated = validate_upload_batch(files)
        documents = []
        combined_text = []

        for file in validated:
            extracted_text = await extract_text_from_document(file)
            file_type = detect_document_type(file.filename or "", getattr(file, "content_type", None))
            documents.append(
                {
                    "filename": file.filename,
                    "text": extracted_text,
                    "document_type": file_type,
                }
            )
            combined_text.append(f"--- {file.filename or 'attachment'} ---\n{extracted_text}")

        return {
            "documents": documents,
            "text": "\n\n".join(combined_text),
            "total_files": len(documents),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/sample_letters")
async def sample_letters():
    return {"letters": list_sample_letters()}


@app.get("/llm_status")
async def llm_status():
    return get_llm_status()


@app.post("/run_sample")
async def run_sample(payload: dict[str, str]):
    try:
        sample_name = payload.get("filename") or payload.get("name")
        if not sample_name:
            raise HTTPException(status_code=400, detail="Missing sample name.")

        target_language = payload.get("target_language", "en")
        sample_path = TEST_LETTERS_DIR / sample_name
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail=f"Sample not found: {sample_name}")

        sample_text = extract_sample_text(sample_path.read_text(encoding="utf-8"))
        sanitized = redact_text(sample_text)
        prompt = build_prompt(target_language, sanitized)
        analysis = analyze_with_llm(prompt)
        print("RAW LLM OUTPUT (/run_sample):", json.dumps(analysis, indent=2, ensure_ascii=False))  # temporary debug line

        if not isinstance(analysis, dict):
            raise HTTPException(status_code=422, detail="LLM returned a non-object response.")

        normalized = normalize_analysis_payload(analysis)
        if not validate_analysis(normalized):
            raise HTTPException(status_code=422, detail="LLM output does not satisfy the schema-v2 contract.")

        return {"analysis": normalized, "source": sample_name}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    try:
        sanitized_text = redact_text(request.text)
        prompt = build_prompt(request.target_language, sanitized_text)
        analysis = analyze_with_llm(prompt)
        print("RAW LLM OUTPUT (/analyze):", json.dumps(analysis, indent=2, ensure_ascii=False))  # temporary debug line

        if not isinstance(analysis, dict):
            raise HTTPException(status_code=422, detail="LLM returned a non-object response.")

        normalized = normalize_analysis_payload(analysis)
        if not validate_analysis(normalized):
            raise HTTPException(status_code=422, detail="LLM output does not satisfy the schema-v2 contract.")

        return {"analysis": normalized}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/save_scan")
async def save_scan(request: AnalysisRequest):
    try:
        conn = sqlite3.connect("lettro.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO scans (original_text, analysis, target_language, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (redact_text(request.text), request.analysis, request.target_language, datetime.now()),
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/history")
async def get_history():
    try:
        conn = sqlite3.connect("lettro.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append(
                {
                    "id": row[0],
                    "original_text": row[1],
                    "analysis": row[2],
                    "target_language": row[3],
                    "timestamp": row[4],
                }
            )
        return {"history": history}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

