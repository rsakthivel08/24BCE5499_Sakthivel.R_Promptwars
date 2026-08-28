"""
app/agents/hr_agent.py
───────────────────────
HR / Culture Agent — evaluates soft skills, teamwork, communication, and culture fit.
"""
from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.agents.prompts.hr_prompt import HR_AGENT_SYSTEM_PROMPT


class HRAgent(BaseAgent):
    name: str = "HR Agent"

    @property
    def system_prompt(self) -> str:
        return HR_AGENT_SYSTEM_PROMPT
