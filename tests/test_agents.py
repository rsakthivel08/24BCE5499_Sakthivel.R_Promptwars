"""
tests/test_agents.py
─────────────────────
Unit tests for the 4 independent AI persona agents.
"""
import pytest
from unittest.mock import patch

from app.agents.schema import AgentOpinionSchema, EvidencedPoint


MOCK_OPINION = {
    "agent": "Technical Agent",
    "overall_assessment": "Proceed to Interview",
    "confidence": 0.75,
    "score": 7,
    "summary": "Candidate shows solid Python skills but limited production experience.",
    "strengths": [
        {
            "point": "Strong Python skills",
            "evidence": "Resume states: Developed ML models using Python and Scikit-learn.",
            "severity": "positive",
        }
    ],
    "concerns": [
        {
            "point": "No cloud deployment",
            "evidence": "No AWS/GCP/Azure mentioned in resume.",
            "severity": "medium",
        }
    ],
    "recommendation": "Proceed to interview to verify depth of ML knowledge.",
    "questions_for_interview": ["Describe a production ML deployment you have done."],
}


class TestAgentOpinionSchema:
    def test_valid_opinion(self):
        op = AgentOpinionSchema(**MOCK_OPINION)
        assert op.agent == "Technical Agent"
        assert op.score == 7
        assert op.confidence == 0.75
        assert len(op.strengths) == 1
        assert len(op.concerns) == 1

    def test_confidence_rounded(self):
        op = AgentOpinionSchema(**{**MOCK_OPINION, "confidence": 0.756789})
        assert op.confidence == 0.76

    def test_invalid_score_range(self):
        with pytest.raises(Exception):
            AgentOpinionSchema(**{**MOCK_OPINION, "score": 15})

    def test_invalid_confidence_range(self):
        with pytest.raises(Exception):
            AgentOpinionSchema(**{**MOCK_OPINION, "confidence": 1.5})


class TestTechnicalAgent:
    @patch("app.agents.base_agent.call_llm_json")
    def test_technical_agent_evaluate(self, mock_llm):
        mock_llm.return_value = MOCK_OPINION

        from app.agents.technical_agent import TechnicalAgent
        agent = TechnicalAgent()
        result = agent.evaluate(
            candidate_profile={"candidate_name": "Alice", "skills": ["Python"]},
            target_role="Backend Engineer",
        )

        assert result.agent == "Technical Agent"
        assert result.score == 7
        mock_llm.assert_called_once()

    @patch("app.agents.base_agent.call_llm_json")
    def test_hr_agent_evaluate(self, mock_llm):
        mock_llm.return_value = {**MOCK_OPINION, "agent": "HR Agent"}

        from app.agents.hr_agent import HRAgent
        agent = HRAgent()
        result = agent.evaluate({"candidate_name": "Alice"}, "Backend Engineer")

        assert result.agent == "HR Agent"

    @patch("app.agents.base_agent.call_llm_json")
    def test_hiring_manager_agent(self, mock_llm):
        mock_llm.return_value = {**MOCK_OPINION, "agent": "Hiring Manager Agent"}

        from app.agents.hiring_manager_agent import HiringManagerAgent
        agent = HiringManagerAgent()
        result = agent.evaluate({"candidate_name": "Alice"}, "Backend Engineer")

        assert result.agent == "Hiring Manager Agent"

    @patch("app.agents.base_agent.call_llm_json")
    def test_skeptic_agent(self, mock_llm):
        mock_llm.return_value = {**MOCK_OPINION, "agent": "Skeptic Agent"}

        from app.agents.skeptic_agent import SkepticAgent
        agent = SkepticAgent()
        result = agent.evaluate({"candidate_name": "Alice"}, "Backend Engineer")

        assert result.agent == "Skeptic Agent"

    def test_agents_have_distinct_system_prompts(self):
        from app.agents.technical_agent import TechnicalAgent
        from app.agents.hr_agent import HRAgent
        from app.agents.hiring_manager_agent import HiringManagerAgent
        from app.agents.skeptic_agent import SkepticAgent

        prompts = [
            TechnicalAgent().system_prompt,
            HRAgent().system_prompt,
            HiringManagerAgent().system_prompt,
            SkepticAgent().system_prompt,
        ]
        # All prompts must be different
        assert len(set(prompts)) == 4, "All 4 agents must have unique system prompts"
