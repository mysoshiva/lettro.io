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

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "schema" / "schema-v2.json"
PROMPT_PATH = BASE_DIR / "prompts" / "prompt-v2.md"
TEST_LETTERS_DIR = BASE_DIR / "test-letters"

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
    redacted = re.sub(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b", "[PHONE]", redacted)
    redacted = re.sub(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", "[DOB]", redacted)
    redacted = re.sub(r"\b\d{5}\b", "[ZIP]", redacted)
    redacted = re.sub(r"\bVIN\s+[A-HJ-NPR-Z0-9]{10,17}\b", "VIN [VIN]", redacted)
    redacted = re.sub(r"(?<![A-Z0-9])(?:[A-ZÄÖÜ]{1,3}-?\d{1,4})(?![A-Z0-9])", "[LICENSE_PLATE]", redacted)
    redacted = re.sub(r"\b(?:Herr|Frau|Herrn|Frauen|Sehr geehrter Herr|Sehr geehrte Frau)\s+[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*\b", "Herr [PERSON]", redacted)
    redacted = re.sub(r"\b(?:Login|Benutzername|User|PIN)\s*[:=]?\s*[A-Z0-9]+\b", "[LOGIN]", redacted)
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


def validate_analysis(payload: dict[str, Any]) -> bool:
    schema = load_schema()
    try:
        validate(instance=payload, schema=schema)
        return True
    except ValidationError:
        return False


async def extract_text_from_image(file: UploadFile) -> str:
    contents = await file.read()
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


def extract_json_from_llm_response(raw_response: str) -> dict[str, Any]:
    cleaned = raw_response.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    return json.loads(cleaned)


def analyze_with_llm(prompt: str) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Configure an OpenAI-compatible API key to enable LLM analysis."
        )

    api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
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
        },
        timeout=60,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"LLM request failed: {response.status_code} {response.text}")

    body = response.json()
    raw_content = body["choices"][0]["message"]["content"]
    return extract_json_from_llm_response(raw_content)


@app.post("/ocr")
async def ocr(image: UploadFile = File(...)):
    try:
        extracted_text = await extract_text_from_image(image)
        return {"text": extracted_text}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/sample_letters")
async def sample_letters():
    return {"letters": list_sample_letters()}


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

        if not validate_analysis(analysis):
            raise HTTPException(status_code=422, detail="LLM output does not satisfy the schema-v2 contract.")

        return {"analysis": analysis, "source": sample_name}
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

        if not validate_analysis(analysis):
            raise HTTPException(status_code=422, detail="LLM output does not satisfy the schema-v2 contract.")

        return {"analysis": analysis}
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

    uvicorn.run(app, host="0.0.0.0", port=8000)