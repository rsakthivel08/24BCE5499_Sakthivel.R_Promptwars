"""
app/agents/schema.py
─────────────────────
Pydantic v2 schema for every agent's independent evaluation output.
Each field requires evidence — raw scores alone are not accepted.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class EvidencedPoint(BaseModel):
    """A single strength or concern backed by quoted evidence."""
    point: str = Field(description="The observation or claim being made")
    evidence: str = Field(
        description="Direct quote or factual reference from the candidate's documents"
    )
    severity: str = Field(
        default="medium",
        description="For concerns: low | medium | high. For strengths: leave as 'positive'",
    )


class AgentOpinionSchema(BaseModel):
    """Structured output that every agent must produce."""
    agent: str = Field(description="Agent name, e.g. 'Technical Agent'")
    overall_assessment: str = Field(
        description="Strong Hire | Hire | Proceed to Interview | Hold | Reject"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence level between 0.0 and 1.0"
    )
    score: int = Field(ge=1, le=10, description="Overall score 1–10")
    summary: str = Field(description="2–3 sentence summary of this agent's perspective")
    strengths: list[EvidencedPoint] = Field(
        default_factory=list,
        description="What speaks in favour of the candidate (with evidence)",
    )
    concerns: list[EvidencedPoint] = Field(
        default_factory=list,
        description="Concerns or red flags (with evidence and severity)",
    )
    recommendation: str = Field(
        description="This agent's recommendation with a brief justification"
    )
    questions_for_interview: list[str] = Field(
        default_factory=list,
        description="Suggested questions to probe weaknesses or verify claims",
    )

    @field_validator("confidence")
    @classmethod
    def round_confidence(cls, v: float) -> float:
        return round(v, 2)
