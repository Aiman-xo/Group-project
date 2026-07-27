from __future__ import annotations

import html
import re
from typing import List

import httpx
from bs4 import BeautifulSoup

from app.schemas.ats_schema import ATSProvider, NormalizedJob


LEVER_COMPANY_PATTERN = re.compile(
    r"https?://jobs\.lever\.co/([^/?#]+)",
    re.IGNORECASE,
)

LEVER_API = "https://api.lever.co/v0/postings/{company}?mode=json"


def fetch_jobs(careers_url: str) -> List[NormalizedJob]:
    """
    Fetch all public jobs from a Lever careers page.

    Example:
        https://jobs.lever.co/postman
    """

    company = _extract_company_slug(careers_url)
    print("Company:", company)

    if not company:
        return []

    api_url = LEVER_API.format(company=company)
    print("API URL:", api_url)

    try:
        with httpx.Client(timeout=20) as client:
            response = client.get(api_url)
            print("Status Code:", response.status_code)

        response.raise_for_status()

        payload = response.json()
        print("Payload Type:", type(payload))
        print("Number of Jobs:", len(payload))

    except httpx.HTTPStatusError:
        return []

    except httpx.RequestError:
        return []

    jobs: List[NormalizedJob] = []

    for job in payload:

        jobs.append(
            NormalizedJob(
                title=job.get("text"),
                provider=ATSProvider.LEVER,
                job_url=job.get("hostedUrl"),
                apply_url=job.get("applyUrl") or job.get("hostedUrl"),
                location=_build_location(job),
                department=_build_department(job),
                description=_clean_description(
                    job.get("descriptionPlain")
                    or job.get("description")
                ),
                employment_type=job.get("categories", {}).get("commitment"),
                posted_at=None,
                external_job_id=str(job.get("id")),
            )
        )

    return jobs


def _extract_company_slug(url: str) -> str | None:
    """
    Example:

        https://jobs.lever.co/postman

    returns:

        postman
    """

    match = LEVER_COMPANY_PATTERN.search(url)

    if not match:
        return None

    return match.group(1)


def _build_location(job: dict) -> str | None:

    return (
        job.get("categories", {})
        .get("location")
    )


def _build_department(job: dict) -> str | None:

    return (
        job.get("categories", {})
        .get("team")
    )


def _clean_description(content: str | None) -> str | None:
    """
    Convert Lever HTML into clean plain text.
    """

    if not content:
        return None

    content = html.unescape(content)

    soup = BeautifulSoup(content, "html.parser")

    return soup.get_text(separator="\n", strip=True)