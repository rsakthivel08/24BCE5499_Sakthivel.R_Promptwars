"""
tests/test_profile_builder.py
──────────────────────────────
Unit tests for the Candidate Profile Builder.
"""
import pytest
from unittest.mock import patch

from app.profile_builder.schema import CandidateProfile, Education, Claim


class TestCandidateProfileSchema:
    def test_default_profile(self):
        profile = CandidateProfile()
        assert profile.candidate_name == "Unknown"
        assert profile.skills == []
        assert profile.experience == []
        assert profile.projects == []
        assert profile.candidate_claims == []

    def test_profile_with_education(self):
        profile = CandidateProfile(
            candidate_name="John Doe",
            education=Education(
                degree="B.Tech Computer Science",
                institution="XYZ University",
                cgpa="8.5",
            ),
        )
        assert profile.candidate_name == "John Doe"
        assert profile.education.degree == "B.Tech Computer Science"
        assert profile.education.cgpa == "8.5"

    def test_profile_model_dump_for_agent(self):
        profile = CandidateProfile(
            candidate_name="Jane Doe",
            raw_resume_snippet="some text",
            raw_transcript_snippet="transcript text",
        )
        dumped = profile.model_dump_for_agent()
        # Should exclude raw snippets
        assert "raw_resume_snippet" not in dumped
        assert "raw_transcript_snippet" not in dumped
        assert dumped["candidate_name"] == "Jane Doe"

    def test_claim_evidence_strength_default(self):
        claim = Claim(claim="Built a chatbot", evidence="Resume mentions chatbot project")
        assert claim.evidence_strength == "weak"


class TestProfileBuilder:
    @patch("app.profile_builder.builder.call_llm_json")
    def test_build_candidate_profile(self, mock_llm):
        mock_llm.return_value = {
            "candidate_name": "Alice Smith",
            "education": {
                "degree": "B.Sc Computer Science",
                "institution": "Test University",
                "cgpa": "9.0",
                "year_of_graduation": "2024",
                "additional_info": "",
            },
            "skills": ["Python", "SQL"],
            "programming_languages": ["Python"],
            "frameworks": ["FastAPI"],
            "tools": [],
            "platforms": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
            "extracurriculars": [],
            "candidate_claims": [
                {
                    "claim": "Expert in Python",
                    "evidence": "Python listed in skills",
                    "evidence_strength": "moderate",
                }
            ],
        }

        from app.profile_builder.builder import build_candidate_profile
        profile = build_candidate_profile(
            resume_text="Alice Smith - Python developer...",
            transcript_text="",
            target_role="Backend Engineer",
        )

        assert profile.candidate_name == "Alice Smith"
        assert "Python" in profile.skills
        assert len(profile.candidate_claims) == 1
        assert profile.candidate_claims[0].evidence_strength == "moderate"

    @patch("app.profile_builder.builder.call_llm_json")
    def test_profile_builder_handles_missing_fields(self, mock_llm):
        """LLM returns minimal JSON — should not crash."""
        mock_llm.return_value = {"candidate_name": "Bob"}

        from app.profile_builder.builder import build_candidate_profile
        profile = build_candidate_profile("Bob's resume")

        assert profile.candidate_name == "Bob"
        assert profile.skills == []
