from __future__ import annotations

import re
from typing import List

import httpx

from app.schemas.ats_schema import ATSProvider, NormalizedJob


ASHBY_PATTERN = re.compile(
    r"jobs\.ashbyhq\.com/([A-Za-z0-9_-]+)",
    re.IGNORECASE,
)

ASHBY_API = (
    "https://api.ashbyhq.com/posting-api/job-board/{job_board}"
)


def fetch_jobs(careers_url: str) -> List[NormalizedJob]:
    """
    Fetch all public jobs from an Ashby job board.

    Example:
        https://jobs.ashbyhq.com/OpenAI
    """

    job_board = _extract_job_board(careers_url)

    if not job_board:
        return []

    api_url = ASHBY_API.format(job_board=job_board)

    try:
        with httpx.Client(timeout=20) as client:
            response = client.get(api_url)

        response.raise_for_status()

        payload = response.json()

    except httpx.HTTPStatusError:
        return []

    except httpx.RequestError:
        return []

    jobs: List[NormalizedJob] = []

    for job in payload.get("jobs", []):

        jobs.append(
            NormalizedJob(
                title=job.get("title"),
                provider=ATSProvider.ASHBY,
                job_url=job.get("jobUrl"),
                apply_url=job.get("applyUrl"),
                location=_build_location(job),
                department=_build_department(job),
                description=job.get("descriptionPlain"),
                employment_type=job.get("employmentType"),
                posted_at=job.get("publishedAt"),
                external_job_id=job.get("jobUrl"),
            )
        )

    return jobs


def _extract_job_board(url: str) -> str | None:
    """
    Example:

        https://jobs.ashbyhq.com/OpenAI

    returns:

        OpenAI
    """

    match = ASHBY_PATTERN.search(url)

    if not match:
        return None

    return match.group(1)


def _build_location(job: dict) -> str | None:

    return job.get("location")


def _build_department(job: dict) -> str | None:

    department = job.get("department")
    team = job.get("team")

    if department and team:
        return f"{department} / {team}"

    return department or team