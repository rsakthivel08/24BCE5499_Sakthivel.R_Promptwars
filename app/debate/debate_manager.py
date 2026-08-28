"""
app/debate/debate_manager.py
─────────────────────────────
Orchestrates the 2-round structured multi-agent debate.

Round 1: Each agent challenges or responds to the most important point
         from any other agent's independent evaluation.

Round 2: Agents respond to Round 1 challenges — agreeing, disagreeing,
         or updating their opinions.

Final:   A neutral moderator LLM summarises agreements, disagreements,
         and unresolved issues.
"""
from __future__ import annotations

from typing import Any

from app.debate.debate_prompts import (
    build_round1_prompt,
    build_round2_prompt,
    build_summary_prompt,
)
from app.debate.schema import DebateRound, DebateTurnSchema, DebateTranscript
from app.utils.llm_client import call_llm_json
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

AGENT_ORDER = [
    "Technical Agent",
    "Skeptic Agent",
    "HR Agent",
    "Hiring Manager Agent",
]


def _parse_turn(raw: dict[str, Any], fallback_speaker: str) -> DebateTurnSchema:
    raw.setdefault("speaker", fallback_speaker)
    raw.setdefault("addressing", "All")
    raw.setdefault("stance", "challenge")
    raw.setdefault("point_being_discussed", "general evaluation")
    raw.setdefault("message", "")
    raw.setdefault("evidence_cited", "")
    raw.setdefault("opinion_change", "none")
    return DebateTurnSchema(**raw)


def run_debate(opinions: list[dict[str, Any]]) -> DebateTranscript:
    """
    Run a full 2-round debate given the 4 independent agent opinions.

    Args:
        opinions: List of serialised AgentOpinionSchema dicts (one per agent).

    Returns:
        DebateTranscript with all turns, agreements, disagreements, and unresolved issues.
    """
    logger.info("debate_starting", agents=len(opinions))

    # ── Round 1: Challenges ───────────────────────────────────────────────────
    round1_turns: list[DebateTurnSchema] = []
    for agent_name in AGENT_ORDER:
        system, user = build_round1_prompt(agent_name, opinions)
        try:
            raw = call_llm_json(system, user, temperature=0.5, max_tokens=1500)
            turn = _parse_turn(raw, agent_name)
        except Exception as exc:
            logger.warning("debate_round1_failed", agent=agent_name, error=str(exc))
            turn = DebateTurnSchema(
                speaker=agent_name,
                addressing="All",
                stance="challenge",
                point_being_discussed="overall evaluation",
                message=f"[{agent_name}] had a technical issue generating a debate turn.",
                evidence_cited="",
                opinion_change="none",
            )
        round1_turns.append(turn)
        logger.info("round1_turn", speaker=agent_name, stance=turn.stance)

    # ── Round 2: Responses ────────────────────────────────────────────────────
    round1_dicts = [t.model_dump() for t in round1_turns]
    round2_turns: list[DebateTurnSchema] = []
    for agent_name in AGENT_ORDER:
        system, user = build_round2_prompt(agent_name, opinions, round1_dicts)
        try:
            raw = call_llm_json(system, user, temperature=0.5, max_tokens=1500)
            turn = _parse_turn(raw, agent_name)
        except Exception as exc:
            logger.warning("debate_round2_failed", agent=agent_name, error=str(exc))
            turn = DebateTurnSchema(
                speaker=agent_name,
                addressing="All",
                stance="update_opinion",
                point_being_discussed="overall evaluation",
                message=f"[{agent_name}] maintains its previous evaluation.",
                evidence_cited="",
                opinion_change="none",
            )
        round2_turns.append(turn)
        logger.info("round2_turn", speaker=agent_name, opinion_change=turn.opinion_change)

    # ── Summary ───────────────────────────────────────────────────────────────
    round2_dicts = [t.model_dump() for t in round2_turns]
    sys_p, usr_p = build_summary_prompt(opinions, round1_dicts, round2_dicts)
    try:
        summary_raw = call_llm_json(sys_p, usr_p, temperature=0.2, max_tokens=1500)
    except Exception as exc:
        logger.warning("debate_summary_failed", error=str(exc))
        summary_raw = {
            "updated_opinions": {},
            "key_agreements": [],
            "key_disagreements": [],
            "unresolved_issues": [],
        }

    transcript = DebateTranscript(
        rounds=[
            DebateRound(round_number=1, turns=round1_turns),
            DebateRound(round_number=2, turns=round2_turns),
        ],
        updated_opinions=summary_raw.get("updated_opinions", {}),
        key_agreements=summary_raw.get("key_agreements", []),
        key_disagreements=summary_raw.get("key_disagreements", []),
        unresolved_issues=summary_raw.get("unresolved_issues", []),
    )
    logger.info(
        "debate_complete",
        agreements=len(transcript.key_agreements),
        disagreements=len(transcript.key_disagreements),
        unresolved=len(transcript.unresolved_issues),
    )
    return transcript
