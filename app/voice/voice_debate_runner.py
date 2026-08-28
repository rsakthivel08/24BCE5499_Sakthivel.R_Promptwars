"""
app/voice/voice_debate_runner.py
──────────────────────────────────
Converts a DebateTranscript into per-turn audio files using the TTS engine.
Ensures audio and text remain consistent.
"""
from __future__ import annotations

from typing import Any

from app.voice.tts_engine import generate_speech
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def _format_spoken_text(turn: dict[str, Any]) -> str:
    """Convert a debate turn dict into natural spoken language."""
    speaker = turn.get("speaker", "Agent")
    addressing = turn.get("addressing", "")
    message = turn.get("message", "")

    if addressing and addressing != "All" and addressing != speaker:
        prefix = f"Responding to the {addressing}: "
    else:
        prefix = ""

    return f"{prefix}{message}"


def generate_voice_debate(
    debate_transcript: dict[str, Any],
    evaluation_id: str,
) -> list[dict[str, Any]]:
    """
    Generate audio for each debate turn and return an enriched turn list
    with audio_url fields.

    Args:
        debate_transcript: Serialised DebateTranscript dict
        evaluation_id: Used to organise audio files

    Returns:
        List of turn dicts enriched with 'audio_url' fields (relative URL or None).
    """
    enriched_turns: list[dict[str, Any]] = []
    turn_index = 0

    for round_data in debate_transcript.get("rounds", []):
        round_num = round_data.get("round_number", 0)
        for turn in round_data.get("turns", []):
            speaker = turn.get("speaker", "Agent")
            spoken_text = _format_spoken_text(turn)

            audio_path = generate_speech(spoken_text, speaker)

            audio_url: str | None = None
            if audio_path is not None:
                # Build a relative URL the frontend can fetch.
                # This MUST match the actual route in voice_routes.py, which is
                # registered under prefix="/api" -> GET /api/audio/{filename}.
                # (Previously this omitted the /api prefix, so the URL fell through
                # to the StaticFiles("/") mount and 404'd on every generated clip.)
                audio_url = f"/api/audio/{audio_path.name}"

            enriched_turn = {
                **turn,
                "round_number": round_num,
                "turn_index": turn_index,
                "audio_url": audio_url,
                "spoken_text": spoken_text,
            }
            enriched_turns.append(enriched_turn)
            turn_index += 1

    logger.info(
        "voice_debate_generated",
        total_turns=len(enriched_turns),
        with_audio=sum(1 for t in enriched_turns if t.get("audio_url")),
    )
    return enriched_turns
