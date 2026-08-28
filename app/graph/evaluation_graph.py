"""
app/graph/evaluation_graph.py
──────────────────────────────
LangGraph state graph orchestrating the full pipeline:

  upload_files
       │
       ▼
  build_profile          (LLM: profile extraction)
       │
       ▼
  run_agents_parallel    (4 parallel LLM calls — each agent is independent)
       │
       ▼
  run_debate             (2-round structured debate)
       │
       ▼
  run_judge              (final reasoning-based decision)
       │
       ▼
  save_results           (persist to DB)
"""
from __future__ import annotations

import asyncio
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents import HiringManagerAgent, HRAgent, SkepticAgent, TechnicalAgent
from app.debate.debate_manager import run_debate
from app.judge.judge_agent import run_judge
from app.profile_builder.builder import build_candidate_profile
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


# ─── State definition ─────────────────────────────────────────────────────────

class EvaluationState(TypedDict, total=False):
    evaluation_id: str
    target_role: str
    resume_text: str
    transcript_text: str

    # Outputs
    candidate_profile: dict[str, Any]
    opinions: list[dict[str, Any]]
    debate_transcript: dict[str, Any]
    final_report: dict[str, Any]

    # Status
    error: str | None
    status: str


# ─── Node functions ───────────────────────────────────────────────────────────

def node_build_profile(state: EvaluationState) -> EvaluationState:
    """Extract structured Candidate Profile from raw text."""
    logger.info("node_build_profile", evaluation_id=state.get("evaluation_id"))
    try:
        profile = build_candidate_profile(
            resume_text=state.get("resume_text", ""),
            transcript_text=state.get("transcript_text", ""),
            target_role=state.get("target_role", ""),
        )
        return {**state, "candidate_profile": profile.model_dump(), "status": "profile_built"}
    except Exception as exc:
        logger.error("node_build_profile_error", error=str(exc))
        return {**state, "error": str(exc), "status": "error"}


def _run_single_agent(agent_cls, profile: dict, role: str) -> dict[str, Any]:
    """Instantiate and run one agent."""
    agent = agent_cls()
    opinion = agent.evaluate(profile, role)
    return opinion.model_dump()


def node_run_agents(state: EvaluationState) -> EvaluationState:
    """
    Run all 4 agents in parallel using asyncio.
    CRITICAL: Each agent receives only the candidate profile — no other agent's output.
    """
    logger.info("node_run_agents", evaluation_id=state.get("evaluation_id"))
    if state.get("error"):
        return state

    profile = state["candidate_profile"]
    role = state.get("target_role", "Software Engineer")

    agent_classes = [TechnicalAgent, HRAgent, HiringManagerAgent, SkepticAgent]

    async def _run_all_parallel():
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(None, _run_single_agent, cls, profile, role)
            for cls in agent_classes
        ]
        return await asyncio.gather(*tasks)

    try:
        # Run parallel agent evaluations
        loop = asyncio.new_event_loop()
        results = loop.run_until_complete(_run_all_parallel())
        loop.close()
        opinions = list(results)
        logger.info("node_run_agents_complete", count=len(opinions))
        return {**state, "opinions": opinions, "status": "agents_complete"}
    except Exception as exc:
        logger.error("node_run_agents_error", error=str(exc))
        return {**state, "error": str(exc), "status": "error"}


def node_run_debate(state: EvaluationState) -> EvaluationState:
    """Run the 2-round structured debate between agents."""
    logger.info("node_run_debate", evaluation_id=state.get("evaluation_id"))
    if state.get("error"):
        return state

    try:
        transcript = run_debate(state["opinions"])
        return {
            **state,
            "debate_transcript": transcript.model_dump(),
            "status": "debate_complete",
        }
    except Exception as exc:
        logger.error("node_run_debate_error", error=str(exc))
        return {**state, "error": str(exc), "status": "error"}


def node_run_judge(state: EvaluationState) -> EvaluationState:
    """Run the Judge Agent to produce the final recommendation."""
    logger.info("node_run_judge", evaluation_id=state.get("evaluation_id"))
    if state.get("error"):
        return state

    try:
        report = run_judge(
            candidate_profile=state["candidate_profile"],
            opinions=state["opinions"],
            debate_transcript=state["debate_transcript"],
            target_role=state.get("target_role", ""),
        )
        return {
            **state,
            "final_report": report.model_dump(),
            "status": "complete",
        }
    except Exception as exc:
        logger.error("node_run_judge_error", error=str(exc))
        return {**state, "error": str(exc), "status": "error"}


def _should_continue(state: EvaluationState) -> str:
    if state.get("error"):
        return END
    return "continue"


# ─── Graph construction ────────────────────────────────────────────────────────

def build_evaluation_graph() -> StateGraph:
    graph = StateGraph(EvaluationState)

    graph.add_node("build_profile", node_build_profile)
    graph.add_node("run_agents", node_run_agents)
    graph.add_node("run_debate", node_run_debate)
    graph.add_node("run_judge", node_run_judge)

    graph.set_entry_point("build_profile")

    graph.add_conditional_edges(
        "build_profile",
        _should_continue,
        {"continue": "run_agents", END: END},
    )
    graph.add_conditional_edges(
        "run_agents",
        _should_continue,
        {"continue": "run_debate", END: END},
    )
    graph.add_conditional_edges(
        "run_debate",
        _should_continue,
        {"continue": "run_judge", END: END},
    )
    graph.add_edge("run_judge", END)

    return graph.compile()


# Singleton compiled graph
evaluation_graph = build_evaluation_graph()


def run_evaluation_pipeline(
    evaluation_id: str,
    resume_text: str,
    transcript_text: str,
    target_role: str,
) -> EvaluationState:
    """
    Execute the full pipeline synchronously.

    Returns the final state dict containing:
    - candidate_profile
    - opinions (list of 4)
    - debate_transcript
    - final_report
    - status
    """
    initial_state: EvaluationState = {
        "evaluation_id": evaluation_id,
        "target_role": target_role,
        "resume_text": resume_text,
        "transcript_text": transcript_text,
        "status": "starting",
        "error": None,
    }
    result = evaluation_graph.invoke(initial_state)
    return result
