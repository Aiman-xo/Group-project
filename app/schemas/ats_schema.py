"""
ATS Job Schema

Defines the normalized data contract for job postings returned by every
Applicant Tracking System (ATS) provider.

All ATS provider services (Greenhouse, Lever, Ashby, Workday, iCIMS)
must convert their raw API/HTML responses into this common schema before
returning data to the ATS Agent.

This ensures every downstream component (ATS Agent, S3 upload, ETL,
Analytics, AI) works with a consistent job structure regardless of the
ATS provider.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, HttpUrl


class ATSProvider(str, Enum):
    """
    Supported Applicant Tracking System providers.
    """

    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WORKDAY = "workday"
    ICIMS = "icims"
    UNKNOWN = "unknown"


class NormalizedJob(BaseModel):
    """
    Normalized representation of a single job posting.

    Every ATS provider service must return job data in this format,
    regardless of the provider's original API response.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=False,
    )

    # Required Fields
    title: str
    job_url: HttpUrl
    provider: ATSProvider

    # Optional Fields
    apply_url: HttpUrl | None = None
    location: str | None = None
    department: str | None = None
    description: str | None = None
    employment_type: str | None = None
    posted_at: datetime | None = None
    external_job_id: str | None = None