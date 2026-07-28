import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.agents.instagram_user_agent import InstagramAgent
from app.utils.s3_uploader import S3Uploader
from app.models.company_model import ProfileDataAnalyser
from app.service.admin_instagram_processor import (
    AdminInstagramProcessor
)


class InstagramService:

    def __init__(self):
        self.agent = InstagramAgent()
        self.s3 = S3Uploader()
        self.admin_instagram_processor = AdminInstagramProcessor()

    def process_instagram(
        self,
        db: Session,
        company_id,
        company_slug: str,
        company_name: str,
        instagram_url: str,
        is_competitor: bool = False,
    ) -> bool:

        if not instagram_url:
            print("[INSTAGRAM] No Instagram URL found.")
            return False

        print(f"[INSTAGRAM] Scraping {instagram_url}")

        # -----------------------------
        # Apify
        # -----------------------------

        profile = self.agent.scrape_profile(instagram_url)

        if not profile:
            print("[INSTAGRAM] No profile found.")
            return False

        # -----------------------------
        # S3 folder
        # -----------------------------

        if is_competitor:
            clean_comp_folder = (
                company_name
                .strip()
                .lower()
                .replace(" ", "_")
            )

            folder_segment = (
                f"competitor/{clean_comp_folder}"
            )

        else:
            folder_segment = "admin"

        s3_target_key = (
            f"social_media/{company_slug}/"
            f"{folder_segment}/"
            f"instagram_data.json"
        )

        # -----------------------------
        # JSON
        # -----------------------------

        json_string_data = json.dumps(
            profile,
            indent=4,
            default=str
        )

        # -----------------------------
        # Upload S3
        # -----------------------------

        self.s3.upload_string_to_s3(
            raw_text_data=json_string_data,
            s3_target_key=s3_target_key
        )

        print(
            f"[INSTAGRAM] Uploaded to S3: "
            f"{s3_target_key}"
        )

        # Only process admin Instagram data
        if not is_competitor:
            self.admin_instagram_processor.process(
                db=db,
                company_id=company_id,
                instagram_data=profile,
                source_file=s3_target_key,
            )

        return True