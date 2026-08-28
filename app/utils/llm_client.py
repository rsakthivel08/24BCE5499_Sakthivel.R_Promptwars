"""
app/utils/llm_client.py
────────────────────────
Groq LLM client with retry logic and structured JSON output.
- 413 (request too large): fails immediately with a clear message — no point retrying.
- 429 (rate limit):        retries up to 4 times with exponential back-off up to 60 s.
- Other errors:            retries up to 3 times with shorter back-off.
"""
from __future__ import annotations

import json
import re
from typing import Any

from groq import Groq, APIStatusError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    RetryCallState,
)

from app.config import get_settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def _get_client() -> Groq:
    settings = get_settings()
    return Groq(api_key=settings.groq_api_key)


def _extract_json(text: str) -> dict[str, Any]:
    """
    Robust JSON extractor:
    1. Direct json.loads
    2. Markdown code fence extraction
    3. First {...} regex block extraction
    4. json_repair.repair_json fallback
    """
    # 1. Direct parse
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown fences ```json ... ```
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        fence_text = fence.group(1).strip()
        try:
            data = json.loads(fence_text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    # 3. Find first {...} block
    brace = re.search(r"\{[\s\S]*\}", text)
    if brace:
        brace_text = brace.group().strip()
        try:
            data = json.loads(brace_text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    # 4. json_repair fallback for malformed JSON (handles internal quotes, missing commas, etc.)
    try:
        from json_repair import repair_json
        data = repair_json(text, return_objects=True)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        logger.debug("json_repair_fallback_failed", error=str(exc))

    raise ValueError(f"Could not extract valid JSON from model response:\n{text[:500]}")


def _is_retryable(exc: BaseException) -> bool:
    """
    Retry only on 429 (rate limit) and server errors (5xx).
    Do NOT retry on 413 (request too large) — same payload = same failure.
    """
    if isinstance(exc, APIStatusError):
        if exc.status_code == 413:
            return False  # fail fast — reduce payload instead
        if exc.status_code == 429:
            return True
        return exc.status_code >= 500
    # Retry transient network / connection errors
    return not isinstance(exc, (ValueError, RuntimeError))


def _before_retry(retry_state: RetryCallState) -> None:
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    if isinstance(exc, APIStatusError) and exc.status_code == 429:
        logger.warning(
            "groq_rate_limit_retry",
            attempt=retry_state.attempt_number,
        )
    else:
        logger.warning(
            "llm_retry",
            attempt=retry_state.attempt_number,
            error=str(exc),
        )


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    before_sleep=_before_retry,
    reraise=True,
)
def call_llm(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    """Single LLM call — returns raw text response."""
    settings = get_settings()
    model = model or settings.groq_model_agents
    client = _get_client()

    # Safety guard: ensure user_message never exceeds 7,000 chars (~1,700 tokens)
    # This prevents prompt + max_tokens from exceeding Groq's 6,000 TPM limit
    _MAX_USER_LEN = 7_000
    if len(user_message) > _MAX_USER_LEN:
        logger.warning(
            "llm_user_message_truncated",
            original_len=len(user_message),
            max_len=_MAX_USER_LEN,
        )
        user_message = user_message[:_MAX_USER_LEN] + "\n\n[... document content truncated to fit within model limits ...]"

    logger.debug(
        "llm_call",
        model=model,
        system_len=len(system_prompt),
        user_len=len(user_message),
    )

    try:
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
    except APIStatusError as e:
        if e.status_code == 413:
            logger.error(
                "llm_request_too_large",
                model=model,
                system_len=len(system_prompt),
                user_len=len(user_message),
                hint="Reduce prompt payload — token limit exceeded.",
            )
            raise RuntimeError(
                f"Request too large for model '{model}'. "
                f"Prompt sizes: system={len(system_prompt)} chars, "
                f"user={len(user_message)} chars. "
                "Reduce the data passed in the prompt."
            ) from e
        raise


def call_llm_json(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """LLM call that returns parsed JSON dict."""
    raw = call_llm(
        system_prompt=system_prompt,
        user_message=user_message,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return _extract_json(raw)



