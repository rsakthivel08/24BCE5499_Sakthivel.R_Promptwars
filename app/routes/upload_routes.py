"""
app/routes/upload_routes.py
────────────────────────────
Handles file uploads (resume + transcript) and creates evaluation records.
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.crud import create_evaluation, update_evaluation
from app.db.session import get_db
from app.extraction.document_parser import extract_text
from app.extraction.text_cleaner import clean_text
from app.utils.logging_config import get_logger

router = APIRouter(prefix="/api", tags=["upload"])
logger = get_logger(__name__)

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


def _validate_file(file: UploadFile, field_name: str) -> None:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}: unsupported file type '{suffix}'. "
                   f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )


def _save_upload(file: UploadFile, dest_dir: Path) -> Path:
    """Save an uploaded file to disk with a UUID prefix."""
    suffix = Path(file.filename or "upload").suffix.lower()
    filename = f"{uuid.uuid4().hex}{suffix}"
    dest = dest_dir / filename
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return dest


@router.post("/upload", summary="Upload resume, transcript, and optional job description to start evaluation")
async def upload_files(
    resume: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    transcript: UploadFile = File(None, description="Interview or academic transcript (optional)"),
    job_description: UploadFile = File(None, description="Job Description document (PDF, DOCX, or TXT, optional)"),
    target_role: str = Form(default="Software Engineer"),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept resume + optional transcript + optional job description document uploads.
    Extracts text, saves files, and creates an Evaluation record.
    Returns evaluation_id for polling.
    """
    settings = get_settings()

    # Validate
    _validate_file(resume, "resume")
    if transcript and transcript.filename:
        _validate_file(transcript, "transcript")
    if job_description and job_description.filename:
        _validate_file(job_description, "job_description")

    # Save files
    upload_dir = settings.upload_dir
    resume_path = _save_upload(resume, upload_dir)
    transcript_path = _save_upload(transcript, upload_dir) if (transcript and transcript.filename) else None
    jd_path = _save_upload(job_description, upload_dir) if (job_description and job_description.filename) else None

    logger.info("files_saved", resume=str(resume_path), transcript=str(transcript_path), jd=str(jd_path))

    # Extract text
    try:
        resume_text = clean_text(extract_text(resume_path))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not extract resume text: {exc}")

    transcript_text = ""
    if transcript_path:
        try:
            transcript_text = clean_text(extract_text(transcript_path))
        except Exception as exc:
            logger.warning("transcript_extraction_failed", error=str(exc))
            transcript_text = ""

    final_role_or_jd = target_role
    if jd_path:
        try:
            extracted_jd = clean_text(extract_text(jd_path))
            if extracted_jd.strip():
                final_role_or_jd = f"{target_role}\n\n[JOB DESCRIPTION DOCUMENT]:\n{extracted_jd}"
        except Exception as exc:
            logger.warning("job_description_extraction_failed", error=str(exc))

    # Create DB record
    ev = await create_evaluation(
        db,
        target_role=final_role_or_jd,
        resume_filename=resume.filename or "",
        transcript_filename=(transcript.filename if transcript else "") or "",
    )
    await update_evaluation(
        db,
        ev.id,
        resume_text=resume_text,
        transcript_text=transcript_text,
        status="pending",
    )

    logger.info("evaluation_created", evaluation_id=ev.id)
    return {
        "evaluation_id": ev.id,
        "message": "Files uploaded successfully. Use /api/evaluate/{evaluation_id} to start evaluation.",
        "resume_chars": len(resume_text),
        "transcript_chars": len(transcript_text),
        "target_role": target_role,
    }
