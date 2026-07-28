# """
# ats_agent.py

# Responsibility of this module (and ONLY this module):
#     1. Receive company information (name + website / careers URL).
#     2. Determine the careers page for that company.
#     3. Detect which ATS provider is being used (Greenhouse, Lever, Ashby,
#        Workday, iCIMS) based on publicly observable URL patterns.
#     4. Dispatch to the correct provider service.
#     5. Return a normalized list of jobs.

# This module explicitly does NOT:
#     - Touch S3 or any storage layer.
#     - Run ETL or AI analysis.
#     - Schedule or manage background tasks.
#     - Contain provider-specific scraping/API logic (that belongs in
#       app/services/ats/<provider>_service.py).

# Provider services are not implemented yet — this phase is architecture
# only. Each service module exposes a fetch_jobs(careers_url) function that
# currently raises NotImplementedError, so the call contract is locked in
# and provider work can happen independently later without touching this
# agent.
# """

# from __future__ import annotations

# from dataclasses import dataclass, field
# from typing import Callable, Optional
# import re

# from app.schemas import ATSProvider, NormalizedJob
# from app.service.ats import greenhouse_service
# from app.service.ats import lever_service
# from app.service.ats import ashby_service
# from app.service.ats import workday_service
# from app.service.ats import icims_service


# # ============================================================
# # Agent-level input/output models
# # ============================================================

# @dataclass
# class CompanyInput:
#     """What the agent receives to start its work."""
#     company_name: str
#     website_url: str
#     careers_url: Optional[str] = None  # usually already known from the crawler


# @dataclass
# class ATSAgentResult:
#     """What the agent hands back to whoever called it."""
#     company_name: str
#     provider: ATSProvider
#     careers_url: Optional[str]
#     jobs: list[NormalizedJob] = field(default_factory=list)


# # ============================================================
# # Provider detection
# # ============================================================
# # Pure pattern matching against publicly visible URL structure.
# # No auth, no private dashboards, no guessing beyond the URL.

# _PROVIDER_PATTERNS: dict[ATSProvider, re.Pattern] = {
#     ATSProvider.GREENHOUSE: re.compile(r"(boards\.greenhouse\.io|greenhouse\.io/embed)", re.I),
#     ATSProvider.LEVER: re.compile(r"jobs\.lever\.co", re.I),
#     ATSProvider.ASHBY: re.compile(r"jobs\.ashbyhq\.com", re.I),
#     ATSProvider.WORKDAY: re.compile(r"myworkdayjobs\.com", re.I),
#     ATSProvider.ICIMS: re.compile(r"\.icims\.com", re.I),
# }


# def detect_provider(url: str) -> ATSProvider:
#     """Identify the ATS provider from a careers/job-board URL."""
#     if not url:
#         return ATSProvider.UNKNOWN

#     for provider, pattern in _PROVIDER_PATTERNS.items():
#         if pattern.search(url):
#             return provider

#     return ATSProvider.UNKNOWN


# # ============================================================
# # Provider service dispatch table
# # ============================================================
# # Maps each provider to its service module's fetch_jobs entrypoint.
# # Adding a new provider later = one import + one dict entry; nothing in
# # the agent's control flow changes.

# _PROVIDER_DISPATCH: dict[ATSProvider, Callable[[str], list[NormalizedJob]]] = {
#     ATSProvider.GREENHOUSE: greenhouse_service.fetch_jobs,
#     ATSProvider.LEVER: lever_service.fetch_jobs,
#     ATSProvider.ASHBY: ashby_service.fetch_jobs,
#     ATSProvider.WORKDAY: workday_service.fetch_jobs,
#     ATSProvider.ICIMS: icims_service.fetch_jobs,
# }


# # ============================================================
# # Agent
# # ============================================================

# class ATSAgent:
#     """
#     Orchestrates: careers page -> provider detection -> service dispatch ->
#     normalized jobs.

#     Deliberately thin. It owns no provider logic, no I/O beyond calling a
#     service function, and no infrastructure concerns (S3, ETL, AI,
#     background tasks all live elsewhere in the pipeline).
#     """

