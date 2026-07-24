import json

from app.agents.instagram_user_agent import InstagramAgent
from app.utils.s3_uploader import S3Uploader


class InstagramService:

    def __init__(self):
        self.agent = InstagramAgent()
        self.s3 = S3Uploader()

    def process_instagram(
        self,
        company_id: str,
        company_name: str,
        crawled_pages: list | None = None,
        instagram_url: str | None = None,
    ) -> bool:
        """
        Process Instagram intelligence.

        Priority:
        1. Manual instagram_url
        2. Auto-detect from crawled pages
        """

        # Auto detect Instagram URL
        if not instagram_url and crawled_pages:

            for page in crawled_pages:

                social_links = page.get("social_links", {})

                if social_links.get("instagram"):
                    instagram_url = social_links["instagram"]
                    break

        if not instagram_url:
            print("[INSTAGRAM] No Instagram URL found.")
            return False

        print(f"[INSTAGRAM] Scraping {instagram_url}")

        profile = self.agent.scrape_profile(instagram_url)

        if not profile:
            print("[INSTAGRAM] No profile found.")
            return False

        folder = company_name.strip().lower().replace(" ", "_")

        key = (
            f"company/{company_id}/"
            f"competitor/{folder}/"
            f"instagram_data.json"
        )

        self.s3.upload_string_to_s3(
            raw_text_data=json.dumps(profile, indent=4),
            s3_target_key=key
        )

        print("[INSTAGRAM] Uploaded to S3")

        return True