import os
from app.agents.google_agent import GoogleReviewAgent
from app.agents.reddit_agent import RedditAgent
from app.utils.s3_uploader import S3Uploader

class IntelService:
    def __init__(self):
        self.google_agent = GoogleReviewAgent()
        self.reddit_agent = RedditAgent()
        self.s3_storage = S3Uploader()

    def process_offsite_intel(self, main_company_id: str, target_name: str, target_url: str = "", is_competitor: bool = False):
        """
        main_company_id: The ID of the logged-in user's company (e.g., company_bridgeon)
        target_name: The company being looked up right now (Main company or a competitor)
        target_url: The web link passed from your dashboard input form
        """
        if is_competitor:
            # Generate a clean sub-folder name from the competitor name (e.g., alpha_academy)
            clean_comp_folder = target_name.strip().lower().replace(" ", "_")
            folder_segment = f"competitor/{clean_comp_folder}"
        else:
            folder_segment = "admin"
            
        print(f"\n  [+] Executing External Scrapers for: {target_name} ({target_url if target_url else 'No URL Required'})")
        print(f"  [+] Target Data Lake Path: company/{main_company_id}/{folder_segment}/")
        
        # 1. Process Google Places Integration
        google_json_data = self.google_agent.extract_summary(target_name)
        
        import json
        google_data_str = json.dumps(google_json_data, indent=4)
        google_s3_key = f"company/{main_company_id}/{folder_segment}/review_and_rating.txt"
        self.s3_storage.upload_string_to_s3(google_data_str, google_s3_key)
            
        # 2. Process Reddit Intelligence Extraction
        reddit_data = self.reddit_agent.fetch_leaks(target_name)
        reddit_s3_key = f"company/{main_company_id}/{folder_segment}/pricing_and_leaks.txt"
        self.s3_storage.upload_string_to_s3(reddit_data, reddit_s3_key)
        
        print(f"    [✓] All target data files safely streamed to S3 bucket location.")