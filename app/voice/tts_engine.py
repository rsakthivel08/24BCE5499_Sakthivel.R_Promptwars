"""
app/voice/tts_engine.py
────────────────────────
Sarvam AI TTS wrapper (Bulbul V3).
Generates per-persona audio clips with distinct voices and styles.
"""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import httpx

from app.config import get_settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Voice configuration per agent persona
# Sarvam Bulbul V3 speaker IDs (aditya, priya, ashutosh, ratan)
AGENT_VOICE_CONFIG: dict[str, dict] = {
    "Technical Agent": {
        "speaker": "aditya",    # Clear, analytical voice
        "pace": 1.0,
        "speech_sample_rate": 22050,
        "model": "bulbul:v3",
    },
    "HR Agent": {
        "speaker": "priya",     # Warm, empathetic voice
        "pace": 0.95,
        "speech_sample_rate": 22050,
        "model": "bulbul:v3",
    },
    "Hiring Manager Agent": {
        "speaker": "ashutosh",  # Authoritative, decisive voice
        "pace": 1.05,
        "speech_sample_rate": 22050,
        "model": "bulbul:v3",
    },
    "Skeptic Agent": {
        "speaker": "ratan",     # Measured, skeptical voice
        "pace": 0.90,
        "speech_sample_rate": 22050,
        "model": "bulbul:v3",
    },
}

_DEFAULT_VOICE = {
    "speaker": "aditya",
    "pace": 1.0,
    "speech_sample_rate": 22050,
    "model": "bulbul:v3",
}


def _get_audio_cache_path(text: str, speaker: str) -> Path:
    """Return a deterministic cache path for a given text+speaker combo."""
    key = hashlib.md5(f"{speaker}:{text}".encode()).hexdigest()
    return Path("data/audio") / f"{key}.wav"


def generate_speech(text: str, agent_name: str) -> Path | None:
    """
    Call the Sarvam AI TTS API to generate speech for the given text.

    Args:
        text: The text to convert to speech (max ~500 chars per call).
        agent_name: Agent name used to select voice config.

    Returns:
        Path to the saved WAV file, or None if TTS is unavailable.
    """
    settings = get_settings()
    if not settings.sarvam_api_key or settings.sarvam_api_key == "your_sarvam_api_key_here":
        logger.warning("sarvam_api_key_not_set", agent=agent_name)
        return None

    voice_cfg = AGENT_VOICE_CONFIG.get(agent_name, _DEFAULT_VOICE)

    # Check cache
    cache_path = _get_audio_cache_path(text, voice_cfg["speaker"])
    if cache_path.exists():
        logger.debug("tts_cache_hit", path=str(cache_path))
        return cache_path

    # Truncate to safe limit
    safe_text = text[:490] if len(text) > 490 else text

    payload = {
        "inputs": [safe_text],
        "target_language_code": "en-IN",
        "speaker": voice_cfg["speaker"],
        "pace": voice_cfg["pace"],
        "speech_sample_rate": voice_cfg["speech_sample_rate"],
        "enable_preprocessing": True,
        "model": voice_cfg["model"],
    }


    try:
        response = httpx.post(
            settings.sarvam_tts_url,
            json=payload,
            headers={
                "api-subscription-key": settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        # Sarvam returns base64-encoded audio
        audios = data.get("audios", [])
        if not audios:
            logger.error("tts_no_audio_returned", agent=agent_name)
            return None

        audio_bytes = base64.b64decode(audios[0])
        cache_path.write_bytes(audio_bytes)
        logger.info("tts_generated", agent=agent_name, path=str(cache_path))
        return cache_path

    except httpx.HTTPStatusError as exc:
        logger.error("tts_http_error", status=exc.response.status_code, agent=agent_name, response=exc.response.text)
        return None
    except Exception as exc:
        logger.error("tts_error", error=str(exc), agent=agent_name)
        return None
