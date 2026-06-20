import json
from urllib.parse import urlparse
from app.service.crawl_service import CrawlerService
from app.agents.extract_agent import ExtractAgent

crawler = CrawlerService()
extractor = ExtractAgent()

TARGET_URL = "https://gemsasc.ac.in/"
domain = urlparse(TARGET_URL).netloc.replace("www.", "")
print(f"\n[+] STARTING UNIVERSAL SEPARATED VERIFICATION: Profiling {domain}...")

pages = crawler.crawl_site(TARGET_URL)
print(f"    Pages successfully crawled: {len(pages)}")

all_emails = set()
all_phones = set()
all_tech_stacks = set()

all_capabilities = set()
all_deliverables = set()
all_people = set()

all_social_links = {
    "linkedin": set(), "github": set(), "twitter": set(),
    "facebook": set(), "instagram": set(), "youtube": set()
}

for page in pages:
    extracted = extractor.extract(page["html"])

    all_capabilities.update(extracted.get("capabilities", []))
    all_deliverables.update(extracted.get("deliverables", []))
    all_people.update(extracted.get("associated_people", []))
        
    all_emails.update(extracted.get("emails", []))
    all_phones.update(extracted.get("phones", []))
    
    if "tech_stack_footprints" in page:
        all_tech_stacks.update(page["tech_stack_footprints"])

    for platform, links in extracted.get("social_links", {}).items():
        all_social_links[platform].update(links)

raw_ingestion_payload = {
    "data_source": "website_crawler",
    "metadata": {
        "root_url": TARGET_URL,
        "domain": domain,
    },
    "contact_info": {
        "emails": sorted(list(all_emails)),
        "phones": sorted(list(all_phones))
    },
    "social_presence": {
        platform: sorted(list(links))
        for platform, links in all_social_links.items() if links
    },
    "capabilities": sorted(list(all_capabilities)),
    "products_or_courses": sorted(list(all_deliverables)),  
    "associated_staff": sorted(list(all_people)),
    "operational_infrastructure": {
        "detected_marketing_tech": sorted(list(all_tech_stacks))
    }
}

local_filename = f"raw_{domain}.json"
with open(local_filename, "w") as f:
    json.dump(raw_ingestion_payload, f, indent=2)

print("\n" + "="*25 + " UNIVERSAL PROFILE VERIFICATION " + "="*25)
print(f"File Saved Locally: {local_filename}")
print(f"Root Domain:        {raw_ingestion_payload['metadata']['domain']}")

print("\nExtracted Academic Staff/People (Isolated Noise):")
for person in raw_ingestion_payload['associated_staff']:
    print(f"  [Staff] {person}")

print("\nExtracted Structural Matrix (Departments / Facilities):")
for cap in raw_ingestion_payload['capabilities']:
    print(f"  - {cap}")

print("\nExtracted Offerings Matrix (Courses / Products / Tracks):")
if raw_ingestion_payload['products_or_courses']:
    for item in raw_ingestion_payload['products_or_courses']:
        print(f"  * {item}")
print("="*76 + "\n")