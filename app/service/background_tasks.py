import json
from app.service.crawl_service import CrawlerService
from app.agents.extract_agent import ExtractAgent
from app.service.intel_service import IntelService
from app.utils.s3_uploader import S3Uploader
from app.service.instagram_oauth_service import InstagramService
from app.utils.progress_tracker import update_progress

crawler_service = CrawlerService()
extractor_agent = ExtractAgent()
intel_service = IntelService()
s3_uploader = S3Uploader()
instagram_service = InstagramService()


def run_background_crawler_pipeline(company_id: str, company_name: str, website_url: str, is_competitor: bool):
    """
    Runs entirely on an isolated background thread pool inside FastAPI.
    Crawls internal domains, cleans each page's text (tags/boilerplate/dupes
    removed), and packages it into S3. Downstream ETL/LLM steps consume this
    JSON separately — this function's only job is to produce clean, accurate
    per-page data and store it.
    """
    print(f"\n[ASYNC TASK START] Target: {company_name} | Partition Type: {'Competitor' if is_competitor else 'Admin'}")
    try:
        update_progress(company_id, 5, "Starting crawler")

        url_str = str(website_url)

        
        update_progress(company_id, 15, "Crawling website")

        print(f"  [1/2] Crawling website data footprints...")
        pages = crawler_service.crawl_site(url_str)

        print(f"  [2/2] Cleaning crawled pages (tags, boilerplate, duplicates)...")

        update_progress(company_id, 40, "Crawl completed")

        crawled_payload = {
            "company_name": company_name,
            "website_url": url_str,
            "total_pages_crawled": len(pages),
            "pages": []
        }


        update_progress(company_id, 50, "Cleaning data")


        for page in pages:
            # Handle if page is a Pydantic object or a raw dictionary safely
            p_dict = page.dict() if hasattr(page, "dict") else page

            page_url = p_dict.get("website_url") or url_str
            page_title = p_dict.get("title") or ""

            extracted = extractor_agent.extract(p_dict)

            social_links = extracted.get("social_links", {})


            crawled_payload["pages"].append({
                "url": page_url,
                "title": page_title,
                "emails": extracted.get("emails", []),
                "phones": extracted.get("phones", []),
                "social_links": social_links,
                "clean_text": extracted.get("clean_text", ""),
            })

        update_progress(company_id, 70, "Data cleaned")

        print(f"  Streaming internal crawled results to AWS S3...")

        if is_competitor:
            clean_comp_folder = company_name.strip().lower().replace(" ", "_")
            folder_segment = f"competitor/{clean_comp_folder}"
        else:
            folder_segment = "admin"

        s3_target_key = f"company/{company_id}/{folder_segment}/internal_crawl_data.json"
        json_string_data = json.dumps(crawled_payload, indent=4)

        s3_uploader.upload_string_to_s3(
            raw_text_data=json_string_data,
            s3_target_key=s3_target_key
        )

        # Instagram analysis (Competitors only)
        
        # if is_competitor:
        #     update_progress(company_id, 75, "Analyzing Instagram")

        #     instagram_service.process_instagram(
        #         company_id=company_id,
        #         company_name=company_name,
        #         crawled_pages=crawled_payload["pages"]
        #     )

        update_progress(company_id, 80, "Processing external intelligence")

        # Off-site intel stays here — separate concern from page cleaning above
        intel_service.process_offsite_intel(
            main_company_id=company_id,
            target_name=company_name,
            target_url=url_str,
            is_competitor=is_competitor
        )


        update_progress(company_id, 100, "Completed")
        print(f"[ASYNC TASK SUCCESS] Background storage synchronization complete for {company_name}!\n")

    except Exception as e:
        print(f"[ASYNC TASK ERROR] Background pipeline execution failed for {company_name}: {e}")
        update_progress(company_id, -1, f"Failed: {str(e)}")