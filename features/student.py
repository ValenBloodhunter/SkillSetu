"""
SkillSetu - Student Experience

Handles:
- Student profile collection/normalization
- Simple skill assessment
- Structured skill state for the roadmap engine

This module intentionally does not implement matching or roadmap logic.
"""

from typing import Dict, List, Any


# ---------------------------------------------------------------------------
# Student Profile
# ---------------------------------------------------------------------------

def create_student_profile(
    name: str,
    location: str,
    education: str,
    skills: List[str],
    target_role: str,
    experience: str = "Fresher",
    work_preference: str = "Any",
    language: str = "English",
) -> Dict[str, Any]:
    """
    Create a normalized student profile.

    Returns a dictionary compatible with the shared Profile structure.
    """

    normalized_skills = sorted(
        {
            str(skill).strip().lower()
            for skill in skills
            if str(skill).strip()
        }
    )

    return {
        "persona": "student",
        "name": str(name).strip(),
        "location": str(location).strip(),
        "language": str(language).strip() or "English",
        "education": str(education).strip(),
        "skills": normalized_skills,
        "target_role": str(target_role).strip(),
        "experience": str(experience).strip() or "Fresher",
        "work_preference": str(work_preference).strip() or "Any",
    }


# ---------------------------------------------------------------------------
# Skill Assessment
# ---------------------------------------------------------------------------

ASSESSMENT_QUESTIONS = [
    {
        "id": "python",
        "skill": "python",
        "question": "How comfortable are you writing Python programs?",
    },
    {
        "id": "excel",
        "skill": "excel",
        "question": "How comfortable are you using Excel for data analysis?",
    },
    {
        "id": "sql",
        "skill": "sql",
        "question": "How comfortable are you writing SQL queries?",
    },
    {
        "id": "statistics",
        "skill": "statistics",
        "question": "How comfortable are you with basic statistics?",
    },
]


def get_skill_assessment_questions() -> List[Dict[str, str]]:
    """Return the short skill-assessment question set."""

    return [question.copy() for question in ASSESSMENT_QUESTIONS]


def calculate_skill_level(score: int) -> float:
    """
    Convert a simple 1-5 self-assessment score into a 0-1 skill value.

    1 = beginner
    5 = advanced
    """

    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 1

    score = max(1, min(5, score))

    return round(score / 5, 2)


def assess_skills(responses: Dict[str, int]) -> Dict[str, float]:
    """
    Convert assessment responses into structured skill state.

    Example:
        {
            "python": 4,
            "excel": 3
        }

    becomes:

        {
            "python": 0.8,
            "excel": 0.6
        }
    """

    skill_state = {}

    for skill, score in responses.items():
        normalized_skill = str(skill).strip().lower()

        if not normalized_skill:
            continue

        skill_state[normalized_skill] = calculate_skill_level(score)

    return skill_state


# ---------------------------------------------------------------------------
# Student Experience Helpers
# ---------------------------------------------------------------------------

def build_student_state(
    profile: Dict[str, Any],
    assessment_responses: Dict[str, int],
) -> Dict[str, Any]:
    """
    Combine the student profile and assessment into one structured state.
    """

    skill_state = assess_skills(assessment_responses)

    return {
        "profile": profile,
        "skill_state": skill_state,
    }


def get_assessment_summary(skill_state: Dict[str, float]) -> Dict[str, Any]:
    """Return a simple summary suitable for UI display."""

    if not skill_state:
        return {
            "skills_assessed": 0,
            "average_level": 0.0,
            "skills": {},
        }

    average_level = sum(skill_state.values()) / len(skill_state)

    return {
        "skills_assessed": len(skill_state),
        "average_level": round(average_level, 2),
        "skills": dict(skill_state),
    }


# ---------------------------------------------------------------------------
# Local Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    profile = create_student_profile(
        name="Test Student",
        location="Hyderabad",
        education="B.Tech",
        skills=["Python", "Excel"],
        target_role="Data Analyst",
    )

    responses = {
        "python": 4,
        "excel": 3,
        "sql": 2,
        "statistics": 2,
    }

    state = build_student_state(profile, responses)

    print("Student module test")
    print("-------------------")
    print("Profile:", profile)
    print("Skill state:", state["skill_state"])
    print("Summary:", get_assessment_summary(state["skill_state"]))