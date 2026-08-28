"""
app/agents/base_agent.py
─────────────────────────
Abstract base class for all evaluation agents.
Each subclass defines its own system prompt and calls the LLM independently.
CRITICAL: No agent sees another agent's opinion at this stage.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from app.agents.schema import AgentOpinionSchema
from app.utils.llm_client import call_llm_json
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_AGENT_USER_TEMPLATE = """\
You are evaluating the following candidate for the role: {target_role}

═══════════════════════════════════════
CANDIDATE PROFILE (JSON)
═══════════════════════════════════════
{profile_json}

Perform your independent evaluation now.
Remember: every strength and concern MUST include a direct quote or factual reference
from the candidate's profile above — do NOT invent evidence.

Output ONLY a single valid JSON object matching this structure:
{{
  "agent": "{agent_name}",
  "overall_assessment": "Strong Hire | Hire | Proceed to Interview | Hold | Reject",
  "confidence": 0.0,
  "score": 0,
  "summary": "",
  "strengths": [
    {{"point": "", "evidence": "", "severity": "positive"}}
  ],
  "concerns": [
    {{"point": "", "evidence": "", "severity": "low | medium | high"}}
  ],
  "recommendation": "",
  "questions_for_interview": []
}}

Provide at most 4 strengths, 4 concerns, and 3 interview questions.
"""


class BaseAgent(ABC):
    """Abstract base for all four evaluation agents."""

    name: str = "Base Agent"

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return this agent's persona system prompt."""
        ...

    def evaluate(
        self,
        candidate_profile: dict[str, Any],
        target_role: str = "Software Engineer",
    ) -> AgentOpinionSchema:
        """
        Run an INDEPENDENT evaluation — no other agent's output is passed in.

        Args:
            candidate_profile: dict from CandidateProfile.model_dump_for_agent()
            target_role: The job role being evaluated for

        Returns:
            Validated AgentOpinionSchema
        """
        logger.info("agent_evaluating", agent=self.name, target_role=target_role)

        user_message = _AGENT_USER_TEMPLATE.format(
            target_role=target_role,
            profile_json=json.dumps(candidate_profile, indent=2),
            agent_name=self.name,
        )

        raw = call_llm_json(
            system_prompt=self.system_prompt,
            user_message=user_message,
            temperature=0.4,
            max_tokens=2500,
        )

        # Ensure agent name matches
        raw["agent"] = self.name

        opinion = AgentOpinionSchema(**raw)
        logger.info(
            "agent_evaluation_complete",
            agent=self.name,
            score=opinion.score,
            confidence=opinion.confidence,
            assessment=opinion.overall_assessment,
        )
        return opinion
