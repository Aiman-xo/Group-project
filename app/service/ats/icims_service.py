from __future__ import annotations

import html
import re
from typing import List

import httpx
from bs4 import BeautifulSoup

from app.schemas.ats_schema import ATSProvider, NormalizedJob

# Regex to match iCIMS portal domain formats:
# e.g., https://careers-company.icims.com/jobs/search
# or https://company.icims.com/jobs/search
ICIMS_URL_PATTERN = re.compile(
    r"https?://([a-zA-Z0-9\-]+)\.icims\.com",
    re.IGNORECASE,
)

PAGE_SIZE = 50
MAX_PAGES = 10  # Capped at 500 jobs per scan for safety


def fetch_jobs(careers_url: str) -> List[NormalizedJob]:
    """
    Fetch all public job postings from an iCIMS job portal.

    Example careers_url:
        https://careers-google.icims.com/jobs/search
    """
    portal_subdomain = _extract_portal_subdomain(careers_url)

    if not portal_subdomain:
        return []

    base_portal_url = f"https://{portal_subdomain}.icims.com"
    jobs: List[NormalizedJob] = []
    page = 0

    try:
        with httpx.Client(
            timeout=20,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
            follow_redirects=True,
        ) as client:
            while page < MAX_PAGES:
                search_url = (
                    f"{base_portal_url}/jobs/search"
                    f"?pr={page}&in_iframe=1"
                )

                response = client.get(search_url)

                if response.status_code != 200:
                    break

                page_jobs = _parse_icims_search_page(
                    response.text, base_portal_url
                )

                if not page_jobs:
                    break

                jobs.extend(page_jobs)

                # Check if next page exists in DOM
                if "pr=" not in response.text or len(page_jobs) < PAGE_SIZE:
                    break

                page += 1

    except Exception:
        return jobs

    return jobs


def _extract_portal_subdomain(url: str) -> str | None:
    """
    Extract subdomain from iCIMS URL.
    https://careers-google.icims.com/jobs/search -> careers-google
    """
    match = ICIMS_URL_PATTERN.search(url)
    if not match:
        return None
    return match.group(1)


def _parse_icims_search_page(
    html_content: str, base_url: str
) -> List[NormalizedJob]:
    """
    Parse HTML search listings rendered by iCIMS search portal.
    """
    soup = BeautifulSoup(html_content, "lxml")
    jobs: List[NormalizedJob] = []

    # iCIMS search results render inside container elements with class 'iCIMS_JobsTable'
    job_rows = soup.find_all("div", class_=re.compile(r"row", re.I))

    for row in job_rows:
        title_tag = row.find("a", class_=re.compile(r"iCIMS_Anchor", re.I))
        if not title_tag or not title_tag.get("href"):
            continue

        title = title_tag.get_text(strip=True)
        job_url = title_tag["href"].split("?")[0]
        if not job_url.startswith("http"):
            job_url = f"{base_url}{job_url}"

        # Extract External ID (iCIMS URLs typically contain /jobs/{id}/job)
        job_id_match = re.search(r"/jobs/(\d+)/", job_url)
        external_id = job_id_match.group(1) if job_id_match else None

        # Extract metadata columns (Location, Category/Department, Employment Type)
        location = None
        department = None

        dl_tags = row.find_all("dl")
        for dl in dl_tags:
            dt = dl.find("dt")
            dd = dl.find("dd")
            if not dt or not dd:
                continue

            label = dt.get_text(strip=True).lower()
            val = dd.get_text(strip=True)

            if "location" in label:
                location = val
            elif "category" in label or "department" in label:
                department = val

        jobs.append(
            NormalizedJob(
                title=title,
                provider=ATSProvider.ICIMS,
                job_url=job_url,
                apply_url=job_url,
                location=location,
                department=department,
                description=None,  # Detailed description is on the individual posting page
                employment_type=None,
                posted_at=None,
                external_job_id=external_id,
            )
        )

    return jobs