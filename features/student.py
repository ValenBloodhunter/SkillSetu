"""
SkillSetu - Student Experience

Handles:
- Student profile creation
- Dynamic role-based skill assessment
- Skill-level calculation
- Structured skill state for roadmap generation

The assessment changes according to:
1. Target role
2. Skills already entered by the student
"""

from typing import Dict, List, Any


# ============================================================
# STUDENT PROFILE
# ============================================================

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


# ============================================================
# ROLE SKILL LIBRARY
# ============================================================

ROLE_SKILLS = {
    "data analyst": [
        "python",
        "excel",
        "sql",
        "statistics",
        "power bi",
    ],

    "data scientist": [
        "python",
        "sql",
        "statistics",
        "machine learning",
        "pandas",
    ],

    "software developer": [
        "python",
        "data structures",
        "git",
        "sql",
        "apis",
    ],

    "software engineer": [
        "python",
        "data structures",
        "git",
        "sql",
        "apis",
    ],

    "web developer": [
        "html",
        "css",
        "javascript",
        "git",
        "react",
    ],

    "frontend developer": [
        "html",
        "css",
        "javascript",
        "react",
        "git",
    ],

    "backend developer": [
        "python",
        "sql",
        "apis",
        "git",
        "databases",
    ],

    "full stack developer": [
        "html",
        "css",
        "javascript",
        "sql",
        "git",
    ],

    "machine learning engineer": [
        "python",
        "machine learning",
        "statistics",
        "pandas",
        "sql",
    ],

    "business analyst": [
        "excel",
        "sql",
        "data analysis",
        "communication",
        "power bi",
    ],

    "cyber security analyst": [
        "networking",
        "linux",
        "cyber security",
        "python",
        "security analysis",
    ],

    "cybersecurity analyst": [
        "networking",
        "linux",
        "cyber security",
        "python",
        "security analysis",
    ],

    "cloud engineer": [
        "linux",
        "networking",
        "cloud",
        "docker",
        "git",
    ],

    "devops engineer": [
        "linux",
        "git",
        "docker",
        "cloud",
        "ci/cd",
    ],

    "database administrator": [
        "sql",
        "databases",
        "database design",
        "linux",
        "backup and recovery",
    ],
}


# ============================================================
# QUESTION TEMPLATES
# ============================================================

QUESTION_TEMPLATES = {
    "python":
        "How comfortable are you writing Python programs?",

    "excel":
        "How comfortable are you using Excel for data analysis?",

    "sql":
        "How comfortable are you writing SQL queries?",

    "statistics":
        "How comfortable are you with statistics and data interpretation?",

    "power bi":
        "How comfortable are you creating dashboards in Power BI?",

    "machine learning":
        "How comfortable are you building basic machine learning models?",

    "pandas":
        "How comfortable are you using Pandas to clean and analyze data?",

    "data structures":
        "How comfortable are you with data structures and algorithms?",

    "git":
        "How comfortable are you using Git for version control?",

    "apis":
        "How comfortable are you working with APIs?",

    "html":
        "How comfortable are you building web pages with HTML?",

    "css":
        "How comfortable are you styling responsive pages with CSS?",

    "javascript":
        "How comfortable are you programming with JavaScript?",

    "react":
        "How comfortable are you building interfaces with React?",

    "databases":
        "How comfortable are you working with databases?",

    "data analysis":
        "How comfortable are you analyzing and interpreting data?",

    "communication":
        "How comfortable are you explaining technical findings clearly?",

    "networking":
        "How comfortable are you with computer networking concepts?",

    "linux":
        "How comfortable are you using Linux and terminal commands?",

    "cyber security":
        "How comfortable are you with cybersecurity fundamentals?",

    "security analysis":
        "How comfortable are you identifying and analyzing security risks?",

    "cloud":
        "How comfortable are you working with cloud platforms?",

    "docker":
        "How comfortable are you using Docker containers?",

    "ci/cd":
        "How comfortable are you with CI/CD pipelines?",

    "database design":
        "How comfortable are you designing relational databases?",

    "backup and recovery":
        "How comfortable are you with database backup and recovery?",
}


# ============================================================
# HELPERS
# ============================================================

def _normalize(value):
    return " ".join(
        str(value or "")
        .lower()
        .strip()
        .split()
    )


def _safe_id(skill):
    """
    Create a Streamlit-safe assessment ID.
    """

    value = _normalize(skill)

    value = (
        value
        .replace("/", "_")
        .replace(" ", "_")
        .replace("-", "_")
    )

    return value


