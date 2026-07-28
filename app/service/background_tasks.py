import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from app.service.crawl_service import CrawlerService
from app.agents.extract_agent import ExtractAgent
from app.service.intel_service import IntelService
from app.utils.s3_uploader import S3Uploader
from app.utils.progress_tracker import update_progress
from app.agents import ats_agent

crawler_service = CrawlerService()
extractor_agent = ExtractAgent()
intel_service = IntelService()
s3_uploader = S3Uploader()


def _extract_all_hrefs(raw_html: str, base_url: str = "") -> list[str]:
    """Extracts and converts all relative hrefs into absolute URLs."""
    if not raw_html:
        return []
    
    soup = BeautifulSoup(raw_html, "lxml")
    extracted_links = []
    
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        
        # Convert relative link (/jobs) to absolute link (https://company.com/jobs)
        full_url = urljoin(base_url, href) if base_url else href
        extracted_links.append(full_url)
        
    return extracted_links


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

        print(f"  [1/3] Crawling website data footprints...")
        pages = crawler_service.crawl_site(url_str)
        #test
        print(f"  Total pages crawled: {len(pages)}")

        print(f"  [2/3] Cleaning crawled pages (tags, boilerplate, duplicates)...")

        update_progress(company_id, 40, "Crawl completed")

        crawled_payload = {
            "company_name": company_name,
            "website_url": url_str,
            "total_pages_crawled": len(pages),
            "pages": [],
        }

        detected_ats_urls = set()

        if ats_agent.detect_provider(url_str) != ats_agent.ATSProvider.UNKNOWN:
            detected_ats_urls.add(url_str)


        update_progress(company_id, 50, "Cleaning data")

        for page in pages:
            # Handle if page is a Pydantic object or a raw dictionary safely
            p_dict = page.dict() if hasattr(page, "dict") else page

            page_url = p_dict.get("website_url") or url_str
            page_title = p_dict.get("title") or ""

            extracted = extractor_agent.extract(p_dict)

            crawled_payload["pages"].append({
                "url": page_url,
                "title": page_title,
                "emails": extracted.get("emails", []),
                "phones": extracted.get("phones", []),
                "social_links": extracted.get("social_links", {}),
                "clean_text": extracted.get("clean_text", ""),
                "careers_page": extracted.get("careers_page", False),
            })



            # Check if this page URL itself is an ATS board
            if ats_agent.detect_provider(page_url) != ats_agent.ATSProvider.UNKNOWN:
                detected_ats_urls.add(page_url)

            # Check outbound links on careers pages for ATS boards
            if extracted.get("careers_page"):
                raw_html = p_dict.get("html", "")
                for link in _extract_all_hrefs(raw_html,base_url=page_url):
                    if ats_agent.detect_provider(link) != ats_agent.ATSProvider.UNKNOWN:
                        detected_ats_urls.add(link)

        # Execute ATS Agent job extraction for all detected ATS portals
        print("  [3/3] Detecting ATS career boards and fetching job postings...")
        update_progress(company_id, 65, "Fetching ATS job postings")
        
        all_ats_jobs = []
        if detected_ats_urls:
            print(f"      Found {len(detected_ats_urls)} ATS career board(s).")
                    
            for ats_url in detected_ats_urls:
                try:
                    jobs = ats_agent.fetch_jobs(ats_url)

                    for job in jobs:
                        if hasattr(job, "model_dump"):
                            all_ats_jobs.append(job.model_dump(mode="json"))
                        elif hasattr(job, "dict"):
                            all_ats_jobs.append(job.dict())
                        else:
                            all_ats_jobs.append(job)

                except Exception as e:
                    print(f"ATS fetch failed for {ats_url}: {e}")

            print(f"  Extracted {len(all_ats_jobs)} job postings from ATS integrations.")
        else:
            print("      No supported ATS career boards detected.")   
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

      
        ats_payload = {
                "company_name": company_name,
                "website_url": url_str,
                "ats_urls": list(detected_ats_urls),
                "total_jobs": len(all_ats_jobs),
                "jobs": all_ats_jobs,
            }

        ats_key = f"company/{company_id}/{folder_segment}/ats_jobs.json"

        s3_uploader.upload_string_to_s3(
                raw_text_data=json.dumps(ats_payload, indent=4),
                s3_target_key=ats_key
            )

        print(f"  ATS job data uploaded to S3 ({len(all_ats_jobs)} jobs).")

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