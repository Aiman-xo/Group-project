from __future__ import annotations

import re
from typing import List
import html
from bs4 import BeautifulSoup

import httpx

from app.schemas.ats_schema import ATSProvider, NormalizedJob


GREENHOUSE_BOARD_PATTERN = re.compile(
    r"boards\.greenhouse\.io/([A-Za-z0-9_\-]+)",
    re.IGNORECASE,
)

GREENHOUSE_API = (
    "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
)


def fetch_jobs(careers_url: str) -> List[NormalizedJob]:
    """
    Fetch all public jobs from a Greenhouse job board.

    Parameters
    ----------
    careers_url:
        Example:
            https://boards.greenhouse.io/openai

    Returns
    -------
    list[NormalizedJob]
    """

    board_token = _extract_board_token(careers_url)
    # print("Board Token:", board_token)

    if not board_token:
        return []

    api_url = GREENHOUSE_API.format(board_token=board_token)

    try:
        with httpx.Client(timeout=20) as client:
            response = client.get(api_url)
            #console
            # print("API URL:", api_url)
            # print("Status Code:", response.status_code)
            

        response.raise_for_status()

        payload = response.json()
        # print(payload)

    except Exception:
        return []

    jobs = []

    for job in payload.get("jobs", []):

       jobs.append(
            NormalizedJob(
                title=job.get("title"),
                job_url=job.get("absolute_url"),
                provider=ATSProvider.GREENHOUSE,
                apply_url=job.get("absolute_url"),
                location=_build_location(job),
                department=_build_department(job),
                description=_clean_description(job.get("content")),
                employment_type=None,
                posted_at=job.get("updated_at"),
                external_job_id=str(job.get("id")),
            )
        )

    return jobs


def _extract_board_token(url: str) -> str | None:
    """
    Extract:

        https://boards.greenhouse.io/openai

    -> openai
    """

    match = GREENHOUSE_BOARD_PATTERN.search(url)

    if not match:
        return None

    return match.group(1)


def _build_location(job: dict) -> str | None:
    offices = job.get("offices") or []

    if not offices:
        return None

    return ", ".join(
        office.get("location") or office.get("name")
        for office in offices
        if office
    )


def _build_department(job: dict) -> str | None:
    departments = job.get("departments") or []

    if not departments:
        return None

    return " / ".join(
        dept.get("name")
        for dept in departments
        if dept.get("name")
    )

def _clean_description(content: str | None) -> str | None:
    """
    Convert Greenhouse HTML job description into clean plain text.
    """

    if not content:
        return None

    content = html.unescape(content)

    soup = BeautifulSoup(content, "html.parser")

    return soup.get_text(separator="\n", strip=True)