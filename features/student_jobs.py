"""
SkillSetu - Student Jobs Experience

Student-facing wrapper around the shared live job fetcher
and matching engine.

This module does not implement its own matching algorithm.
"""

from typing import Any, Dict, List

from data.jobs import fetch_jobs
from core.matching_engine import matching_engine


def get_student_jobs(profile) -> List[Dict[str, Any]]:
    """
    Fetch live jobs relevant to the student's profile.

    Returns an empty list if the live provider fails.
    """

    try:
        jobs = fetch_jobs(profile)

        if not isinstance(jobs, list):
            return []

        return jobs

    except Exception:
        return []


def match_student_jobs(
    profile,
    opportunities: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    """
    Match jobs against the student's profile.

    If opportunities are not supplied, live jobs are fetched automatically.

    The actual scoring remains inside core.matching_engine.
    """

    if opportunities is None:
        opportunities = get_student_jobs(profile)

    if not opportunities:
        return []

    try:
        results = matching_engine(profile, opportunities)

        if not isinstance(results, list):
            return []

        return results

    except Exception:
        return []


def format_job_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a shared matching result into a student-friendly structure.
    """

    opportunity = result.get("opportunity", {})

    score = result.get("score", 0)

    # The shared engine may return either a decimal score or percentage.
    if isinstance(score, (int, float)):
        match_percentage = (
            round(score * 100)
            if 0 <= score <= 1
            else round(score)
        )
    else:
        match_percentage = 0

    return {
        "title": opportunity.get("title", ""),
        "company": opportunity.get("company", ""),
        "location": opportunity.get("location", ""),
        "remote": bool(opportunity.get("remote", False)),
        "match_percentage": match_percentage,
        "matched_skills": result.get("matched_skills", []),
        "missing_skills": result.get("missing_skills", []),
        "reasons": result.get("reasons", []),
        "source": opportunity.get("source", ""),
        "url": opportunity.get("url", ""),
    }


def get_student_job_results(profile) -> List[Dict[str, Any]]:
    """
    Complete student job flow:

        Profile
          ↓
        Live jobs
          ↓
        Shared matching engine
          ↓
        Student-friendly results
    """

    matched_results = match_student_jobs(profile)

    return [
        format_job_result(result)
        for result in matched_results
        if isinstance(result, dict)
    ]


# ---------------------------------------------------------------------------
# Local Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from core.profile import normalize_profile

    test_profile = normalize_profile(
        {
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
    )

    print("Student jobs module test")
    print("------------------------")

    jobs = get_student_jobs(test_profile)

    print(f"Live relevant jobs fetched: {len(jobs)}")

    results = get_student_job_results(test_profile)

    print(f"Matched results: {len(results)}")

    if results:
        print("First result:")
        print(results[0])
    else:
        print("No matching live jobs returned.")
        print("This is an acceptable result if the live provider has no relevant jobs or is unavailable.")