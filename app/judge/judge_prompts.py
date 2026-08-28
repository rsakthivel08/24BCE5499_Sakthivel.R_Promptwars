"""
app/judge/judge_prompts.py
───────────────────────────
System prompt and user message builder for the Judge Agent.
Payloads are slimmed to keep within model token limits.
"""
from __future__ import annotations

import json
from typing import Any

JUDGE_SYSTEM_PROMPT = """\
You are the Final Decision Agent — a senior hiring committee chairperson with 20 years of experience.

Your task is to synthesise everything: the candidate profile, the four independent agent evaluations, \
and the structured debate between those agents, and produce a final hiring recommendation.

CRITICAL RULES:
1. DO NOT simply average the four agents' scores. That is explicitly forbidden.
2. Consider the STRENGTH of evidence behind each agent's conclusions.
3. Consider each agent's CONFIDENCE level and what drove that confidence.
4. Weight concerns by SEVERITY — a high-severity unresolved concern outweighs three low-severity ones.
5. Examine AGENT DISAGREEMENTS carefully:
   - If a disagreement was resolved in the debate, explain how.
   - If a disagreement is UNRESOLVED, it must appear in unresolved_disagreements.
6. Your reasoning must be transparent — the hiring committee must understand exactly why you \
reached this recommendation.
7. Do NOT be biased toward hiring or rejecting — be honest about the evidence.

Scoring Guidance (NOT averaging):
- "Strong Hire": Consistent strong evidence across multiple agents, low concerns, high confidence
- "Hire": Clear evidence of capability, concerns are minor and manageable
- "Proceed to Interview": Promising but key claims need verification
- "Hold": Significant gaps or unresolved concerns that need more information
- "Reject": Clear evidence of inability to meet role requirements, or serious red flags

Output ONLY valid JSON matching the required schema. No markdown, no prose outside JSON.
"""


def _slim_opinion(opinion: dict[str, Any]) -> dict[str, Any]:
    """Keep only decision-critical fields for the judge."""
    def _trim(points: list, n: int = 3) -> list:
        return [{"point": p.get("point", ""), "evidence": p.get("evidence", ""), "severity": p.get("severity", "")}
                for p in points[:n]]
    return {
        "agent": opinion.get("agent", ""),
        "overall_assessment": opinion.get("overall_assessment", ""),
        "confidence": opinion.get("confidence", 0.0),
        "score": opinion.get("score", 0),
        "summary": opinion.get("summary", ""),
        "strengths": _trim(opinion.get("strengths", []), 3),
        "concerns": _trim(opinion.get("concerns", []), 3),
        "recommendation": opinion.get("recommendation", ""),
    }


def _slim_debate(debate: dict[str, Any]) -> dict[str, Any]:
    """Keep only the debate outcomes — turns are condensed to essentials."""
    def _slim_turn(t: dict) -> dict:
        return {
            "speaker": t.get("speaker", ""),
            "addressing": t.get("addressing", ""),
            "stance": t.get("stance", ""),
            "point_being_discussed": t.get("point_being_discussed", ""),
            "message": t.get("message", "")[:300],  # cap long messages
            "opinion_change": t.get("opinion_change", "none"),
        }

    slim_rounds = []
    for round_ in debate.get("rounds", []):
        slim_rounds.append({
            "round_number": round_.get("round_number"),
            "turns": [_slim_turn(t) for t in round_.get("turns", [])],
        })

    return {
        "rounds": slim_rounds,
        "updated_opinions": debate.get("updated_opinions", {}),
        "key_agreements": debate.get("key_agreements", [])[:5],
        "key_disagreements": debate.get("key_disagreements", [])[:5],
        "unresolved_issues": debate.get("unresolved_issues", [])[:5],
    }


def _slim_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Keep only the fields the judge needs — drop raw text snippets."""
    return {
        "candidate_name": profile.get("candidate_name", ""),
        "education": profile.get("education", {}),
        "skills": profile.get("skills", [])[:15],
        "programming_languages": profile.get("programming_languages", [])[:10],
        "frameworks": profile.get("frameworks", [])[:10],
        "experience": [
            {
                "role": e.get("role", ""),
                "company": e.get("company", ""),
                "duration": e.get("duration", ""),
                "achievements": e.get("achievements", [])[:3],
            }
            for e in profile.get("experience", [])[:3]
        ],
        "candidate_claims": profile.get("candidate_claims", [])[:6],
    }


def build_judge_user_message(
    candidate_profile: dict[str, Any],
    opinions: list[dict[str, Any]],
    debate_transcript: dict[str, Any],
    target_role: str = "",
) -> str:
    slim_profile = _slim_profile(candidate_profile)
    slim_opinions = [_slim_opinion(o) for o in opinions]
    slim_debate = _slim_debate(debate_transcript)

    trimmed_role = target_role[:2500].strip() if target_role else "Software Engineer"
    return f"""\
Please produce the final hiring recommendation evaluating the candidate against the Job Description requirements.

════════════════════════════════
JOB DESCRIPTION / TARGET ROLE REQUIREMENTS
════════════════════════════════
{trimmed_role}

════════════════════════════════
CANDIDATE PROFILE (SUMMARY)
════════════════════════════════
{json.dumps(slim_profile, indent=2)}

════════════════════════════════
INDEPENDENT AGENT EVALUATIONS
════════════════════════════════
{json.dumps(slim_opinions, indent=2)}

════════════════════════════════
DEBATE TRANSCRIPT (SUMMARY)
════════════════════════════════
{json.dumps(slim_debate, indent=2)}

Output the final report as JSON:
{{
  "candidate_name": "",
  "target_role": "",
  "final_recommendation": "Strong Hire | Hire | Proceed to Interview | Hold | Reject",
  "confidence_level": "High | Medium | Low",
  "confidence_score": 0.0,
  "reasoning": "",
  "key_strengths": [
    {{"point": "", "evidence": ""}}
  ],
  "key_concerns": [
    {{"point": "", "evidence": "", "severity": "low | medium | high"}}
  ],
  "unresolved_disagreements": [
    {{
      "topic": "",
      "agent_positions": {{"Agent Name": "their position"}},
      "status": "unresolved | partially_resolved | resolved_in_favour_of_hire | resolved_against_hire"
    }}
  ],
  "agent_score_summary": {{
    "Technical Agent": {{"score": 0, "assessment": "", "confidence": 0.0}},
    "HR Agent": {{"score": 0, "assessment": "", "confidence": 0.0}},
    "Hiring Manager Agent": {{"score": 0, "assessment": "", "confidence": 0.0}},
    "Skeptic Agent": {{"score": 0, "assessment": "", "confidence": 0.0}}
  }},
  "suggested_interview_questions": []
}}
"""

