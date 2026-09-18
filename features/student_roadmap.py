"""
SkillSetu - Student Roadmap Experience

Handles:
- Converting student assessment results into roadmap-compatible skill levels
- Generating a roadmap using the shared roadmap engine
- Simulating skill improvements
- Comparing before/after skill states and roadmaps

This module does not duplicate roadmap logic.
"""

from typing import Any, Dict

from core.roadmap_engine import roadmap_engine
from core.profile import normalize_profile


# ---------------------------------------------------------------------------
# Skill-State Adapter
# ---------------------------------------------------------------------------

def assessment_to_roadmap_state(
    skill_state: Dict[str, float],
) -> Dict[str, str]:
    """
    Convert 0-1 assessment values into the level labels expected
    by the shared roadmap engine.

    0.00        -> none
    0.01-0.40   -> beginner
    0.41-0.70   -> intermediate
    0.71-1.00   -> advanced
    """

    roadmap_state = {}

    for skill, value in skill_state.items():
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.0

        value = max(0.0, min(1.0, value))

        if value == 0:
            level = "none"
        elif value <= 0.40:
            level = "beginner"
        elif value <= 0.70:
            level = "intermediate"
        else:
            level = "advanced"

        roadmap_state[str(skill).strip().lower()] = level

    return roadmap_state


# ---------------------------------------------------------------------------
# Roadmap Generation
# ---------------------------------------------------------------------------

def generate_student_roadmap(
    profile: Dict[str, Any],
    skill_state: Dict[str, float],
) -> Dict[str, Any]:
    """
    Generate a roadmap for a student.

    Uses the shared deterministic roadmap engine.
    """

    try:
        normalized_profile = normalize_profile(profile)

        roadmap_state = assessment_to_roadmap_state(skill_state)

        return roadmap_engine(
            normalized_profile,
            roadmap_state,
        )

    except Exception as exc:
        return {
            "target_role": profile.get("target_role", ""),
            "matched_role": profile.get("target_role", ""),
            "skills": [],
            "roadmap": [],
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Simulated Skill Update
# ---------------------------------------------------------------------------

def simulate_skill_update(
    skill_state: Dict[str, float],
    skill: str,
    improvement: float = 0.20,
) -> Dict[str, float]:
    """
    Simulate improvement in one skill.

    The original dictionary is not modified.

    Example:
        Python 0.60 + 0.20 -> 0.80
    """

    updated_state = dict(skill_state)

    normalized_skill = str(skill).strip().lower()

    if not normalized_skill:
        return updated_state

    try:
        current_value = float(
            updated_state.get(normalized_skill, 0.0)
        )
        improvement = float(improvement)
    except (TypeError, ValueError):
        return updated_state

    current_value = max(0.0, min(1.0, current_value))
    improvement = max(0.0, improvement)

    updated_state[normalized_skill] = round(
        min(1.0, current_value + improvement),
        2,
    )

    return updated_state


# ---------------------------------------------------------------------------
# Before / After Comparison
# ---------------------------------------------------------------------------

def compare_roadmaps(
    before: Dict[str, Any],
    after: Dict[str, Any],
    before_skill_state: Dict[str, float] | None = None,
    after_skill_state: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """
    Compare before/after roadmaps and skill states.

    A skill can disappear from the roadmap because it reached its
    target level, so skill-state changes are also tracked.
    """

    before_skill_state = before_skill_state or {}
    after_skill_state = after_skill_state or {}

    changes = []

    all_skills = sorted(
        set(before_skill_state) | set(after_skill_state)
    )

    for skill in all_skills:
        try:
            old_value = float(
                before_skill_state.get(skill, 0.0)
            )
        except (TypeError, ValueError):
            old_value = 0.0

        try:
            new_value = float(
                after_skill_state.get(skill, 0.0)
            )
        except (TypeError, ValueError):
            new_value = 0.0

        if old_value != new_value:
            changes.append(
                {
                    "skill": skill,
                    "before_value": round(old_value, 2),
                    "after_value": round(new_value, 2),
                    "improvement": round(
                        new_value - old_value,
                        2,
                    ),
                }
            )

    return {
        "changes": changes,
        "changed_skills": len(changes),
    }


# ---------------------------------------------------------------------------
# Complete Simulation Flow
# ---------------------------------------------------------------------------

def simulate_roadmap_progress(
    profile: Dict[str, Any],
    skill_state: Dict[str, float],
    skill: str,
    improvement: float = 0.20,
) -> Dict[str, Any]:
    """
    Complete before/after roadmap simulation.

    Returns:
        original skill state
        updated skill state
        before roadmap
        after roadmap
        roadmap changes
    """

    before_roadmap = generate_student_roadmap(
        profile,
        skill_state,
    )

    updated_state = simulate_skill_update(
        skill_state,
        skill,
        improvement,
    )

    after_roadmap = generate_student_roadmap(
        profile,
        updated_state,
    )

    comparison = compare_roadmaps(
        before_roadmap,
        after_roadmap,
        before_skill_state=skill_state,
        after_skill_state=updated_state,
    )

    return {
        "original_skill_state": dict(skill_state),
        "updated_skill_state": updated_state,
        "before_roadmap": before_roadmap,
        "after_roadmap": after_roadmap,
        "comparison": comparison,
    }


# ---------------------------------------------------------------------------
# Local Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    profile = {
        "persona": "student",
        "name": "Test Student",
        "location": "Hyderabad",
        "education": "B.Tech",
        "skills": ["Python", "Excel"],
        "target_role": "Data Analyst",
        "experience": "Fresher",
        "work_preference": "Any",
        "language": "English",
    }

    skill_state = {
        "python": 0.80,
        "excel": 0.60,
    }

    print("Student roadmap module test")
    print("---------------------------")

    before = generate_student_roadmap(
        profile,
        skill_state,
    )

    print("Before roadmap steps:")

    for step in before.get("roadmap", []):
        print(
            f"  {step['step']}. "
            f"{step['skill']} - "
            f"{step['current_level']} -> "
            f"{step['target_level']}"
        )

    simulation = simulate_roadmap_progress(
        profile,
        skill_state,
        skill="python",
        improvement=0.20,
    )

    print("\nUpdated skill state:")
    print(simulation["updated_skill_state"])

    print("\nChanged skills:")

    for change in simulation["comparison"]["changes"]:
        print(
            f"  {change['skill']}: "
            f"{change['before_value']} -> "
            f"{change['after_value']} "
            f"(+{change['improvement']})"
        )

    print(
        f"\nTotal changed skills: "
        f"{simulation['comparison']['changed_skills']}"
    )