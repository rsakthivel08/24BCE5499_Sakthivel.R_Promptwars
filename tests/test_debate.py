"""
tests/test_debate.py
─────────────────────
Unit tests for the debate manager and schemas.
"""
import pytest
from unittest.mock import patch

from app.debate.schema import DebateTurnSchema, DebateTranscript, DebateRound


MOCK_TURN_RAW = {
    "speaker": "Skeptic Agent",
    "addressing": "Technical Agent",
    "stance": "challenge",
    "point_being_discussed": "Python experience depth",
    "message": "The Technical Agent's confidence in Python skills is overstated. "
               "While Python is listed, none of the projects demonstrate production-level usage.",
    "evidence_cited": "Resume lists Python but all projects are academic.",
    "opinion_change": "none",
}

MOCK_OPINIONS = [
    {"agent": "Technical Agent", "overall_assessment": "Hire", "score": 8, "confidence": 0.8,
     "summary": "Strong skills", "strengths": [], "concerns": [], "recommendation": "Hire"},
    {"agent": "HR Agent", "overall_assessment": "Hire", "score": 7, "confidence": 0.7,
     "summary": "Good soft skills", "strengths": [], "concerns": [], "recommendation": "Hire"},
    {"agent": "Hiring Manager Agent", "overall_assessment": "Proceed to Interview", "score": 6,
     "confidence": 0.65, "summary": "Role fit unclear", "strengths": [], "concerns": [],
     "recommendation": "Interview"},
    {"agent": "Skeptic Agent", "overall_assessment": "Hold", "score": 5, "confidence": 0.7,
     "summary": "Unsupported claims", "strengths": [], "concerns": [], "recommendation": "Hold"},
]


class TestDebateTurnSchema:
    def test_valid_turn(self):
        turn = DebateTurnSchema(**MOCK_TURN_RAW)
        assert turn.speaker == "Skeptic Agent"
        assert turn.stance == "challenge"
        assert turn.addressing == "Technical Agent"

    def test_default_addressing(self):
        turn = DebateTurnSchema(
            speaker="HR Agent",
            stance="agree",
            point_being_discussed="teamwork",
            message="I agree with the Technical Agent.",
        )
        assert turn.addressing == ""


class TestDebateTranscript:
    def test_empty_transcript(self):
        t = DebateTranscript(rounds=[])
        assert t.rounds == []
        assert t.key_agreements == []
        assert t.unresolved_issues == []


class TestDebateManager:
    @patch("app.debate.debate_manager.call_llm_json")
    def test_run_debate_produces_transcript(self, mock_llm):
        mock_llm.return_value = {
            **MOCK_TURN_RAW,
            "updated_opinions": {},
            "key_agreements": ["Python skills are present"],
            "key_disagreements": ["Production readiness"],
            "unresolved_issues": ["No deployment evidence"],
        }

        from app.debate.debate_manager import run_debate
        transcript = run_debate(MOCK_OPINIONS)

        assert len(transcript.rounds) == 2
        assert len(transcript.rounds[0].turns) == 4  # One per agent
        assert len(transcript.rounds[1].turns) == 4

    @patch("app.debate.debate_manager.call_llm_json")
    def test_debate_handles_llm_failure_gracefully(self, mock_llm):
        """Even if one LLM call fails, debate continues."""
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Simulated LLM failure")
            return {**MOCK_TURN_RAW,
                    "updated_opinions": {}, "key_agreements": [], "key_disagreements": [], "unresolved_issues": []}
        mock_llm.side_effect = side_effect

        from app.debate.debate_manager import run_debate
        transcript = run_debate(MOCK_OPINIONS)

        # Should still complete with fallback turn
        assert len(transcript.rounds) == 2
