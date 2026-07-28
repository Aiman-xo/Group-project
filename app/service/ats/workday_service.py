from __future__ import annotations

import re
from typing import List

import httpx

from app.schemas.ats_schema import ATSProvider, NormalizedJob


# ---------------------------------------------------------------------------
# VERIFICATION NOTES (read before trusting field names blindly)
# ---------------------------------------------------------------------------
# Endpoint verified live: GET against this URL returns HTTP 400 (not 404),
# confirming it exists and requires POST:
#
#   https://workday.wd5.myworkdayjobs.com/wday/cxs/workday/Workday/jobs
#
# This is Workday's public CXS (career site) JSON feed, exposed by every
# public Workday tenant career site. It is NOT the same as Workday's
# official SOAP/REST HCM API, which requires OAuth2 and a paying tenant
# account -- that API cannot be used for this purpose at all.
#
# Field names below (jobPostings, title, locationsText, postedOn,
# externalPath, bulletFields, total) are sourced from a third-party
# technical breakdown of this API, not invented and not from memory of
# a specific integration. They could NOT be confirmed against a live
# response in this environment because outbound network access here is
# restricted to a fixed allowlist that does not include
# myworkdayjobs.com. Run test_workday.py in your own environment first
# and inspect the raw JSON before relying on this in production --
# adjust field names if the live payload differs.
#
# The listing endpoint does not reliably expose department or full
# description across tenants (per the same source). Getting those
# requires a second per-job GET to
# /wday/cxs/{tenant}/{site}/job/{externalPath}, which this module
# deliberately does NOT call automatically -- doing so for every job
# multiplies request volume and risks tripping Workday's bot detection
# (Akamai). department/description are returned as None here; add
# per-job enrichment as an explicit opt-in later if you need it.
# ---------------------------------------------------------------------------


WORKDAY_URL_PATTERN = re.compile(
    r"https?://(?P<tenant>[a-zA-Z0-9\-]+)\.(?P<dc>wd\d+)\.myworkdayjobs\.com"
    r"/(?:[a-zA-Z]{2}-[A-Z]{2}/)?(?P<site>[^/?#]+)",
)

WORKDAY_JOBS_API = (
    "https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
)

WORKDAY_JOB_BASE_URL = "https://{tenant}.{dc}.myworkdayjobs.com/en-US/{site}"

PAGE_SIZE = 20
MAX_PAGES = 25  # safety cap: up to 500 jobs per company per run


def fetch_jobs(careers_url: str) -> List[NormalizedJob]:
    """
    Fetch all public jobs from a Workday career site's CXS listing API.

    Example:
        https://workday.wd5.myworkdayjobs.com/Workday

    Paginates using offset/limit until the API returns an empty page or
    the running offset reaches the reported total. Capped at MAX_PAGES
    as a safety limit against runaway pagination.
    """

    info = _extract_workday_info(careers_url)

    if not info:
        return []

    tenant, dc, site = info
    api_url = WORKDAY_JOBS_API.format(tenant=tenant, dc=dc, site=site)

    jobs: List[NormalizedJob] = []
    offset = 0

    try:
        with httpx.Client(timeout=20) as client:
            for _ in range(MAX_PAGES):
                request_body = {
                    "appliedFacets": {},
                    "limit": PAGE_SIZE,
                    "offset": offset,
                    "searchText": "",
                }

                response = client.post(api_url, json=request_body)
                


                response.raise_for_status()

                payload = response.json()
                postings = payload.get("jobPostings") or []

                if not postings:
                    break

                for job in postings:
                    jobs.append(
                        NormalizedJob(
                            title=job.get("title"),
                            provider=ATSProvider.WORKDAY,
                            job_url=_build_job_url(job, tenant, dc, site),
                            apply_url=_build_job_url(job, tenant, dc, site),
                            location=_build_location(job),
                            department=_build_department(job),
                            description=None,  # not available in listing endpoint; see module notes
                            employment_type=job.get("timeType"),
                            posted_at=None,
                            external_job_id=_build_external_id(job),
                        )
                    )

                total = payload.get("total", 0)
                offset += PAGE_SIZE

                if offset >= total:
                    break

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(e)

        return []

    return jobs


def _extract_workday_info(url: str) -> tuple[str, str, str] | None:
    """
    Extract (tenant, data_center, site) from a Workday careers URL.

    Example:
        https://workday.wd5.myworkdayjobs.com/en-US/Workday

    -> ("workday", "wd5", "Workday")
    """

    match = WORKDAY_URL_PATTERN.search(url)

    if not match:
        return None

    tenant = match.group("tenant").lower()
    dc = match.group("dc").lower()
    site = match.group("site")

    return tenant, dc, site


def _build_job_url(job: dict, tenant: str, dc: str, site: str) -> str | None:
    external_path = job.get("externalPath")

    if not external_path:
        return None

    base = WORKDAY_JOB_BASE_URL.format(tenant=tenant, dc=dc, site=site)
    return base + external_path


def _build_location(job: dict) -> str | None:
    return job.get("locationsText") or job.get("location")


def _build_department(job: dict) -> str | None:
    # See module-level VERIFICATION NOTES: not reliably present in the
    # listing payload across tenants. Left as None rather than guessing
    # at a field name that may not exist for a given tenant.
    return None


def _build_external_id(job: dict) -> str | None:
    bullet_fields = job.get("bulletFields") or []

    if not bullet_fields:
        return None

    return str(bullet_fields[0])