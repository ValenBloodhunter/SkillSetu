"""
SkillSetu - Adaptive Roadmap Engine

Phase 4:
    roadmap_engine(profile, skill_state) -> roadmap

Deterministic skill-gap analysis for Student and Livelihood personas.
No LLM or external API is required.
"""

from typing import Any, Dict, List, Tuple


# ---------------------------------------------------------------------------
# Skill levels
# ---------------------------------------------------------------------------

SKILL_LEVELS = {
    "none": 0,
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}


# ---------------------------------------------------------------------------
# Role skill requirements
#
# Each skill has:
#   target_level = minimum desired level
#   importance   = importance of the skill for that role (0.0 - 1.0)
# ---------------------------------------------------------------------------

ROLE_REQUIREMENTS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "data analyst": {
        "Python": {"target_level": "intermediate", "importance": 0.85},
        "SQL": {"target_level": "advanced", "importance": 1.00},
        "Statistics": {"target_level": "intermediate", "importance": 0.90},
        "Excel": {"target_level": "intermediate", "importance": 0.75},
        "Power BI": {"target_level": "intermediate", "importance": 0.80},
        "Communication": {"target_level": "intermediate", "importance": 0.65},
    },

    "data scientist": {
        "Python": {"target_level": "advanced", "importance": 1.00},
        "SQL": {"target_level": "intermediate", "importance": 0.70},
        "Statistics": {"target_level": "advanced", "importance": 1.00},
        "Machine Learning": {"target_level": "intermediate", "importance": 0.95},
        "Data Analysis": {"target_level": "intermediate", "importance": 0.85},
        "Communication": {"target_level": "intermediate", "importance": 0.60},
    },

    "machine learning engineer": {
        "Python": {"target_level": "advanced", "importance": 1.00},
        "Machine Learning": {"target_level": "advanced", "importance": 1.00},
        "Statistics": {"target_level": "intermediate", "importance": 0.80},
        "SQL": {"target_level": "intermediate", "importance": 0.60},
        "Data Analysis": {"target_level": "intermediate", "importance": 0.70},
        "Problem Solving": {"target_level": "advanced", "importance": 0.85},
    },

    "software engineer": {
        "Programming": {"target_level": "advanced", "importance": 1.00},
        "Data Structures": {"target_level": "intermediate", "importance": 0.95},
        "Algorithms": {"target_level": "intermediate", "importance": 0.95},
        "Python": {"target_level": "intermediate", "importance": 0.65},
        "SQL": {"target_level": "beginner", "importance": 0.45},
        "Problem Solving": {"target_level": "advanced", "importance": 0.90},
        "Communication": {"target_level": "intermediate", "importance": 0.55},
    },

    "web developer": {
        "HTML": {"target_level": "intermediate", "importance": 0.80},
        "CSS": {"target_level": "intermediate", "importance": 0.75},
        "JavaScript": {"target_level": "intermediate", "importance": 1.00},
        "SQL": {"target_level": "beginner", "importance": 0.45},
        "Git": {"target_level": "beginner", "importance": 0.60},
        "Communication": {"target_level": "intermediate", "importance": 0.50},
    },

    "ai engineer": {
        "Python": {"target_level": "advanced", "importance": 1.00},
        "Machine Learning": {"target_level": "intermediate", "importance": 0.95},
        "Statistics": {"target_level": "intermediate", "importance": 0.80},
        "Data Analysis": {"target_level": "intermediate", "importance": 0.70},
        "Problem Solving": {"target_level": "advanced", "importance": 0.85},
        "Communication": {"target_level": "intermediate", "importance": 0.50},
    },

    "cybersecurity analyst": {
        "Networking": {"target_level": "intermediate", "importance": 0.95},
        "Linux": {"target_level": "intermediate", "importance": 0.85},
        "Python": {"target_level": "intermediate", "importance": 0.75},
        "Cybersecurity": {"target_level": "intermediate", "importance": 1.00},
        "Problem Solving": {"target_level": "advanced", "importance": 0.80},
        "Communication": {"target_level": "intermediate", "importance": 0.55},
    },

    "business analyst": {
        "Excel": {"target_level": "advanced", "importance": 0.90},
        "SQL": {"target_level": "intermediate", "importance": 0.75},
        "Power BI": {"target_level": "intermediate", "importance": 0.80},
        "Data Analysis": {"target_level": "intermediate", "importance": 0.90},
        "Communication": {"target_level": "advanced", "importance": 1.00},
        "Problem Solving": {"target_level": "intermediate", "importance": 0.85},
    },

    # Generic fallback for unknown roles
    "general": {
        "Communication": {"target_level": "intermediate", "importance": 0.75},
        "Problem Solving": {"target_level": "intermediate", "importance": 0.85},
        "Digital Literacy": {"target_level": "intermediate", "importance": 0.80},
    },
}


# ---------------------------------------------------------------------------
# Skill aliases
# ---------------------------------------------------------------------------

