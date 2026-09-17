from dataclasses import dataclass, field
from typing import List


@dataclass
class Profile:
    persona: str
    name: str = ""
    location: str = ""
    language: str = ""
    education: str = ""
    skills: List[str] = field(default_factory=list)
    target_role: str = ""
    experience: str = ""
    work_preference: str = ""


def normalize_profile(profile: dict) -> Profile:
    """
    Convert a raw profile dictionary into the shared Profile format.

    This same function is used for both Student and Livelihood profiles.
    """

    return Profile(
        persona=str(profile.get("persona", "")).strip().lower(),
        name=str(profile.get("name", "")).strip(),
        location=str(profile.get("location", "")).strip(),
        language=str(profile.get("language", "")).strip(),
        education=str(profile.get("education", "")).strip(),
        skills=[
            str(skill).strip().lower()
            for skill in profile.get("skills", [])
            if str(skill).strip()
        ],
        target_role=str(profile.get("target_role", "")).strip(),
        experience=str(profile.get("experience", "")).strip(),
        work_preference=str(profile.get("work_preference", "")).strip(),
    )


def validate_profile(profile: Profile) -> bool:
    """
    Basic validation for the shared profile.

    A profile must have a persona.
    """

    valid_personas = {"student", "livelihood"}

    if profile.persona not in valid_personas:
        return False

    return True