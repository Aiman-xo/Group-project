#Greenhouse -test

# from app.service.ats.greenhouse_service import fetch_jobs


# def main():
#     careers_url = "https://boards.greenhouse.io/postman"

#     print(f"Testing Greenhouse board: {careers_url}\n")

#     jobs = fetch_jobs(careers_url)

#     print(f"Found {len(jobs)} jobs\n")

#     if not jobs:
#         print("No jobs returned.")
#         return

#     print("First 5 Normalized Jobs:\n")

#     for index, job in enumerate(jobs[:5], start=1):
#         print("=" * 80)
#         print(f"Job #{index}")
#         print("=" * 80)

#         print("Title      :", job.title)
#         print("Provider   :", job.provider.value)
#         print("Location   :", job.location)
#         print("Department :", job.department)
#         print("Job URL    :", job.job_url)
#         print("Posted At  :", job.posted_at)
#         print("Job ID     :", job.external_job_id)

#         print("\nDescription Preview:")
#         if job.description:
#             print(job.description[:300] + "...")
#         else:
#             print("No description")

#         print()


# if __name__ == "__main__":
#     main()


#lever

# from app.service.ats.lever_service import fetch_jobs


# def main():

#     careers_url = "https://jobs.lever.co/figma"

#     print(f"Testing Lever board: {careers_url}\n")

#     jobs = fetch_jobs(careers_url)

#     print(f"Found {len(jobs)} jobs\n")

#     if not jobs:
#         print("No jobs returned.")
#         return

#     for index, job in enumerate(jobs[:5], start=1):

#         print("=" * 80)
#         print(f"Job #{index}")
#         print("=" * 80)

#         print("Title      :", job.title)
#         print("Provider   :", job.provider.value)
#         print("Location   :", job.location)
#         print("Department :", job.department)
#         print("Job URL    :", job.job_url)
#         print("Posted At  :", job.posted_at)
#         print("Job ID     :", job.external_job_id)

#         print("\nDescription Preview:")

#         if job.description:
#             print(job.description[:300] + "...")
#         else:
#             print("No description")

#         print()


# if __name__ == "__main__":
#     main()

#ashby
# from app.service.ats.ashby_service import fetch_jobs


# def main():

#     careers_url = "https://jobs.ashbyhq.com/OpenAI"

#     print(f"Testing Ashby board: {careers_url}\n")

#     jobs = fetch_jobs(careers_url)

#     print(f"Found {len(jobs)} jobs\n")

#     if not jobs:
#         print("No jobs returned.")
#         return

#     for job in jobs[:5]:

#         print("=" * 80)
#         print("Title      :", job.title)
#         print("Provider   :", job.provider.value)
#         print("Location   :", job.location)
#         print("Department :", job.department)
#         print("Job URL    :", job.job_url)
#         print("Posted At  :", job.posted_at)
#         print("Job ID     :", job.external_job_id)
#         print()


# if __name__ == "__main__":
#     main()

"""
Manual verification script for workday_service.py.

Run this from your own machine/network (NOT in a sandboxed environment
with restricted outbound access) since it makes a real network call to
Workday's public CXS API.

Target company: Workday, Inc. itself.
Verified real careers URL: https://workday.wd5.myworkdayjobs.com/Workday
Corresponding CXS API:     https://workday.wd5.myworkdayjobs.com/wday/cxs/workday/Workday/jobs

This target was chosen because it is independently confirmed by a
third-party scraping tool's own documented example (Apify's Workday Job
Scraper actor uses this exact endpoint as its sample input), in addition
to a direct GET request against it returning HTTP 400 (endpoint exists,
requires POST) rather than 404 (endpoint does not exist).

IMPORTANT: run this yourself and inspect the printed output before
trusting this in production. The field names in workday_service.py were
sourced from third-party documentation, not confirmed against a live
payload in this environment -- if Workday's response shape differs from
what's assumed, job titles/locations may come back as None and the
field-parsing helpers will need adjusting.
"""

from app.service.ats.workday_service import fetch_jobs

CAREERS_URL = "https://workday.wd5.myworkdayjobs.com/Workday"


def main():
    print(f"Fetching jobs from: {CAREERS_URL}")
    print(f"Expected API call:  https://workday.wd5.myworkdayjobs.com/wday/cxs/workday/Workday/jobs")
    print("-" * 70)

    jobs = fetch_jobs(CAREERS_URL)

    print(f"Total jobs returned: {len(jobs)}")

    if not jobs:
        print(
            "No jobs returned. This could mean:\n"
            "  - The field names in workday_service.py don't match the "
            "live response shape (most likely if this is your first run)\n"
            "  - Workday's bot detection blocked the request\n"
            "  - The tenant/site in CAREERS_URL is no longer valid\n"
            "Add a print(response.json()) inside fetch_jobs() temporarily "
            "to inspect the raw payload."
        )
        return

    print("\nFirst 5 jobs:\n")
    for job in jobs[:5]:
        print(f"  Title:       {job.title}")
        print(f"  Location:    {job.location}")
        print(f"  Department:  {job.department}")
        print(f"  Posted:      {job.posted_at}")
        print(f"  Job URL:     {job.job_url}")
        print(f"  External ID: {job.external_job_id}")
        print()


if __name__ == "__main__":
    main()