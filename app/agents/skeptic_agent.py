"""
app/agents/skeptic_agent.py
────────────────────────────
Skeptic Agent — critical reviewer searching for contradictions and unsupported claims.
"""
from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.agents.prompts.skeptic_prompt import SKEPTIC_AGENT_SYSTEM_PROMPT


class SkepticAgent(BaseAgent):
    name: str = "Skeptic Agent"

    @property
    def system_prompt(self) -> str:
        return SKEPTIC_AGENT_SYSTEM_PROMPT
