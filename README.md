![Description of image](lettro-logo.svg)

# Lettro

Lettro explains confusing official letters — from government agencies, insurers, landlords, or any other formal sender — in plain language, in whatever language the reader actually understands.

## The problem

People who do not fluently read the language a letter arrives in often cannot tell what it is asking of them, what the deadline is, or what happens if they miss it. Many turn to online translation tools, which means handing documents with personal information — case numbers, addresses, financial details — to a third party.

## What Lettro does

- Reads a photo or PDF of a letter, in any source language
- Extracts the sender, letter type, a plain-language summary, the deadline, and the required next steps
- Returns the explanation in the reader's preferred language
- Tries to keep sensitive personal details from leaving the device unnecessarily
- Supports a local Ollama model path for privacy-first testing and development

## Current features

- Local Ollama/OpenAI-compatible model support
- Local model status indicator in the frontend
- Multiple-file upload support (up to 30 files)
- Total upload limit of 20 MB per batch
- Strict supported-format enforcement for PDF, PNG, JPG, JPEG, WebP, TIFF
- PDF extraction with OCR fallback for scanned documents
- Language selection for multiple European and international language targets
- Sample-letter runner and history drawer
- Backend schema validation to keep LLM output aligned with the required JSON contract

## Status

The project is now running in a local privacy-first mode and is suitable for local testing with Ollama. The backend validation and local-model flow have been verified with automated tests.

## Repo structure

```
/backend       — FastAPI API, OCR, validation, LLM integration
/frontend      — static HTML/CSS/JS app
/prompts       — prompt versions
/schema        — JSON schema files
/test-letters  — anonymized sample letters for local testing
```

## Local setup and testing

### 1) Install dependencies

```bash
cd ~/lettro.io
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

If OCR is required for scans or PDFs, install Tesseract.

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

### 2) Install and run Ollama locally

Install Ollama from the official package for your OS, then pull a small local model:

```bash
ollama pull qwen3:4b
```

Verify the server is up:

```bash
curl http://localhost:11434/api/tags
```

You should see `qwen3:4b` listed.

### 3) Configure environment variables

The backend automatically loads `.env` at startup through `python-dotenv`.

Create a local `.env` file from the template:

```bash
cd ~/lettro.io
cp .env.example .env
```

For local Ollama testing, use:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=qwen3:4b
```

If you want to use cloud providers instead, set the appropriate Anthropic or OpenAI values in `.env`.

> The `.env` file is local-only and should not be committed.

### 4) Start the backend

```bash
cd ~/lettro.io
source .venv/bin/activate
export LLM_PROVIDER=openai
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_MODEL=qwen3:4b
uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

You can also start it with inline environment variables in one command:

```bash
cd ~/lettro.io && LLM_PROVIDER=openai OPENAI_API_KEY=ollama OPENAI_BASE_URL=http://localhost:11434/v1 OPENAI_MODEL=qwen3:4b uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

### 5) Start the frontend

```bash
cd ~/lettro.io/frontend
python -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

### 6) Test the app

Use either of the following flows:

- Select a sample letter and click “Run sample”
- Upload PDF/image files and click “Scan Letter”
- Use the camera button to capture a letter from the webcam

### 7) Check the local model status

The app calls `GET /llm_status`, which returns JSON like:

```json
{"provider":"ollama","kind":"local","available":true,"model":"qwen3:4b","message":"Ollama is running and qwen3:4b is installed"}
```

If `available` is false, the most common reasons are:

- Ollama is not installed or not running
- the model is not pulled
- the backend was started without the env variables
- the backend is pointing at the wrong port or base URL

## API endpoints

- `GET /llm_status` — local/cloud model state
- `GET /sample_letters` — list sample letters
- `POST /ocr` — OCR one or more uploaded files
- `POST /analyze` — analyze OCR text with the configured LLM
- `POST /run_sample` — run one included test letter through the full flow
- `POST /save_scan` — save a scan result to SQLite
- `GET /history` — load saved scans

## Environment variable behavior

The app does not automatically keep reading new shell variables after startup. The backend loads environment values when the Python process starts, using `load_dotenv()` from `.env` and the current process environment.

That means:

- if you launch `uvicorn` in a shell where the variables are exported, they are available immediately
- if you place them in `.env`, they are read on each backend start
- if you change `.env` while the server is running, you must restart the backend to reload them

## Expected behavior

The app should:

- detect the letter language
- redact PII before sending anything to the LLM
- return a structured JSON analysis that matches the schema contract
- show a plain-language summary, deadline, required action, and consequence if missed
- keep model access local when using Ollama

## Disclaimer

Lettro is not a substitute for legal or professional advice. Always verify deadlines and requirements against the original letter or with a qualified professional.
