

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

## Disclaimer

Lettro is not a substitute for legal or professional advice. Always verify deadlines and requirements against the original letter or with a qualified professional.
