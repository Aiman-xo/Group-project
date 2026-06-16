from app.service.crawl_service import CrawlerService
from app.agents.extract_agent import ExtractAgent

crawler = CrawlerService()
extractor = ExtractAgent()

pages = crawler.crawl_site(
    "https://www.python.org"
)

print(f"Pages crawled: {len(pages)}")

all_emails = set()
all_phones = set()

all_social_links = {
    "linkedin": set(),
    "github": set(),
    "twitter": set(),
    "facebook": set(),
    "instagram": set(),
    "youtube": set(),
}

all_job_roles = set()

for page in pages:

    extracted = extractor.extract(
        page["html"],
        page["website_url"]
    )

    all_job_roles.update(
        extracted["job_roles"]
    )
    

    all_emails.update(
        extracted["emails"]
    )

    all_phones.update(
        extracted["phones"]
    )

    for platform, links in extracted["social_links"].items():
        all_social_links[platform].update(
            links
        )

result = {
    "emails": sorted(all_emails),
    "phones": sorted(all_phones),
    "social_links": {
        platform: sorted(links)
        for platform, links in all_social_links.items()
        if links
    },
    "job_roles": sorted(all_job_roles)
}

print("\n===== COMPANY PROFILE =====")
print(result)