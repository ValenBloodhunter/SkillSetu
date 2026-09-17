"""
Livelihood / Rural Worker experience for SkillSetu.

IMPORTANT:
Both Student and Livelihood experiences use the SAME
core.matching_engine.matching_engine() function.
"""

from dataclasses import dataclass, field
from typing import List

from core.matching_engine import matching_engine
from data.jobs import fetch_jobs


@dataclass
class LivelihoodProfile:
    name: str
    location: str
    skills: List[str] = field(default_factory=list)

    education: str = ""
    occupation: str = ""
    target_role: str = ""

    experience: str = "fresher"
    work_preference: str = "local"
    language: str = "Telugu"


def create_livelihood_profile(
    name,
    location,
    skills,
    education="",
    occupation="",
    target_role="",
    experience="fresher",
    work_preference="local",
    language="Telugu",
):
    """
    Create the normalized livelihood profile used by
    the shared SkillSetu engine.
    """

    clean_skills = [
        str(skill).strip()
        for skill in (skills or [])
        if str(skill).strip()
    ]

    return LivelihoodProfile(
        name=name.strip(),
        location=location.strip(),
        skills=clean_skills,
        education=education.strip(),
        occupation=occupation.strip(),
        target_role=target_role.strip(),
        experience=experience,
        work_preference=work_preference,
        language=language,
    )


def get_livelihood_opportunities(profile, limit=5):
    """
    Fetch live opportunities and rank them using
    the SAME matching engine as the student experience.
    """

    jobs = fetch_jobs(profile)

    if not jobs:
        return []

    ranked_jobs = matching_engine(
        profile,
        jobs,
    )

    return ranked_jobs[:limit]


def get_livelihood_summary(profile):
    """
    Small deterministic summary for the UI.

    This does not require Gemini, so the MVP still
    works if the LLM API is unavailable.
    """

    skills = ", ".join(profile.skills)

    if not skills:
        skills = "No skills entered"

    return {
        "name": profile.name,
        "location": profile.location,
        "education": profile.education or "Not specified",
        "occupation": profile.occupation or "Not specified",
        "target_role": profile.target_role or "Open to opportunities",
        "skills": skills,
        "work_preference": profile.work_preference,
        "language": profile.language,
    }