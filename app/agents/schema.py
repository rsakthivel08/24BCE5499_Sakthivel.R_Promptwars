from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


class EvidencedPoint(BaseModel):
    """A single strength or concern backed by quoted evidence."""
    point: str = Field(default="", description="The observation or claim being made")
    evidence: str = Field(
        default="",
        description="Direct quote or factual reference from the candidate's documents"
    )
    severity: str = Field(
        default="medium",
        description="For concerns: low | medium | high. For strengths: leave as 'positive'",
    )

    @model_validator(mode="before")
    @classmethod
    def parse_point(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"point": data, "evidence": data, "severity": "medium"}
        return data


class AgentOpinionSchema(BaseModel):
    """Structured output that every agent must produce."""
    agent: str = Field(default="", description="Agent name, e.g. 'Technical Agent'")
    overall_assessment: str = Field(
        default="Proceed to Interview",
        description="Strong Hire | Hire | Proceed to Interview | Hold | Reject"
    )
    confidence: float = Field(
        default=0.75,
        ge=0.0, le=1.0, description="Confidence level between 0.0 and 1.0"
    )
    score: int = Field(default=7, ge=1, le=10, description="Overall score 1–10")
    summary: str = Field(default="", description="2–3 sentence summary of this agent's perspective")
    strengths: list[EvidencedPoint] = Field(
        default_factory=list,
        description="What speaks in favour of the candidate (with evidence)",
    )
    concerns: list[EvidencedPoint] = Field(
        default_factory=list,
        description="Concerns or red flags (with evidence and severity)",
    )
    recommendation: str = Field(
        default="",
        description="This agent's recommendation with a brief justification"
    )
    questions_for_interview: list[str] = Field(
        default_factory=list,
        description="Suggested questions to probe weaknesses or verify claims",
    )

    @model_validator(mode="before")
    @classmethod
    def clean_agent_dict(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        
        # Ensure recommendation is populated
        if not data.get("recommendation"):
            data["recommendation"] = data.get("summary") or data.get("overall_assessment") or "Proceed to Interview"
            
        # Ensure summary is populated
        if not data.get("summary"):
            data["summary"] = data.get("recommendation") or data.get("overall_assessment") or ""

        # Normalize score
        raw_score = data.get("score")
        if raw_score is not None:
            try:
                s = int(float(raw_score))
                if s > 10:
                    s = min(max(int(s / 10), 1), 10)
                data["score"] = min(max(s, 1), 10)
            except (ValueError, TypeError):
                data["score"] = 7
        else:
            data["score"] = 7

        return data

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            if val > 10.0:
                val = val / 100.0
            elif val > 1.0:
                val = val / 10.0
            return round(min(max(val, 0.0), 1.0), 2)
        except (ValueError, TypeError):
            return 0.75


