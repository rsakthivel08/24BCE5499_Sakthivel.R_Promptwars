"""
app/profile_builder/builder.py
───────────────────────────────
Calls the LLM to extract a CandidateProfile from raw resume/transcript text.
"""
from __future__ import annotations

from app.profile_builder.prompts import PROFILE_SYSTEM_PROMPT, build_profile_user_message
from app.profile_builder.schema import CandidateProfile
from app.utils.llm_client import call_llm_json
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def build_candidate_profile(
    resume_text: str,
    transcript_text: str = "",
    target_role: str = "",
) -> CandidateProfile:
    """
    Extract and validate a CandidateProfile from raw document text.

    Args:
        resume_text: Cleaned text from the uploaded resume.
        transcript_text: Cleaned text from the uploaded transcript (optional).
        target_role: The job role being evaluated for (used as hint in prompt).

    Returns:
        Validated CandidateProfile instance.
    """
    logger.info("building_candidate_profile", target_role=target_role)

    user_msg = build_profile_user_message(resume_text, transcript_text, target_role)
    raw_json = call_llm_json(
        system_prompt=PROFILE_SYSTEM_PROMPT,
        user_message=user_msg,
        temperature=0.1,  # Low temperature for extraction accuracy
        max_tokens=4096,
    )

    # Add raw snippets for quick reference (not sent to agents)
    raw_json["raw_resume_snippet"] = resume_text[:500]
    raw_json["raw_transcript_snippet"] = transcript_text[:500] if transcript_text else ""

    profile = CandidateProfile(**raw_json)
    logger.info(
        "profile_built",
        name=profile.candidate_name,
        skills=len(profile.skills),
        claims=len(profile.candidate_claims),
    )
    return profile
