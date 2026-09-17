import requests
from datetime import datetime, timezone


ARBEITNOW_API = "https://www.arbeitnow.com/api/job-board-api"


def _normalize_job(job):
    """Convert an Arbeitnow job into our shared job format."""

    return {
        "id": str(job.get("slug") or job.get("id") or ""),
        "title": str(job.get("title") or "").strip(),
        "company": str(job.get("company_name") or "").strip(),
        "location": str(job.get("location") or "").strip(),
        "remote": bool(job.get("remote", False)),
        "description": str(job.get("description") or "").strip(),
        "tags": [
            str(tag).strip().lower()
            for tag in job.get("tags", [])
            if str(tag).strip()
        ],
        "url": str(job.get("url") or "").strip(),
        "source": "Arbeitnow",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _job_matches_profile(job, profile):
    """Check whether a job has some relevance to the user's profile."""

    if profile is None:
        return True

    profile_skills = {
        skill.strip().lower()
        for skill in getattr(profile, "skills", [])
        if skill.strip()
    }

    job_text = " ".join([
        job.get("title", ""),
        job.get("description", ""),
        " ".join(job.get("tags", [])),
    ]).lower()

    skill_match = any(
        skill in job_text
        for skill in profile_skills
    )

    role = getattr(profile, "target_role", "").strip().lower()

    role_match = role and role in job_text

    location = getattr(profile, "location", "").strip().lower()
    job_location = job.get("location", "").lower()

    location_match = (
        location
        and location in job_location
    )

    remote_preference = (
        getattr(profile, "work_preference", "")
        .strip()
        .lower()
    )

    remote_match = (
        remote_preference == "remote"
        and job.get("remote", False)
    )

    return bool(
        skill_match
        or role_match
        or location_match
        or remote_match
    )


def fetch_jobs(profile=None):
    """
    Fetch live jobs from Arbeitnow.

    If a profile is provided, return jobs relevant to that profile.
    If no profile is provided, return all normalized jobs.
    """

    try:
        response = requests.get(
            ARBEITNOW_API,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        jobs = data.get("data", [])

        normalized_jobs = [
            _normalize_job(job)
            for job in jobs
            if isinstance(job, dict)
        ]

        if profile is None:
            return normalized_jobs

        filtered_jobs = [
            job
            for job in normalized_jobs
            if _job_matches_profile(job, profile)
        ]

        return filtered_jobs

    except requests.RequestException:
        return []

    except (ValueError, TypeError):
        return []

    except Exception:
        return []