"""
app/db/crud.py
───────────────
Async CRUD helpers for all ORM models.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AgentOpinion, DebateTurn, Evaluation, FinalReport


# ─── Evaluation ──────────────────────────────────────────────────────────────

async def create_evaluation(
    db: AsyncSession,
    target_role: str = "",
    resume_filename: str = "",
    transcript_filename: str = "",
) -> Evaluation:
    ev = Evaluation(
        id=str(uuid.uuid4()),
        target_role=target_role,
        resume_filename=resume_filename,
        transcript_filename=transcript_filename,
        status="pending",
    )
    db.add(ev)
    await db.flush()
    return ev


async def get_evaluation(db: AsyncSession, evaluation_id: str) -> Evaluation | None:
    result = await db.execute(
        select(Evaluation)
        .where(Evaluation.id == evaluation_id)
        .options(
            selectinload(Evaluation.opinions),
            selectinload(Evaluation.debate_turns),
            selectinload(Evaluation.final_report),
        )
    )
    return result.scalar_one_or_none()


async def update_evaluation(
    db: AsyncSession, evaluation_id: str, **kwargs: Any
) -> Evaluation | None:
    ev = await db.get(Evaluation, evaluation_id)
    if ev is None:
        return None
    for key, value in kwargs.items():
        setattr(ev, key, value)
    await db.flush()
    return ev


# ─── Agent Opinion ────────────────────────────────────────────────────────────

async def save_agent_opinion(
    db: AsyncSession,
    evaluation_id: str,
    agent_name: str,
    opinion_data: dict,
) -> AgentOpinion:
    op = AgentOpinion(
        evaluation_id=evaluation_id,
        agent_name=agent_name,
        overall_assessment=opinion_data.get("overall_assessment"),
        confidence=opinion_data.get("confidence"),
        score=opinion_data.get("score"),
        opinion_data=opinion_data,
    )
    db.add(op)
    await db.flush()
    return op


async def get_opinions_for_evaluation(
    db: AsyncSession, evaluation_id: str
) -> list[AgentOpinion]:
    result = await db.execute(
        select(AgentOpinion).where(AgentOpinion.evaluation_id == evaluation_id)
    )
    return list(result.scalars().all())


# ─── Debate Turn ──────────────────────────────────────────────────────────────

async def save_debate_turn(
    db: AsyncSession,
    evaluation_id: str,
    round_number: int,
    turn_number: int,
    speaker: str,
    message: str,
    addressing: str | None = None,
    stance: str | None = None,
    audio_path: str | None = None,
    turn_data: dict | None = None,
) -> DebateTurn:
    turn = DebateTurn(
        evaluation_id=evaluation_id,
        round_number=round_number,
        turn_number=turn_number,
        speaker=speaker,
        addressing=addressing,
        stance=stance,
        message=message,
        audio_path=audio_path,
        turn_data=turn_data or {},
    )
    db.add(turn)
    await db.flush()
    return turn


async def get_debate_turns(
    db: AsyncSession, evaluation_id: str
) -> list[DebateTurn]:
    result = await db.execute(
        select(DebateTurn)
        .where(DebateTurn.evaluation_id == evaluation_id)
        .order_by(DebateTurn.round_number, DebateTurn.turn_number)
    )
    return list(result.scalars().all())


# ─── Final Report ─────────────────────────────────────────────────────────────

async def save_final_report(
    db: AsyncSession,
    evaluation_id: str,
    report_data: dict,
) -> FinalReport:
    report = FinalReport(
        evaluation_id=evaluation_id,
        recommendation=report_data.get("final_recommendation"),
        confidence_level=report_data.get("confidence_level"),
        confidence_score=report_data.get("confidence_score"),
        report_data=report_data,
    )
    db.add(report)
    await db.flush()
    return report


async def get_final_report(
    db: AsyncSession, evaluation_id: str
) -> FinalReport | None:
    result = await db.execute(
        select(FinalReport).where(FinalReport.evaluation_id == evaluation_id)
    )
    return result.scalar_one_or_none()
