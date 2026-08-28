"""
app/judge/judge_agent.py
─────────────────────────
The Final Decision Agent — synthesises all evaluations and debate into a
reasoned hiring recommendation. Explicitly NOT a score average.
"""
from __future__ import annotations

from typing import Any

from app.judge.judge_prompts import JUDGE_SYSTEM_PROMPT, build_judge_user_message
from app.judge.schema import FinalReportSchema
from app.utils.llm_client import call_llm_json
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def run_judge(
    candidate_profile: dict[str, Any],
    opinions: list[dict[str, Any]],
    debate_transcript: dict[str, Any],
    target_role: str = "",
) -> FinalReportSchema:
    """
    Run the Judge Agent to produce a final hiring recommendation.

    Args:
        candidate_profile: CandidateProfile dict
        opinions: List of AgentOpinion dicts (one per agent)
        debate_transcript: DebateTranscript dict
        target_role: The job role being evaluated for

    Returns:
        Validated FinalReportSchema
    """
    logger.info("judge_starting", target_role=target_role, opinions=len(opinions))

    user_message = build_judge_user_message(
        candidate_profile=candidate_profile,
        opinions=opinions,
        debate_transcript=debate_transcript,
        target_role=target_role,
    )

    raw = call_llm_json(
        system_prompt=JUDGE_SYSTEM_PROMPT,
        user_message=user_message,
        temperature=0.2,  # Low temperature for consistent, careful reasoning
        max_tokens=4096,
    )

    # Set candidate and role if not populated by LLM
    raw.setdefault("candidate_name", candidate_profile.get("candidate_name", ""))
    raw.setdefault("target_role", target_role)

    report = FinalReportSchema(**raw)
    logger.info(
        "judge_complete",
        recommendation=report.final_recommendation,
        confidence=report.confidence_score,
        unresolved=len(report.unresolved_disagreements),
    )
    return report
