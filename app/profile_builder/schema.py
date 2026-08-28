"""
app/profile_builder/schema.py
──────────────────────────────
Pydantic v2 models for the structured Candidate Profile.
This is the shared source of truth consumed by all 4 agents.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Education(BaseModel):
    degree: str = Field(default="", description="e.g. B.Tech Computer Science")
    institution: str = Field(default="", description="College / University name")
    cgpa: str = Field(default="", description="CGPA, GPA, percentage, or grade")
    year_of_graduation: str = Field(default="", description="Year or expected year")
    additional_info: str = Field(default="", description="Honours, minors, specialisations")


class Experience(BaseModel):
    role: str = Field(default="")
    company: str = Field(default="")
    duration: str = Field(default="", description="e.g. '3 months', 'Jan 2023 – Jun 2023'")
    type: str = Field(default="", description="Internship | Full-time | Part-time | Contract")
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str = Field(default="")
    description: str = Field(default="")
    technologies: list[str] = Field(default_factory=list)
    outcome: str = Field(default="", description="Key result or impact")
    url: str = Field(default="", description="GitHub / live link if mentioned")


class Claim(BaseModel):
    claim: str = Field(description="Statement made by the candidate")
    evidence: str = Field(
        description="Direct quote or reference from resume/transcript that supports or contradicts the claim"
    )
    evidence_strength: str = Field(
        default="weak",
        description="strong | moderate | weak | unverified",
    )


class CandidateProfile(BaseModel):
    candidate_name: str = Field(default="Unknown")
    email: str = Field(default="")
    phone: str = Field(default="")
    linkedin: str = Field(default="")
    github: str = Field(default="")

    education: Education = Field(default_factory=Education)
    skills: list[str] = Field(default_factory=list, description="All technical skills listed")
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)

    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    extracurriculars: list[str] = Field(default_factory=list)

    candidate_claims: list[Claim] = Field(
        default_factory=list,
        description="Key claims the candidate makes about themselves",
    )

    raw_resume_snippet: str = Field(
        default="", description="First 500 chars of resume for quick reference"
    )
    raw_transcript_snippet: str = Field(
        default="", description="First 500 chars of transcript for quick reference"
    )

    def model_dump_for_agent(self) -> dict[str, Any]:
        """Serialise to a dict suitable for passing to LLM prompts."""
        return self.model_dump(exclude={"raw_resume_snippet", "raw_transcript_snippet"})
