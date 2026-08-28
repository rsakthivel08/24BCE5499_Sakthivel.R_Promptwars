"""
app/agents/technical_agent.py
──────────────────────────────
Technical Agent — evaluates programming skills, projects, and technical depth.
"""
from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.agents.prompts.technical_prompt import TECHNICAL_AGENT_SYSTEM_PROMPT


class TechnicalAgent(BaseAgent):
    name: str = "Technical Agent"

    @property
    def system_prompt(self) -> str:
        return TECHNICAL_AGENT_SYSTEM_PROMPT