SKILL_ALIASES = {
    "python programming": "Python",
    "python": "Python",

    "sql": "SQL",
    "mysql": "SQL",
    "postgresql": "SQL",

    "statistics": "Statistics",
    "stats": "Statistics",

    "power bi": "Power BI",
    "powerbi": "Power BI",

    "excel": "Excel",
    "microsoft excel": "Excel",

    "machine learning": "Machine Learning",
    "ml": "Machine Learning",

    "data analysis": "Data Analysis",
    "data analytics": "Data Analysis",

    "communication": "Communication",
    "communication skills": "Communication",

    "problem solving": "Problem Solving",
    "problem-solving": "Problem Solving",

    "programming": "Programming",
    "coding": "Programming",

    "data structures": "Data Structures",
    "dsa": "Data Structures",

    "algorithms": "Algorithms",
    "algorithm": "Algorithms",

    "javascript": "JavaScript",
    "js": "JavaScript",

    "html": "HTML",
    "html5": "HTML",

    "css": "CSS",
    "css3": "CSS",

    "git": "Git",
    "github": "Git",

    "networking": "Networking",
    "computer networking": "Networking",

    "linux": "Linux",

    "cybersecurity": "Cybersecurity",
    "cyber security": "Cybersecurity",

    "digital literacy": "Digital Literacy",
}


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _normalise_text(value: Any) -> str:
    """Safely convert a value to lowercase normalized text."""
    if value is None:
        return ""

    return " ".join(str(value).strip().lower().split())


def _canonical_skill(skill: Any) -> str:
    """
    Convert a skill name into the canonical SkillSetu skill name.
    Unknown skills are returned in cleaned title form.
    """
    normalized = _normalise_text(skill)

    if not normalized:
        return ""

    if normalized in SKILL_ALIASES:
        return SKILL_ALIASES[normalized]

    return str(skill).strip()


def _skill_level(value: Any) -> int:
    """
    Convert a skill level into a numeric value.

    Unknown/missing levels safely become 0 ('none').
    """
    if isinstance(value, (int, float)):
        value = int(value)
        return max(0, min(value, 4))

    normalized = _normalise_text(value)

    return SKILL_LEVELS.get(normalized, 0)


def _level_name(value: Any) -> str:
    """Return the normalized textual skill level."""
    numeric = _skill_level(value)

    for name, number in SKILL_LEVELS.items():
        if number == numeric:
            return name

    return "none"


def _get_profile_value(profile: Any, field: str, default: Any = None) -> Any:
    """Read a profile field safely from dict-like or object-like profiles."""
    if profile is None:
        return default

    if isinstance(profile, dict):
        return profile.get(field, default)

    return getattr(profile, field, default)


def _find_role(target_role: Any) -> str:
    """
    Match a target role to the closest supported role.

    Exact and substring matching are used.
    """
    role = _normalise_text(target_role)

    if not role:
        return "general"

    # Exact match
    for supported_role in ROLE_REQUIREMENTS:
        if role == supported_role:
            return supported_role

    # Substring match
    for supported_role in ROLE_REQUIREMENTS:
        if supported_role in role or role in supported_role:
            return supported_role

    # Common role mappings
    role_keywords = {
        "analyst": "data analyst",
        "data analyst": "data analyst",
        "scientist": "data scientist",
        "machine learning": "machine learning engineer",
        "ml engineer": "machine learning engineer",
        "software": "software engineer",
        "developer": "web developer",
        "web": "web developer",
        "ai": "ai engineer",
        "cyber": "cybersecurity analyst",
        "security": "cybersecurity analyst",
        "business": "business analyst",
    }

    for keyword, mapped_role in role_keywords.items():
        if keyword in role:
            return mapped_role

    return "general"


def _normalize_skill_state(skill_state: Any) -> Dict[str, Any]:
    """
    Normalize the user's skill state into:

        {
            "Canonical Skill": "level"
        }

    Accepts a normal dictionary and safely handles invalid input.
    """
    if not isinstance(skill_state, dict):
        return {}

    normalized = {}

    for skill, level in skill_state.items():
        canonical = _canonical_skill(skill)

        if not canonical:
            continue

        normalized[canonical] = _level_name(level)

    return normalized


# ---------------------------------------------------------------------------
# Priority calculation
# ---------------------------------------------------------------------------

def _calculate_priority(
    current_level: int,
    target_level: int,
    importance: float,
) -> float:
    """
    Calculate deterministic roadmap priority.

    Priority is based on:
        - size of skill gap
        - importance of skill for the target role

    Returns a value between 0 and 1.

    A skill already at or above the target level receives zero priority.
    """
    if current_level >= target_level:
        return 0.0

    gap = target_level - current_level

    # Maximum meaningful gap is 4 levels.
    gap_ratio = gap / 4.0

    priority = gap_ratio * importance

    return round(max(0.0, min(priority, 1.0)), 4)


