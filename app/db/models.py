"""
app/db/models.py
─────────────────
SQLAlchemy ORM models for persisting evaluation data.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Evaluation(Base):
    """Top-level evaluation record created when files are uploaded."""

    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    candidate_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    transcript_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    candidate_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending | processing | complete | error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    opinions: Mapped[list[AgentOpinion]] = relationship(
        "AgentOpinion", back_populates="evaluation", cascade="all, delete-orphan"
    )
    debate_turns: Mapped[list[DebateTurn]] = relationship(
        "DebateTurn", back_populates="evaluation", cascade="all, delete-orphan"
    )
    final_report: Mapped[FinalReport | None] = relationship(
        "FinalReport", back_populates="evaluation", uselist=False, cascade="all, delete-orphan"
    )


class AgentOpinion(Base):
    """One agent's independent evaluation before debate."""

    __tablename__ = "agent_opinions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluations.id"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    overall_assessment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opinion_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    evaluation: Mapped[Evaluation] = relationship("Evaluation", back_populates="opinions")


class DebateTurn(Base):
    """A single turn in the structured agent debate."""

    __tablename__ = "debate_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluations.id"), nullable=False
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker: Mapped[str] = mapped_column(String(100), nullable=False)
    addressing: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stance: Mapped[str | None] = mapped_column(String(50), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    turn_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    evaluation: Mapped[Evaluation] = relationship("Evaluation", back_populates="debate_turns")


class FinalReport(Base):
    """Judge agent's final hiring recommendation."""

    __tablename__ = "final_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluations.id"), unique=True, nullable=False
    )
    recommendation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    report_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    evaluation: Mapped[Evaluation] = relationship("Evaluation", back_populates="final_report")
