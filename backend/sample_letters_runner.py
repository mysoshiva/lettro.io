#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

from backend.main import analyze_with_llm, build_prompt, redact_text

ROOT = Path(__file__).resolve().parent.parent
TEST_LETTERS_DIR = ROOT / "test-letters"


def extract_sample_text(markdown_text: str) -> str:
    match = re.search(
        r"## (?:Input|Letter text).*?\n(.*?)(?:\n## Expected output|\Z)",
        markdown_text,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        raise ValueError("Could not find sample input section in test letter file.")
    return match.group(1).strip()


def run_sample(letter_path: Path, target_language: str = "en") -> dict:
    markdown = letter_path.read_text(encoding="utf-8")
    extracted = extract_sample_text(markdown)
    redacted = redact_text(extracted)
    prompt = build_prompt(target_language, redacted)
    result = analyze_with_llm(prompt)
    result["_source_file"] = letter_path.name
    return result


def main() -> None:
    os.environ.setdefault("OPENAI_MODEL", "gpt-4o-mini")
    files = sorted(TEST_LETTERS_DIR.glob("*.md"))
    if not files:
        print("No sample letters found in test-letters/")
        return

    print(f"Running {len(files)} sample letters against the Lettro prompt...\n")
    for path in files:
        if path.name == "README.md":
            continue
        print(f"--- {path.name} ---")
        result = run_sample(path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()


if __name__ == "__main__":
    main()