def _priority_reason(
    skill: str,
    current_level: str,
    target_level: str,
    priority: float,
) -> str:
    """Generate a deterministic explanation for the priority."""
    current = _skill_level(current_level)
    target = _skill_level(target_level)

    if current >= target:
        return (
            f"{skill} is already at the target level "
            f"({target_level})."
        )

    gap = target - current

    if gap >= 3:
        gap_description = "large"
    elif gap == 2:
        gap_description = "moderate"
    else:
        gap_description = "small"

    return (
        f"{skill} has a {gap_description} skill gap "
        f"({current_level} → {target_level}) and should be "
        f"developed to better match the target role."
    )


# ---------------------------------------------------------------------------
# Main roadmap engine
# ---------------------------------------------------------------------------

def roadmap_engine(profile: Any, skill_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an adaptive deterministic roadmap.

    Parameters
    ----------
    profile:
        Normalized SkillSetu profile.

    skill_state:
        Dictionary mapping skill names to skill levels.

    Returns
    -------
    dict
        Structured roadmap suitable for Person 2 / Streamlit UI.

    Example
    -------
    >>> profile = {
    ...     "persona": "student",
    ...     "target_role": "Data Analyst"
    ... }
    >>> skills = {
    ...     "SQL": "beginner",
    ...     "Statistics": "beginner",
    ...     "Power BI": "none"
    ... }
    >>> roadmap = roadmap_engine(profile, skills)
    """

    target_role = _get_profile_value(profile, "target_role", "")

    role_key = _find_role(target_role)

    requirements = ROLE_REQUIREMENTS.get(
        role_key,
        ROLE_REQUIREMENTS["general"],
    )

    normalized_state = _normalize_skill_state(skill_state)

    skill_results: List[Dict[str, Any]] = []

    for skill, requirement in requirements.items():

        current_level_name = normalized_state.get(skill, "none")

        current_level = _skill_level(current_level_name)
        target_level_name = requirement["target_level"]
        target_level = _skill_level(target_level_name)

        importance = float(requirement["importance"])

        gap = max(0, target_level - current_level)

        priority = _calculate_priority(
            current_level=current_level,
            target_level=target_level,
            importance=importance,
        )

        reason = _priority_reason(
            skill=skill,
            current_level=current_level_name,
            target_level=target_level_name,
            priority=priority,
        )

        skill_results.append(
            {
                "skill": skill,
                "current_level": current_level_name,
                "target_level": target_level_name,
                "gap": gap,
                "importance": round(importance, 4),
                "priority": priority,
                "reason": reason,
            }
        )

    # ---------------------------------------------------------------
    # Sort:
    #   1. Higher priority first
    #   2. Higher importance second
    #   3. Alphabetical skill name as deterministic tie-breaker
    # ---------------------------------------------------------------

    skill_results.sort(
        key=lambda item: (
            -item["priority"],
            -item["importance"],
            item["skill"].lower(),
        )
    )

    # Only actual skill gaps belong in the learning roadmap.
    roadmap_items = [
        {
            "step": index,
            "skill": item["skill"],
            "priority": item["priority"],
            "current_level": item["current_level"],
            "target_level": item["target_level"],
            "gap": item["gap"],
            "reason": item["reason"],
        }
        for index, item in enumerate(
            [item for item in skill_results if item["gap"] > 0],
            start=1,
        )
    ]

    return {
        "target_role": target_role or None,
        "matched_role": role_key,
        "skills": skill_results,
        "roadmap": roadmap_items,
    }


# ---------------------------------------------------------------------------
# Optional helper functions
# ---------------------------------------------------------------------------

def get_required_skills(target_role: str) -> Dict[str, Dict[str, Any]]:
    """
    Return the deterministic skill requirements for a target role.

    This is useful for testing or UI components.
    """
    role_key = _find_role(target_role)

    return ROLE_REQUIREMENTS.get(
        role_key,
        ROLE_REQUIREMENTS["general"],
    ).copy()


def get_skill_level_value(level: Any) -> int:
    """
    Public helper for converting a skill level to 0-4.
    """
    return _skill_level(level)


# ---------------------------------------------------------------------------
# Simple local test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    demo_profile = {
        "persona": "student",
        "target_role": "Data Analyst",
    }

    beginner_state = {
        "SQL": "beginner",
        "Statistics": "beginner",
        "Power BI": "none",
    }

    advanced_sql_state = {
        "SQL": "advanced",
        "Statistics": "beginner",
        "Power BI": "none",
    }

    before = roadmap_engine(
        demo_profile,
        beginner_state,
    )

    after = roadmap_engine(
        demo_profile,
        advanced_sql_state,
    )

    before_sql = next(
        item
        for item in before["skills"]
        if item["skill"] == "SQL"
    )

    after_sql = next(
        item
        for item in after["skills"]
        if item["skill"] == "SQL"
    )

    print("=== SkillSetu Phase 4 Demo ===")
    print()
    print("Before SQL improvement:")
    print(before_sql)

    print()
    print("After SQL improvement:")
    print(after_sql)

    print()
    print(
        "SQL priority decreased:",
        after_sql["priority"] < before_sql["priority"],
    )