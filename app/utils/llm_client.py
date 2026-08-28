"""
app/utils/llm_client.py
────────────────────────
Groq LLM client with retry logic and structured JSON output.
"""
from __future__ import annotations

import json
import re
from typing import Any

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def _get_client() -> Groq:
    settings = get_settings()
    return Groq(api_key=settings.groq_api_key)


def _extract_json(text: str) -> dict[str, Any]:
    """Extract first JSON object found in model output."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass

    # Find first {...} block
    brace = re.search(r"\{[\s\S]*\}", text)
    if brace:
        try:
            return json.loads(brace.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from model response:\n{text[:500]}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def call_llm(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Single LLM call — returns raw text response."""
    settings = get_settings()
    model = model or settings.groq_model_agents
    client = _get_client()

    logger.debug("llm_call", model=model, system_len=len(system_prompt))

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def call_llm_json(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """LLM call that returns parsed JSON dict."""
    raw = call_llm(system_prompt, user_message, model, temperature, max_tokens)
    return _extract_json(raw)
