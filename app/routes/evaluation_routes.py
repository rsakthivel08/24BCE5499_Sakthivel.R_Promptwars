"""
app/routes/evaluation_routes.py
────────────────────────────────
Triggers the full evaluation pipeline and provides status/result endpoints.
The pipeline runs in a background thread to avoid blocking the event loop.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import (
    get_evaluation,
    get_final_report,
    save_agent_opinion,
    save_debate_turn,
    save_final_report,
    update_evaluation,
)
from app.db.session import get_db, get_session_factory
from app.graph.evaluation_graph import run_evaluation_pipeline
from app.utils.logging_config import get_logger

router = APIRouter(prefix="/api", tags=["evaluation"])
logger = get_logger(__name__)
_executor = ThreadPoolExecutor(max_workers=2)


async def _persist_results(evaluation_id: str, result: dict) -> None:
    """Save all pipeline results to the database."""
    factory = get_session_factory()
    async with factory() as db:
        try:
            # Save agent opinions
            for opinion in result.get("opinions", []):
                await save_agent_opinion(db, evaluation_id, opinion["agent"], opinion)

            # Save debate turns
            if debate := result.get("debate_transcript"):
                for round_data in debate.get("rounds", []):
                    for turn_idx, turn in enumerate(round_data.get("turns", [])):
                        await save_debate_turn(
                            db=db,
                            evaluation_id=evaluation_id,
                            round_number=round_data["round_number"],
                            turn_number=turn_idx + 1,
                            speaker=turn.get("speaker", ""),
                            message=turn.get("message", ""),
                            addressing=turn.get("addressing", ""),
                            stance=turn.get("stance", ""),
                            turn_data=turn,
                        )

            # Save final report
            if report := result.get("final_report"):
                await save_final_report(db, evaluation_id, report)

            # Update status
            status = result.get("status", "complete")
            error = result.get("error")
            await update_evaluation(
                db,
                evaluation_id,
                candidate_profile=result.get("candidate_profile"),
                candidate_name=(result.get("candidate_profile") or {}).get("candidate_name", ""),
                status="error" if error else status,
                error_message=error,
            )
            await db.commit()
            logger.info("results_persisted", evaluation_id=evaluation_id, status=status)
        except Exception as exc:
            await db.rollback()
            logger.error("persist_results_failed", error=str(exc))
            await update_evaluation(db, evaluation_id, status="error", error_message=str(exc))
            await db.commit()


def _run_pipeline_sync(evaluation_id: str, resume_text: str, transcript_text: str, target_role: str) -> dict:
    """Blocking pipeline call — runs in thread pool."""
    return run_evaluation_pipeline(evaluation_id, resume_text, transcript_text, target_role)


async def _background_evaluate(evaluation_id: str, resume_text: str, transcript_text: str, target_role: str):
    """Background task: run pipeline then persist results."""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            _executor,
            _run_pipeline_sync,
            evaluation_id,
            resume_text,
            transcript_text,
            target_role,
        )
    except Exception as exc:
        logger.error("pipeline_failed", evaluation_id=evaluation_id, error=str(exc))
        result = {"status": "error", "error": str(exc)}

    await _persist_results(evaluation_id, result)


@router.post("/evaluate/{evaluation_id}", summary="Start the evaluation pipeline")
async def start_evaluation(
    evaluation_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger the full pipeline for an uploaded evaluation."""
    ev = await get_evaluation(db, evaluation_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    if ev.status == "processing":
        raise HTTPException(status_code=409, detail="Evaluation already in progress")
    if ev.status == "complete":
        return {"evaluation_id": evaluation_id, "status": "complete", "message": "Already complete"}

    await update_evaluation(db, evaluation_id, status="processing")

    background_tasks.add_task(
        _background_evaluate,
        evaluation_id,
        ev.resume_text or "",
        ev.transcript_text or "",
        ev.target_role or "Software Engineer",
    )

    return {
        "evaluation_id": evaluation_id,
        "status": "processing",
        "message": "Evaluation pipeline started. Poll /api/status/{evaluation_id} for updates.",
    }


@router.get("/status/{evaluation_id}", summary="Poll evaluation status")
async def get_status(evaluation_id: str, db: AsyncSession = Depends(get_db)):
    """Returns current status of the evaluation pipeline."""
    ev = await get_evaluation(db, evaluation_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return {
        "evaluation_id": evaluation_id,
        "status": ev.status,
        "candidate_name": ev.candidate_name,
        "error": ev.error_message,
    }


@router.get("/results/{evaluation_id}", summary="Get full evaluation results")
async def get_results(evaluation_id: str, db: AsyncSession = Depends(get_db)):
    """Returns the full evaluation results including profile, opinions, debate, and report."""
    ev = await get_evaluation(db, evaluation_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    if ev.status == "processing":
        raise HTTPException(status_code=202, detail="Evaluation still in progress")
    if ev.status == "error":
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {ev.error_message}")

    opinions = [op.opinion_data for op in ev.opinions]
    debate_turns = [
        dt.turn_data for dt in sorted(ev.debate_turns, key=lambda x: (x.round_number, x.turn_number))
    ]
    report = ev.final_report.report_data if ev.final_report else None

    return {
        "evaluation_id": evaluation_id,
        "status": ev.status,
        "candidate_profile": ev.candidate_profile,
        "opinions": opinions,
        "debate_turns": debate_turns,
        "final_report": report,
    }


@router.get("/report/{evaluation_id}", summary="Get final report only")
async def get_report(evaluation_id: str, db: AsyncSession = Depends(get_db)):
    """Returns only the final hiring report."""
    report = await get_final_report(db, evaluation_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or evaluation incomplete")
    return report.report_data
