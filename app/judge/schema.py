"""
app/judge/schema.py
────────────────────
Pydantic schema for the Final Report produced by the Judge Agent.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class EvidencedStrength(BaseModel):
    point: str
    evidence: str


class EvidencedConcern(BaseModel):
    point: str
    evidence: str
    severity: str = "medium"


class UnresolvedDisagreement(BaseModel):
    topic: str
    agent_positions: dict[str, str] = Field(
        description="Agent name → their position on this topic"
    )
    status: str = Field(
        description="unresolved | partially_resolved | resolved_in_favour_of_hire | resolved_against_hire"
    )


class FinalReportSchema(BaseModel):
    """Complete final hiring recommendation from the Judge Agent."""
    candidate_name: str = ""
    target_role: str = ""

    final_recommendation: str = Field(
        description="Strong Hire | Hire | Proceed to Interview | Hold | Reject"
    )
    confidence_level: str = Field(
        description="High | Medium | Low"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Numeric confidence 0.0–1.0"
    )

    reasoning: str = Field(
        description="3–5 sentence explanation of why this recommendation was made, "
                    "explicitly referencing evidence and agent debate outcomes"
    )

    key_strengths: list[EvidencedStrength] = Field(default_factory=list)
    key_concerns: list[EvidencedConcern] = Field(default_factory=list)
    unresolved_disagreements: list[UnresolvedDisagreement] = Field(default_factory=list)

    agent_score_summary: dict[str, dict] = Field(
        default_factory=dict,
        description="Agent name → {'score': int, 'assessment': str, 'confidence': float}",
    )

    suggested_interview_questions: list[str] = Field(
        default_factory=list,
        description="Top 5 questions to verify remaining uncertainties",
    )

    @field_validator("confidence_score", mode="before")
    @classmethod
    def normalize_score(cls, v: Any) -> float:
        try:
            val = float(v)
            if val > 10.0:
                val = val / 100.0
            elif val > 1.0:
                val = val / 10.0
            return round(min(max(val, 0.0), 1.0), 2)
        except (ValueError, TypeError):
            return 0.5

