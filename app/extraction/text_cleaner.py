"""
app/extraction/text_cleaner.py
───────────────────────────────
Cleans extracted raw text: removes noise, normalises whitespace,
and truncates to a safe token limit for the LLM.
"""
from __future__ import annotations

import re


_MAX_CHARS = 8_000  # ~2000 tokens — keeps combined prompt comfortably within Groq TPM limits


def clean_text(raw: str, max_chars: int = _MAX_CHARS) -> str:
    """
    1. Remove non-printable / control characters (except newlines/tabs).
    2. Collapse runs of whitespace lines to max two blank lines.
    3. Strip leading/trailing whitespace per line.
    4. Truncate to max_chars with a clear notice.
    """
    # Remove control characters except \n \t \r
    cleaned = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", " ", raw)

    # Normalise line endings
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # Strip per-line whitespace
    lines = [line.strip() for line in cleaned.split("\n")]

    # Collapse 3+ consecutive blank lines to 2
    result_lines: list[str] = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                result_lines.append("")
        else:
            blank_count = 0
            result_lines.append(line)

    result = "\n".join(result_lines).strip()

    # Truncate if necessary
    if len(result) > max_chars:
        result = result[:max_chars] + f"\n\n[... document truncated at {max_chars} characters ...]"

    return result
