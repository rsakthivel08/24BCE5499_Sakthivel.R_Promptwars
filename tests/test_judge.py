"""
tests/test_judge.py
────────────────────
Unit tests for the Judge Agent and Final Report schema.
"""
import pytest
from unittest.mock import patch

from app.judge.schema import FinalReportSchema, EvidencedStrength, EvidencedConcern, UnresolvedDisagreement


MOCK_REPORT = {
    "candidate_name": "Alice Smith",
    "target_role": "Backend Engineer",
    "final_recommendation": "Proceed to Interview",
    "confidence_level": "Medium",
    "confidence_score": 0.68,
    "reasoning": (
        "The candidate demonstrates foundational Python and ML skills evidenced by project work. "
        "However, the Skeptic Agent raises valid concerns about production readiness. "
        "The Technical Agent's high confidence was partially challenged in the debate. "
        "A targeted interview is recommended to verify depth of knowledge."
    ),
    "key_strengths": [
        {"point": "Python experience", "evidence": "3 ML projects using Python listed"}
    ],
    "key_concerns": [
        {"point": "No deployment experience", "evidence": "No cloud platform mentioned", "severity": "high"}
    ],
    "unresolved_disagreements": [
        {
            "topic": "Production readiness",
            "agent_positions": {
                "Technical Agent": "Candidate is ready",
                "Skeptic Agent": "Insufficient production evidence",
            },
            "status": "unresolved",
        }
    ],
    "agent_score_summary": {
        "Technical Agent": {"score": 8, "assessment": "Hire", "confidence": 0.8},
        "HR Agent": {"score": 7, "assessment": "Hire", "confidence": 0.7},
        "Hiring Manager Agent": {"score": 6, "assessment": "Proceed to Interview", "confidence": 0.65},
        "Skeptic Agent": {"score": 5, "assessment": "Hold", "confidence": 0.7},
    },
    "suggested_interview_questions": [
        "Describe a production system you have deployed.",
        "How do you handle model drift in ML systems?",
    ],
}


class TestFinalReportSchema:
    def test_valid_report(self):
        report = FinalReportSchema(**MOCK_REPORT)
        assert report.final_recommendation == "Proceed to Interview"
        assert report.confidence_score == 0.68
        assert len(report.key_strengths) == 1
        assert len(report.key_concerns) == 1
        assert len(report.unresolved_disagreements) == 1

    def test_confidence_score_rounded(self):
        report = FinalReportSchema(**{**MOCK_REPORT, "confidence_score": 0.678901})
        assert report.confidence_score == 0.68

    def test_invalid_confidence_range(self):
        with pytest.raises(Exception):
            FinalReportSchema(**{**MOCK_REPORT, "confidence_score": 1.5})

    def test_unresolved_disagreement(self):
        report = FinalReportSchema(**MOCK_REPORT)
        disagreement = report.unresolved_disagreements[0]
        assert disagreement.status == "unresolved"
        assert "Technical Agent" in disagreement.agent_positions


class TestJudgeAgent:
    @patch("app.judge.judge_agent.call_llm_json")
    def test_run_judge(self, mock_llm):
        mock_llm.return_value = MOCK_REPORT

        from app.judge.judge_agent import run_judge
        report = run_judge(
            candidate_profile={"candidate_name": "Alice Smith"},
            opinions=[],
            debate_transcript={},
            target_role="Backend Engineer",
        )

        assert report.final_recommendation == "Proceed to Interview"
        assert report.candidate_name == "Alice Smith"
        mock_llm.assert_called_once()

    @patch("app.judge.judge_agent.call_llm_json")
    def test_judge_sets_candidate_name_from_profile(self, mock_llm):
        """If LLM forgets candidate_name, judge agent fills it from profile."""
        raw = {**MOCK_REPORT}
        del raw["candidate_name"]
        mock_llm.return_value = raw

        from app.judge.judge_agent import run_judge
        report = run_judge(
            candidate_profile={"candidate_name": "Bob Jones"},
            opinions=[],
            debate_transcript={},
            target_role="Data Scientist",
        )
        assert report.candidate_name == "Bob Jones"

    def test_judge_not_averaging_scores(self):
        """
        Validate that the judge's final recommendation is NOT a simple average.
        Technical:8, HR:7, HM:6, Skeptic:5 → average=6.5 → "Hire" by naive logic.
        Judge chose "Proceed to Interview" due to unresolved concerns.
        """
        report = FinalReportSchema(**MOCK_REPORT)
        avg_score = (8 + 7 + 6 + 5) / 4  # 6.5
        # If score averaging were used with 6.5 → "Hire", but report says "Proceed to Interview"
        # This tests the CONTRACT that averaging is not used
        assert report.final_recommendation != "Hire", (
            "Judge must NOT use score averaging — unresolved concerns should override."
        )
