from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


class EvidencedStrength(BaseModel):
    point: str = Field(default="")
    evidence: str = Field(default="")

    @model_validator(mode="before")
    @classmethod
    def parse_strength(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"point": data, "evidence": data}
        return data


class EvidencedConcern(BaseModel):
    point: str = Field(default="")
    evidence: str = Field(default="")
    severity: str = Field(default="medium")

    @model_validator(mode="before")
    @classmethod
    def parse_concern(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"point": data, "evidence": data, "severity": "medium"}
        return data


class UnresolvedDisagreement(BaseModel):
    topic: str = Field(default="")
    agent_positions: dict[str, str] = Field(
        default_factory=dict,
        description="Agent name → their position on this topic"
    )
    status: str = Field(
        default="unresolved",
        description="unresolved | partially_resolved | resolved_in_favour_of_hire | resolved_against_hire"
    )


class FinalReportSchema(BaseModel):
    """Complete final hiring recommendation from the Judge Agent."""
    candidate_name: str = ""
    target_role: str = ""

    final_recommendation: str = Field(
        default="Proceed to Interview",
        description="Strong Hire | Hire | Proceed to Interview | Hold | Reject"
    )
    confidence_level: str = Field(
        default="Medium",
        description="High | Medium | Low"
    )
    confidence_score: float = Field(
        default=0.75,
        ge=0.0, le=1.0,
        description="Numeric confidence 0.0–1.0"
    )

    reasoning: str = Field(
        default="",
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

    @model_validator(mode="before")
    @classmethod
    def clean_report_dict(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        
        if not data.get("final_recommendation"):
            data["final_recommendation"] = data.get("recommendation") or data.get("overall_assessment") or "Proceed to Interview"
            
        if not data.get("reasoning"):
            data["reasoning"] = data.get("summary") or data.get("justification") or "Comprehensive evaluation synthesized from panel debate."
            
        if not data.get("confidence_level"):
            score = data.get("confidence_score", 0.75)
            try:
                s = float(score)
                data["confidence_level"] = "High" if s >= 0.8 else "Medium" if s >= 0.5 else "Low"
            except (ValueError, TypeError):
                data["confidence_level"] = "Medium"
                
        return data

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
            return 0.75


