def _normalize_text(value):
    """Convert a value to lowercase stripped text."""
    if value is None:
        return ""
    return str(value).strip().lower()


def _normalize_skills(skills):
    """Convert skills into a clean lowercase set."""
    if not skills:
        return set()

    return {
        _normalize_text(skill)
        for skill in skills
        if _normalize_text(skill)
    }


def _skill_match(profile_skills, opportunity):
    """Calculate skill match between 0 and 1."""
    user_skills = _normalize_skills(profile_skills)
    opportunity_skills = _normalize_skills(opportunity.get("tags", []))

    if not opportunity_skills:
        return 0.0, [], []

    matched = sorted(user_skills & opportunity_skills)
    missing = sorted(opportunity_skills - user_skills)

    score = len(matched) / len(opportunity_skills)

    return score, matched, missing


def _location_match(profile, opportunity):
    """Calculate location compatibility between 0 and 1."""
    profile_location = _normalize_text(profile.location)
    opportunity_location = _normalize_text(opportunity.get("location", ""))

    if not profile_location or not opportunity_location:
        return 0.0

    remote = opportunity.get("remote", False)

    if remote and _normalize_text(profile.work_preference) == "remote":
        return 1.0

    if profile_location in opportunity_location:
        return 1.0

    if opportunity_location in profile_location:
        return 1.0

    return 0.0


def _experience_match(profile, opportunity):
    """Calculate experience compatibility between 0 and 1."""
    profile_experience = _normalize_text(profile.experience)
    opportunity_experience = _normalize_text(
        opportunity.get("experience", "")
    )

    if not opportunity_experience or not profile_experience:
        return 0.0

    if profile_experience == opportunity_experience:
        return 1.0

    # Treat entry-level opportunities as compatible with beginners.
    beginner_words = {"beginner", "entry", "entry-level", "fresher", "junior"}

    if (
        profile_experience in beginner_words
        and opportunity_experience in beginner_words
    ):
        return 1.0

    return 0.0


def _preference_match(profile, opportunity):
    """Calculate work-preference compatibility between 0 and 1."""
    preference = _normalize_text(profile.work_preference)

    if not preference:
        return 0.0

    remote = opportunity.get("remote", False)

    if preference == "remote":
        return 1.0 if remote else 0.0

    opportunity_location = _normalize_text(
        opportunity.get("location", "")
    )

    if preference in opportunity_location:
        return 1.0

    if preference in {"local", "onsite", "on-site"}:
        return 1.0 if not remote else 0.0

    return 0.0


def matching_engine(profile, opportunities):
    """
    Rank opportunities against a profile.

    Scoring:
        0.50 * skill_match
        0.20 * location_match
        0.15 * experience_match
        0.15 * preference_match
    """

    results = []

    for opportunity in opportunities or []:
        skill_score, matched_skills, missing_skills = _skill_match(
            profile.skills,
            opportunity,
        )

        location_score = _location_match(profile, opportunity)
        experience_score = _experience_match(profile, opportunity)
        preference_score = _preference_match(profile, opportunity)

        total_score = (
            0.50 * skill_score
            + 0.20 * location_score
            + 0.15 * experience_score
            + 0.15 * preference_score
        )

        reasons = []

        if matched_skills:
            reasons.append(
                f"Matched skills: {', '.join(matched_skills)}"
            )

        if missing_skills:
            reasons.append(
                f"Missing skills: {', '.join(missing_skills)}"
            )

        if location_score == 1.0:
            reasons.append("Location matches")

        if experience_score == 1.0:
            reasons.append("Experience level matches")

        if preference_score == 1.0:
            reasons.append("Work preference matches")

        results.append(
            {
                "opportunity": opportunity,
                "score": round(total_score * 100),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "reasons": reasons,
            }
        )

    results.sort(key=lambda result: result["score"], reverse=True)

    return results