def _find_role_skills(target_role):
    """
    Find the closest supported role.

    Exact role matches are preferred.
    Then simple contained-name matches are attempted.
    """

    target = _normalize(
        target_role
    )

    if not target:
        return []

    if target in ROLE_SKILLS:
        return list(
            ROLE_SKILLS[target]
        )

    for role, skills in ROLE_SKILLS.items():
        if (
            role in target
            or target in role
        ):
            return list(
                skills
            )

    return []


def _question_for_skill(skill):
    """
    Generate a question for any skill.

    Known skills get a more specific question.
    Unknown user-entered skills still work dynamically.
    """

    normalized = _normalize(
        skill
    )

    if normalized in QUESTION_TEMPLATES:
        return QUESTION_TEMPLATES[
            normalized
        ]

    display_name = normalized.title()

    return (
        f"How comfortable are you using "
        f"{display_name}?"
    )


# ============================================================
# DYNAMIC SKILL ASSESSMENT
# ============================================================

def get_skill_assessment_questions(
    profile=None,
) -> List[Dict[str, str]]:
    """
    Build assessment questions dynamically.

    Priority:
    1. Skills required by target role
    2. Skills already entered by student

    Maximum: 7 questions.

    This keeps the hackathon assessment short while
    making it role-specific.
    """

    if not profile:
        fallback_skills = [
            "python",
            "excel",
            "sql",
            "communication",
        ]

        return [
            {
                "id": _safe_id(skill),
                "skill": skill,
                "question": _question_for_skill(
                    skill
                ),
            }
            for skill in fallback_skills
        ]

    if isinstance(profile, dict):
        target_role = profile.get(
            "target_role",
            "",
        )

        current_skills = profile.get(
            "skills",
            [],
        )

    else:
        target_role = getattr(
            profile,
            "target_role",
            "",
        )

        current_skills = getattr(
            profile,
            "skills",
            [],
        )

    role_skills = _find_role_skills(
        target_role
    )

    selected_skills = []

    # Target-role skills first.
    for skill in role_skills:
        normalized = _normalize(
            skill
        )

        if (
            normalized
            and normalized
            not in selected_skills
        ):
            selected_skills.append(
                normalized
            )

    # Then include skills the student
    # entered in their profile.
    for skill in current_skills or []:
        normalized = _normalize(
            skill
        )

        if (
            normalized
            and normalized
            not in selected_skills
        ):
            selected_skills.append(
                normalized
            )

    # Unknown role + no skills.
    if not selected_skills:
        selected_skills = [
            "communication",
            "problem solving",
            "digital skills",
        ]

    # Keep assessment short.
    selected_skills = (
        selected_skills[:7]
    )

    questions = []

    for skill in selected_skills:
        questions.append(
            {
                "id": _safe_id(
                    skill
                ),
                "skill": skill,
                "question": (
                    _question_for_skill(
                        skill
                    )
                ),
            }
        )

    return questions


# ============================================================
# SKILL LEVEL
# ============================================================

def calculate_skill_level(
    score: int,
) -> float:

    try:
        score = int(
            score
        )

    except (
        TypeError,
        ValueError,
    ):
        score = 1

    score = max(
        1,
        min(
            5,
            score,
        ),
    )

    return round(
        score / 5,
        2,
    )


def assess_skills(
    responses: Dict[str, int],
) -> Dict[str, float]:

    skill_state = {}

    for skill, score in responses.items():

        normalized_skill = (
            _normalize(
                skill
            )
        )

        if not normalized_skill:
            continue

        skill_state[
            normalized_skill
        ] = calculate_skill_level(
            score
        )

    return skill_state


# ============================================================
# STUDENT STATE
# ============================================================

def build_student_state(
    profile: Dict[str, Any],
    assessment_responses: Dict[str, int],
) -> Dict[str, Any]:

    skill_state = assess_skills(
        assessment_responses
    )

    return {
        "profile": profile,
        "skill_state": skill_state,
    }


# ============================================================
# ASSESSMENT SUMMARY
# ============================================================

def get_assessment_summary(
    skill_state: Dict[str, float],
) -> Dict[str, Any]:

    if not skill_state:
        return {
            "skills_assessed": 0,
            "average_level": 0.0,
            "skills": {},
        }

    average_level = (
        sum(
            skill_state.values()
        )
        / len(
            skill_state
        )
    )

    return {
        "skills_assessed": len(
            skill_state
        ),

        "average_level": round(
            average_level,
            2,
        ),

        "skills": dict(
            skill_state
        ),
    }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    profile = create_student_profile(
        name="Priya",
        location="Hyderabad",
        education="B.Tech",
        skills=[
            "Python",
            "Excel",
        ],
        target_role="Data Analyst",
    )

    questions = (
        get_skill_assessment_questions(
            profile
        )
    )

    print(
        "Dynamic assessment:"
    )

    for question in questions:
        print(
            "-",
            question["skill"],
            ":",
            question["question"],
        )