#     def run(self, company: CompanyInput) -> ATSAgentResult:
#         careers_url = self._resolve_careers_url(company)
#         provider = detect_provider(careers_url) if careers_url else ATSProvider.UNKNOWN

#         jobs: list[NormalizedJob] = []
#         if provider is not ATSProvider.UNKNOWN and careers_url:
#             jobs = self._dispatch(provider, careers_url)

#         return ATSAgentResult(
#             company_name=company.company_name,
#             provider=provider,
#             careers_url=careers_url,
#             jobs=jobs,
#         )

#     def _resolve_careers_url(self, company: CompanyInput) -> Optional[str]:
#         """
#         The caller should pass a careers URL whenever possible.

#         If one is already available, use it directly.
#         Otherwise, future discovery strategies can be plugged in here.
#         """
#         if company.careers_url:
#             return company.careers_url

#         return None

#     def _dispatch(self, provider: ATSProvider, careers_url: str) -> list[NormalizedJob]:
#         service_fn = _PROVIDER_DISPATCH.get(provider)
#         if service_fn is None:
#             return []
#         return service_fn(careers_url)

"""
ats_agent.py

Responsibilities:
    1. Detect the ATS provider from a careers URL.
    2. Dispatch to the correct ATS service.
    3. Return normalized jobs.

This module does NOT:
    - Discover careers URLs
    - Upload to S3
    - Perform AI/ETL
    - Handle background tasks
"""

from __future__ import annotations

import re
from typing import Callable

from app.schemas.ats_schema import ATSProvider, NormalizedJob

from app.service.ats import greenhouse_service
from app.service.ats import lever_service
from app.service.ats import ashby_service
from app.service.ats import workday_service
from app.service.ats import icims_service


# ============================================================
# Provider Detection
# ============================================================

_PROVIDER_PATTERNS: dict[ATSProvider, re.Pattern] = {
    ATSProvider.GREENHOUSE: re.compile(
        r"(boards\.greenhouse\.io|greenhouse\.io/embed)",
        re.IGNORECASE,
    ),
    ATSProvider.LEVER: re.compile(
        r"jobs\.lever\.co",
        re.IGNORECASE,
    ),
    ATSProvider.ASHBY: re.compile(
        r"jobs\.ashbyhq\.com",
        re.IGNORECASE,
    ),
    ATSProvider.WORKDAY: re.compile(
        r"myworkdayjobs\.com",
        re.IGNORECASE,
    ),
    ATSProvider.ICIMS: re.compile(r"\.icims\.com", re.IGNORECASE,),
}


def detect_provider(careers_url: str) -> ATSProvider:
    """
    Detect which ATS provider owns the careers URL.
    """

    if not careers_url:
        return ATSProvider.UNKNOWN

    for provider, pattern in _PROVIDER_PATTERNS.items():
        if pattern.search(careers_url):
            return provider

    return ATSProvider.UNKNOWN


# ============================================================
# Provider Dispatch
# ============================================================

_PROVIDER_DISPATCH: dict[
    ATSProvider,
    Callable[[str], list[NormalizedJob]]
] = {
    ATSProvider.GREENHOUSE: greenhouse_service.fetch_jobs,
    ATSProvider.LEVER: lever_service.fetch_jobs,
    ATSProvider.ASHBY: ashby_service.fetch_jobs,
    ATSProvider.WORKDAY: workday_service.fetch_jobs,
    ATSProvider.ICIMS: icims_service.fetch_jobs,
}


# ============================================================
# Public Entry Point
# ============================================================

def fetch_jobs(careers_url: str) -> list[NormalizedJob]:
    """
    Detect the ATS provider and fetch normalized jobs.

    Returns:
        List[NormalizedJob]
    """

    provider = detect_provider(careers_url)

    if provider == ATSProvider.UNKNOWN:
        return []

    service = _PROVIDER_DISPATCH.get(provider)

    if service is None:
        return []

    try:
        return service(careers_url)

    except Exception:
        # Prevent a provider failure from stopping the competitor crawl.
        return []