"""
app/judge/judge_prompts.py
───────────────────────────
System prompt and user message builder for the Judge Agent.
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


def build_judge_user_message(
    candidate_profile: dict[str, Any],
    opinions: list[dict[str, Any]],
    debate_transcript: dict[str, Any],
    target_role: str = "",
) -> str:
    return f"""\
Please produce the final hiring recommendation.

Target Role: {target_role or "Not specified"}

════════════════════════════════
CANDIDATE PROFILE
════════════════════════════════
{json.dumps(candidate_profile, indent=2)}

════════════════════════════════
INDEPENDENT AGENT EVALUATIONS
════════════════════════════════
{json.dumps(opinions, indent=2)}

════════════════════════════════
DEBATE TRANSCRIPT
════════════════════════════════
{json.dumps(debate_transcript, indent=2)}

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
