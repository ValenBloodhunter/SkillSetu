"""
SkillSetu - Live Job Data Source

Arbeitnow is used only as a LIVE job source.

IMPORTANT:
This module does NOT decide whether a job is a good
recommendation. The shared matching_engine() does ranking.

We deliberately avoid aggressive filtering here because
filtering the API response too early can remove all jobs.
"""

from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


ARBEITNOW_API = (
    "https://www.arbeitnow.com/api/job-board-api"
)


def _clean_html(value):
    """Convert HTML descriptions into plain text."""

    if not value:
        return ""

    try:
        return BeautifulSoup(
            str(value),
            "html.parser",
        ).get_text(
            " ",
            strip=True,
        )

    except Exception:
        return str(value)


def _normalize_tags(tags):
    """Normalize job tags into a clean list."""

    if not tags:
        return []

    if isinstance(tags, list):
        return [
            str(tag).strip()
            for tag in tags
            if str(tag).strip()
        ]

    return [
        str(tags).strip()
    ]


def _normalize_job(job):
    """
    Convert Arbeitnow's response into the common
    SkillSetu opportunity format.
    """

    return {
        "id": (
            job.get("slug")
            or job.get("id")
            or ""
        ),

        "slug": (
            job.get("slug")
            or ""
        ),

        "title": (
            job.get("title")
            or "Untitled Opportunity"
        ),

        "company": (
            job.get("company_name")
            or job.get("company")
            or "Not specified"
        ),

        "location": (
            job.get("location")
            or "Not specified"
        ),

        "remote": bool(
            job.get("remote", False)
        ),

        "description": _clean_html(
            job.get("description", "")
        ),

        "tags": _normalize_tags(
            job.get("tags", [])
        ),

        "url": (
            job.get("url")
            or ""
        ),

        "source": "Arbeitnow Live API",

        "fetched_at": datetime.now(
            timezone.utc
        ).strftime(
            "%Y-%m-%d %H:%M UTC"
        ),

        # Arbeitnow does not reliably provide
        # structured experience requirements.
        "experience": "",
    }


def fetch_jobs(profile=None):
    """
    Fetch LIVE jobs.

    We intentionally return the normalized live feed
    without doing profile filtering here.

    Why?

    Previously SkillSetu used checks such as:

        skill_match OR role_match OR location_match

    That caused false positives.

    Example:
        Skill = "Driving"

    could accidentally match:
        "driving business insights"

    inside a Data Scientist description.

    Profile relevance must therefore be handled by the
    shared matching_engine() and the presentation layer,
    not by loose substring filtering in the data source.
    """

    try:
        response = requests.get(
            ARBEITNOW_API,
            timeout=10,
            headers={
                "User-Agent": (
                    "SkillSetu-Hackathon/1.0"
                )
            },
        )

        response.raise_for_status()

        payload = response.json()

        raw_jobs = payload.get(
            "data",
            [],
        )

        normalized_jobs = []

        for job in raw_jobs:
            try:
                normalized = (
                    _normalize_job(job)
                )

                if normalized.get("title"):
                    normalized_jobs.append(
                        normalized
                    )

            except Exception:
                continue

        return normalized_jobs

    except Exception as exc:
        print(
            "SkillSetu job fetch error:",
            exc,
        )

        return []