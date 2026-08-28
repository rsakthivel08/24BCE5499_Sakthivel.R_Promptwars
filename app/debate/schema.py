"""
app/debate/schema.py
─────────────────────
Pydantic schemas for a structured agent debate turn and full transcript.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class DebateTurnSchema(BaseModel):
    """A single agent's contribution to the debate."""
    speaker: str = Field(description="Agent name making this statement")
    addressing: str = Field(
        default="",
        description="Which agent (or 'All') this response is directed at",
    )
    stance: str = Field(
        description="agree | disagree | partially_agree | challenge | update_opinion | new_concern"
    )
    point_being_discussed: str = Field(
        description="The specific claim or topic this turn addresses"
    )
    message: str = Field(description="The full debate statement")
    evidence_cited: str = Field(
        default="",
        description="Quote or reference from the profile that supports this argument",
    )
    opinion_change: str = Field(
        default="none",
        description="none | increased_confidence | decreased_confidence | changed_recommendation",
    )


class DebateRound(BaseModel):
    round_number: int
    turns: list[DebateTurnSchema]


class DebateTranscript(BaseModel):
    """Full structured debate output."""
    rounds: list[DebateRound]
    updated_opinions: dict[str, str] = Field(
        default_factory=dict,
        description="Agent name → updated overall_assessment after debate",
    )
    key_agreements: list[str] = Field(default_factory=list)
    key_disagreements: list[str] = Field(default_factory=list)
    unresolved_issues: list[str] = Field(default_factory=list)
