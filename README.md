![Description of image](lettro-logo.svg)

# Lettro

Lettro explains confusing official letters — from government agencies, insurers, landlords, or any other formal sender — in plain language, in whatever language the reader actually understands.

## The problem

People who don't fluently read the language a letter arrives in often can't tell what it's asking of them, what the deadline is, or what happens if they miss it. Many turn to online translation tools, which means handing documents with personal information — case numbers, addresses, financial details — to a third party.

## What Lettro does

- Reads a photo of a letter, in any source language
- Extracts the sender, letter type, a plain-language summary, the deadline, and the required next steps
- Returns the explanation in the reader's preferred language
- Aims to keep sensitive personal details from ever leaving the device unnecessarily

## Status

Early MVP, in progress. Currently on **Step 1 — defining the prompt and output schema** against a small set of real letter types.

## Planned architecture (v1)

- Mobile-friendly web app (PWA) — camera capture, no app-store dependency to start
- Client-side OCR — image to text, on-device
- Local redaction pass — strip identifying details before anything reaches the cloud
- Small backend API wrapping an LLM call for translation and explanation
- Structured JSON output with a confidence score per field (deadline, required actions, etc.)
- Future: a fully on-device model path for users who want zero network calls

## Repo structure

```
/prompts        — versioned prompt text, one file per iteration
/test-letters   — anonymized or synthetic sample letters only (never real originals)
/schema         — the JSON output schema
/docs           — design decisions as they're made
```

## Local setup and testing

### 1) Configure environment variables

Create a local `.env` file from the template:

```bash
cd /workspaces/lettro.io
cp .env.example .env
```

Then choose your provider and set the matching API key:

```env
LLM_PROVIDER=anthropic

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=claude-opus-5
```

If you already have an Anthropic key, set `LLM_PROVIDER=anthropic` and use your Anthropic key. If you prefer OpenAI-compatible providers, keep `LLM_PROVIDER=openai` and populate `OPENAI_API_KEY` instead.

#### How to test with Anthropic

1. Set `LLM_PROVIDER=anthropic` in [.env](.env)
2. Put your Anthropic key in `ANTHROPIC_API_KEY`
3. Keep `ANTHROPIC_BASE_URL=https://api.anthropic.com`
4. Use a valid model ID such as `claude-opus-5`
5. Start the backend and call the sample endpoint:

```bash
cd /workspaces/lettro.io
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
curl -X POST http://localhost:8000/run_sample \
  -H 'Content-Type: application/json' \
  -d '{"filename":"01-stadt-heilbronn-kfz-adresse.md","target_language":"en"}'
```

> The `.env` file is local-only and should never be committed.

### 2) Install dependencies

```bash
cd /workspaces/lettro.io
python -m pip install -r backend/requirements.txt
```

If you want OCR to work locally, Tesseract must also be installed on the machine:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

### 3) Run the API

```bash
cd /workspaces/lettro.io
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4) Run the frontend

```bash
cd /workspaces/lettro.io/frontend
python -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

### 5) Test the app

Use either of the following flows:

- Select a sample letter from the dropdown and click “Run sample”
- Upload a letter image and click “Scan Letter”
- Use the camera button to capture a letter directly from the webcam

The API endpoints available are:

- `POST /ocr` — OCR from an uploaded image
- `POST /analyze` — redact text and call the LLM
- `POST /save_scan` — store a scan record
- `GET /history` — retrieve previous scan records
- `GET /sample_letters` — list local sample letters
- `POST /run_sample` — run one local sample through the full flow

### 6) Expected behavior

The app should:

- detect the letter language
- redact PII before sending anything to the LLM
- return a structured JSON analysis that matches the schema contract
- show a plain-language summary, deadline, required action, and consequence if missed

## Disclaimer

Lettro is not a substitute for legal or professional advice. Always verify deadlines and requirements against the original letter or with a qualified professional.
