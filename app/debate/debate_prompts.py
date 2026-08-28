"""
app/debate/debate_prompts.py
─────────────────────────────
System and user prompts for each agent during the debate rounds.
"""
from __future__ import annotations

import json
from typing import Any

DEBATE_SYSTEM_PROMPTS: dict[str, str] = {
    "Technical Agent": """\
You are the Technical Agent participating in a structured hiring debate.
You have already evaluated this candidate independently. 
Now you must engage with the other agents' arguments — agreeing, disagreeing, or challenging them \
with evidence from the candidate's profile.
Stay in character: you care about technical depth and evidence of real skills.
Output ONLY valid JSON for your debate turn.""",

    "HR Agent": """\
You are the HR Agent participating in a structured hiring debate.
You have already evaluated this candidate independently.
Now you must respond to the other agents — especially challenging concerns about soft skills, \
leadership, or cultural fit with evidence.
Stay in character: you care about people, team dynamics, and professional integrity.
Output ONLY valid JSON for your debate turn.""",

    "Hiring Manager Agent": """\
You are the Hiring Manager Agent participating in a structured hiring debate.
You have already evaluated this candidate independently.
Now you must weigh in on the debate — considering the business case and role fit.
Stay in character: you must make a pragmatic call about hiring risk and value.
Output ONLY valid JSON for your debate turn.""",

    "Skeptic Agent": """\
You are the Skeptic Agent participating in a structured hiring debate.
You have already evaluated this candidate independently with a critical eye.
Now challenge the other agents' conclusions where you find insufficient evidence.
Stay in character: you are the rigorous devil's advocate who protects against poor hires.
Output ONLY valid JSON for your debate turn.""",
}


_ROUND1_CHALLENGE_TEMPLATE = """\
The four agents have completed their independent evaluations:

{opinions_json}

════════════════════════════════
ROUND 1 — CHALLENGE PHASE
════════════════════════════════

You are: {agent_name}

Read ALL four independent opinions above carefully.

Your task: Identify the MOST IMPORTANT point made by another agent that you want to challenge, \
question, or build upon. You must respond directly to a specific agent's argument.

Output a JSON object matching this structure EXACTLY:
{{
  "speaker": "{agent_name}",
  "addressing": "<name of the agent you are responding to>",
  "stance": "agree | disagree | partially_agree | challenge | new_concern",
  "point_being_discussed": "<specific claim or topic>",
  "message": "<your full debate statement, 3–6 sentences, cite evidence>",
  "evidence_cited": "<direct quote or fact from the candidate profile>",
  "opinion_change": "none | increased_confidence | decreased_confidence | changed_recommendation"
}}
"""


_ROUND2_RESPONSE_TEMPLATE = """\
The four agents have completed their independent evaluations:

{opinions_json}

════════════════════════════════
ROUND 1 — CHALLENGES (completed)
════════════════════════════════

{round1_json}

════════════════════════════════
ROUND 2 — RESPONSE PHASE
════════════════════════════════

You are: {agent_name}

Read the Round 1 challenges above. Another agent may have challenged YOUR earlier argument,
or you may wish to respond to a challenge made by one agent against another.

Your task: Provide a direct response. You may:
- Defend your original position with additional evidence
- Partially concede a point
- Update your recommendation
- Agree with a challenge and explain why it changes your view

Output a JSON object matching this structure EXACTLY:
{{
  "speaker": "{agent_name}",
  "addressing": "<name of the agent you are responding to>",
  "stance": "agree | disagree | partially_agree | update_opinion",
  "point_being_discussed": "<specific claim or topic>",
  "message": "<your full response, 3–6 sentences, cite evidence>",
  "evidence_cited": "<direct quote or fact from the candidate profile>",
  "opinion_change": "none | increased_confidence | decreased_confidence | changed_recommendation"
}}
"""


_SUMMARY_TEMPLATE = """\
All four agents have completed two rounds of debate.

Independent Evaluations:
{opinions_json}

Round 1 Challenges:
{round1_json}

Round 2 Responses:
{round2_json}

════════════════════════════════
DEBATE SUMMARY
════════════════════════════════

Analyse the full debate above and produce a JSON summary:
{{
  "updated_opinions": {{
    "Technical Agent": "<updated overall_assessment or 'unchanged'>",
    "HR Agent": "<updated overall_assessment or 'unchanged'>",
    "Hiring Manager Agent": "<updated overall_assessment or 'unchanged'>",
    "Skeptic Agent": "<updated overall_assessment or 'unchanged'>"
  }},
  "key_agreements": ["<point agents agreed on>"],
  "key_disagreements": ["<point agents still disagree on>"],
  "unresolved_issues": ["<concern not resolved by debate>"]
}}
"""


def build_round1_prompt(agent_name: str, opinions: list[dict[str, Any]]) -> tuple[str, str]:
    system = DEBATE_SYSTEM_PROMPTS[agent_name]
    user = _ROUND1_CHALLENGE_TEMPLATE.format(
        opinions_json=json.dumps(opinions, indent=2),
        agent_name=agent_name,
    )
    return system, user


def build_round2_prompt(
    agent_name: str,
    opinions: list[dict[str, Any]],
    round1_turns: list[dict[str, Any]],
) -> tuple[str, str]:
    system = DEBATE_SYSTEM_PROMPTS[agent_name]
    user = _ROUND2_RESPONSE_TEMPLATE.format(
        opinions_json=json.dumps(opinions, indent=2),
        round1_json=json.dumps(round1_turns, indent=2),
        agent_name=agent_name,
    )
    return system, user


def build_summary_prompt(
    opinions: list[dict[str, Any]],
    round1_turns: list[dict[str, Any]],
    round2_turns: list[dict[str, Any]],
) -> tuple[str, str]:
    system = """\
You are a neutral debate moderator. Summarise the debate outcomes objectively.
Output ONLY valid JSON."""
    user = _SUMMARY_TEMPLATE.format(
        opinions_json=json.dumps(opinions, indent=2),
        round1_json=json.dumps(round1_turns, indent=2),
        round2_json=json.dumps(round2_turns, indent=2),
    )
    return system, user
