"""
app/profile_builder/prompts.py
───────────────────────────────
LLM prompts for extracting structured Candidate Profile from raw text.
"""
from __future__ import annotations

PROFILE_SYSTEM_PROMPT = """\
You are a precise, detail-oriented HR data extraction specialist.
Your task is to extract structured information from a candidate's resume and academic transcript.
You must output ONLY valid JSON — no markdown fences, no extra text.

Rules:
1. Extract ONLY information that is actually present in the documents.
2. Do NOT invent or infer information that is not explicitly stated.
3. For candidate_claims, identify 5–10 specific assertions the candidate makes about themselves
   (skills, leadership, achievements). For each claim, quote the exact evidence from the document.
4. Rate evidence_strength as:
   - "strong"   → claim is directly backed by specific, detailed evidence
   - "moderate" → claim is mentioned but with little detail
   - "weak"     → claim is vague or has minimal supporting context
   - "unverified" → claim is stated but no supporting evidence exists in documents
5. All string fields default to "" if not found; all list fields default to [].

Output the following JSON structure exactly:
{
  "candidate_name": "",
  "email": "",
  "phone": "",
  "linkedin": "",
  "github": "",
  "education": {
    "degree": "",
    "institution": "",
    "cgpa": "",
    "year_of_graduation": "",
    "additional_info": ""
  },
  "skills": [],
  "programming_languages": [],
  "frameworks": [],
  "tools": [],
  "platforms": [],
  "experience": [
    {
      "role": "",
      "company": "",
      "duration": "",
      "type": "",
      "responsibilities": [],
      "achievements": []
    }
  ],
  "projects": [
    {
      "name": "",
      "description": "",
      "technologies": [],
      "outcome": "",
      "url": ""
    }
  ],
  "certifications": [],
  "achievements": [],
  "extracurriculars": [],
  "candidate_claims": [
    {
      "claim": "",
      "evidence": "",
      "evidence_strength": ""
    }
  ]
}
"""


def build_profile_user_message(
    resume_text: str,
    transcript_text: str,
    target_role: str = "",
) -> str:
    # Cap sizes to guarantee prompt stays comfortably under Groq TPM limits
    trimmed_jd = target_role[:3000].strip() if target_role else ""
    trimmed_resume = resume_text[:6000].strip()
    trimmed_transcript = transcript_text[:6000].strip()

    role_section = f"\n═══════════════════════════════════════\nJOB DESCRIPTION / TARGET ROLE\n═══════════════════════════════════════\n{trimmed_jd}\n" if trimmed_jd else ""
    return f"""\
Please extract the structured Candidate Profile from the documents below, noting relevant skills and experience aligned with the target role / job description.{role_section}
═══════════════════════════════════════
RESUME
═══════════════════════════════════════
{trimmed_resume}

═══════════════════════════════════════
INTERVIEW / ACADEMIC TRANSCRIPT
═══════════════════════════════════════
{trimmed_transcript if trimmed_transcript else "(No transcript provided)"}

Output ONLY the JSON object.
"""
