"""
app/agents/hiring_manager_agent.py
────────────────────────────────────
Hiring Manager Agent — evaluates role fit, business value, and hiring risk.
"""
from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.agents.prompts.hiring_manager_prompt import HIRING_MANAGER_AGENT_SYSTEM_PROMPT


class HiringManagerAgent(BaseAgent):
    name: str = "Hiring Manager Agent"

    @property
    def system_prompt(self) -> str:
        return HIRING_MANAGER_AGENT_SYSTEM_PROMPT
