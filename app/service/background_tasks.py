import json
import asyncio
from app.service.crawl_service import CrawlerService
from app.agents.extract_agent import ExtractAgent
from app.service.intel_service import IntelService
from app.utils.s3_uploader import S3Uploader  # <-- Imported your uploader utility

# Initialize core microservices cleanly outside the loop
crawler_service = CrawlerService()
extractor_agent = ExtractAgent()
intel_service = IntelService()
s3_uploader = S3Uploader()  # <-- Created S3 client instance

def run_background_crawler_pipeline(company_id: str, company_name: str, website_url: str, is_competitor: bool):
    """
    Runs entirely on an isolated background thread pool inside FastAPI.
    Crawls internal domains, extracts capabilities matrix data, and packages everything into S3.
    """
    print(f"\n[ASYNC TASK START] Target: {company_name} | Partition Type: {'Competitor' if is_competitor else 'Admin'}")
    try:
        url_str = str(website_url)
        
        # 1. Core domain crawling loop
        print(f"  [1/3] Crawling website data footprints...")
        pages = crawler_service.crawl_site(url_str)
        
        # 2. Extract structural nodes and match schema path architecture
        print(f"  [2/3] Extracting capabilities and compiling crawl data...")
        all_capabilities = set()
        
        crawled_payload = {
            "company_name": company_name,
            "website_url": url_str,
            "total_pages_crawled": len(pages),
            "pages": []
        }
        
        for page in pages:
            # Handle if page is a Pydantic object or a raw dictionary safely
            p_dict = page.dict() if hasattr(page, "dict") else page
            
            # Use 'website_url' to match your schema exactly
            page_url = p_dict.get("website_url") or url_str
            page_title = p_dict.get("title") or ""
            page_desc = p_dict.get("meta_description") or ""
            page_headings = p_dict.get("headings") or []
            
            # Fallback: Feed title/headings text to the extractor if raw HTML isn't in your schema
            text_context = f"Title: {page_title}\nDescription: {page_desc}\nHeadings: {' | '.join(page_headings)}"
            
            extracted = extractor_agent.extract(text_context)
            all_capabilities.update(extracted.get("capabilities", []))
            
            crawled_payload["pages"].append({
                "url": page_url,
                "title": page_title,
                "headings": page_headings,
                "extracted_capabilities": extracted.get("capabilities", [])
            })
            
        print(f"  [2.5/3] Streaming internal crawled results to AWS S3...")
        
        # Match your exact folder path pattern inside your IntelService logic
        if is_competitor:
            clean_comp_folder = company_name.strip().lower().replace(" ", "_")
            folder_segment = f"competitor/{clean_comp_folder}"
        else:
            folder_segment = "admin"
            
        s3_target_key = f"company/{company_id}/{folder_segment}/internal_crawl_data.json"
        
        # Convert crawl dict to json string
        json_string_data = json.dumps(crawled_payload, indent=4)
        
        # Send internal crawl payload to S3!
        s3_uploader.upload_string_to_s3(
            raw_text_data=json_string_data,
            s3_target_key=s3_target_key
        )

        # 3. Stream off-site reviews/leaks straight to S3 data lake partitions
        print(f"  [3/3] Fetching off-site social signals (Google & Reddit fallback nodes)...")
        intel_service.process_offsite_intel(
            main_company_id=company_id,
            target_name=company_name,
            target_url=url_str,
            is_competitor=is_competitor
        )
        print(f"[ASYNC TASK SUCCESS] Background storage synchronization complete for {company_name}!\n")
        
    except Exception as e:
        print(f"[ASYNC TASK ERROR] Background pipeline execution failed for {company_name}: {e}")