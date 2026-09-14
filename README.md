![Description of image](lettro-logo.svg)

# Lettro

Lettro is a local-first letter understanding app. It helps users read formal letters, identify what they mean, and understand what action is required without needing to hand the document to a generic online translation tool.

The project is designed for privacy-sensitive local use: OCR runs on the local machine, the app can use a local Ollama model, and the backend validates the LLM output against a strict JSON schema before presenting it to the user.

## Product goal

Lettro turns a letter into a simple, trusted summary:

- who sent it
- what type of letter it is
- whether action is required
- what the deadline is
- what happens if the deadline is missed
- how the app reached that conclusion

## Architecture

The current architecture is intentionally simple and local-first:

```text
Browser / static frontend
        |
        v
     HTTP API (FastAPI)
        |
        +--> OCR pipeline
        |       + PDF / image upload validation
        |       + Tesseract OCR
        |       + PDF fallback / scanned PDF handling
        |
        +--> Redaction layer
        |       + email, phone, ZIP, IBAN, account references, case IDs
        |
        +--> LLM adapter
        |       + Ollama / OpenAI-compatible endpoint
        |       + Anthropic option
        |       + default local model: qwen3:4b
        |
        +--> JSON normalization
        |       + schema cleanup
        |       + evidence preservation
        |
        +--> JSON schema validation
                + schema-v2 contract enforced

        +--> Local SQLite history (opt-in only)
```

The backend lives in backend/main.py, the schema is in schema/schema-v2.json, and the static UI is in frontend/index.html and frontend/app.js.

## Current app features

- Local Ollama/OpenAI-compatible inference with a default model of qwen3:4b
- Strict model-status checking through /llm_status
- OCR for PDF and image uploads
- OCR fallback for scanned PDFs via PyMuPDF rasterization
- Multi-file uploads with strict batch limits
- Supported file validation for PDF, PNG, JPG, JPEG, WebP, TIFF
- Local sample-letter runner for reproducible testing
- JSON schema validation before results are shown to users
- Evidence-aware result display for deadlines and required actions
- Privacy-oriented redaction for common sensitive identifiers
- Optional local scan history (disabled by default until the user opts in)

## Privacy and security posture

This app is designed for local testing and privacy-conscious use, not as a public cloud service.

Current safeguards include:

- document text is sanitized before sending it to the LLM
- common invoice/account identifiers are masked
- upload file types and content signatures are checked
- prompt-injection guidance prevents document text from acting as instructions
- the app never treats document content as trusted control instructions
- local SQLite history is opt-in rather than enabled by default

> This is not a formal legal/privacy guarantee. It is a local-first MVP with explicit safeguards and manual review requirements.

## Repository layout

```text
/backend        FastAPI app, OCR, schema validation, model adapters, storage
/frontend       Static HTML/CSS/JS interface
/prompts        Prompt templates and prompt-injection guards
/schema         Schema definitions for structured output
/test-letters   Local sample letters used for validation and QA
```

## Local setup

### 1) Create a virtual environment and install Python dependencies

```bash
cd /workspaces/lettro.io
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

### 2) Install OCR support

If you want OCR on scanned PDFs or images, install Tesseract:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

### 3) Pull the local model

Install Ollama and pull the default model:

```bash
ollama pull qwen3:4b
```

Verify the model is available:

```bash
curl http://localhost:11434/api/tags
```

### 4) Configure environment variables

The backend loads variables from `.env` and the current shell automatically on startup.

Example local Ollama setup:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=qwen3:4b
```

You can also configure Anthropic or other OpenAI-compatible endpoints as needed.

### 5) Run the backend

```bash
cd /workspaces/lettro.io
source .venv/bin/activate
export LLM_PROVIDER=openai
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_MODEL=qwen3:4b
uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

### 6) Run the frontend

```bash
cd /workspaces/lettro.io/frontend
python -m http.server 8080
```

Open:

```text
http://localhost:8080
```

## API overview

Main routes exposed by the backend:

- GET /llm_status — check the configured model and whether it is installed
- GET /sample_letters — list available sample letters
- POST /ocr — OCR and normalize uploaded files
- POST /analyze — analyze text using the configured model
- POST /run_sample — run a sample file through the full pipeline
- POST /save_scan — save a scan to SQLite, only when the UI opt-in is enabled
- GET /history — list saved scan history entries

## Local testing flow

You can test the app in either of these ways:

1. Select a sample letter and click “Run sample”
2. Upload PDF/image files and click “Scan Letter”
3. Use the camera button to capture a scanned letter directly from the webcam

## Important development notes

- The backend loads environment values when it starts. If you change .env while the server is already running, restart the backend.
- The default app path is local-only: frontend on http://localhost:8080, backend on http://localhost:8001.
- The project currently expects a local model setup for the strongest privacy story.

## Validation and quality gates

The project includes backend regression tests for:

- schema validation
- hidden extra fields rejection
- redaction behavior
- upload validation
- model config defaults
- model status detection
- sample traversal protections

Run the checks with:

```bash
cd /workspaces/lettro.io
pytest backend/test_backend.py -q
```

## Disclaimer

Lettro is designed to help interpret letters and deadlines, but it is not legal advice. Always verify key deadlines and obligations against the original document and, where necessary, consult a professional or authority directly.
