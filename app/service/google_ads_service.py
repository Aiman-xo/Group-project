
from datetime import datetime
import os
import requests
from urllib.parse import urlparse
from typing import List, Optional, Dict, Any
from uuid import UUID
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.schemas.google_ads_schema import GoogleAdItem
from app.models.competetor_analyser  import GoogleAdsComparisonReport
from app.agents.google_ads_agent import GoogleAdsAgent

load_dotenv()


class GoogleAdsService:
    def __init__(self):
        self.serp_api_key = os.getenv("SERP_API_KEY", "")
        self.agent = GoogleAdsAgent()

    def _clean_search_term(self, term: str) -> str:
        """
        Cleans URLs into clean search terms (e.g. 'https://www.scaler.com/' -> 'scaler.com')
        """
        term = term.strip()
        if term.startswith("http://") or term.startswith("https://"):
            parsed = urlparse(term)
            domain = parsed.netloc or parsed.path
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        return term

    def _format_timestamp(self, ts) -> Optional[str]:
        """
        Converts raw Unix epoch timestamps to YYYY-MM-DD format strings.
        """
        if not ts:
            return None
        try:
            return datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return str(ts)

    def _analyze_rendering_strategy(self, item: dict, ad_url: Optional[str], ad_format: str) -> dict:
        """
        Analyzes raw SerpApi item fields to determine UI rendering strategy for React frontend.
        """
        media_url = item.get("media_url") or item.get("image_url") or item.get("thumbnail")
        youtube_id = item.get("youtube_id") or item.get("video_id")
        
        # Determine render type
        format_lower = str(ad_format).lower()
        if youtube_id or "video" in format_lower or "youtube" in format_lower:
            render_type = "youtube_embed"
            should_use_iframe = True
            embed_url = f"https://www.youtube.com/embed/{youtube_id}" if youtube_id else ad_url
        elif media_url or "image" in format_lower:
            render_type = "image"
            should_use_iframe = False
            embed_url = None
        elif ad_url and ("google.com" in ad_url or "adstransparency" in ad_url):
            render_type = "iframe"
            should_use_iframe = True
            embed_url = ad_url
        else:
            render_type = "text_card"
            should_use_iframe = False
            embed_url = None

        return {
            "media_url": media_url,
            "youtube_id": youtube_id,
            "render_type": render_type,
            "should_use_iframe": should_use_iframe,
            "embed_url": embed_url
        }

    def fetch_active_ads(self, search_term: str) -> List[GoogleAdItem]:
        """
        Fetches active ads from SerpApi and calculates UI rendering fields.
        """
        if not self.serp_api_key:
            print("[GOOGLE ADS SERVICE] Warning: SERP_API_KEY not set in .env")
            return []

        clean_term = self._clean_search_term(search_term)
        url = "https://serpapi.com/search.json"
        
        # 1. Attempt Google Ads Transparency Center search
        transparency_params = {
            "engine": "google_ads_transparency_center",
            "text": clean_term,
            "api_key": self.serp_api_key
        }

        try:
            response = requests.get(url, params=transparency_params, timeout=20)
            response.raise_for_status()
            data = response.json()

            ads_data = data.get("ad_creatives", []) or data.get("ad_results", [])
            parsed_ads = []

            for idx, item in enumerate(ads_data):
                ad_format = item.get("creative_format") or item.get("format") or "unknown"
                advertiser_id = item.get("advertiser_id")
                creative_id = str(item.get("ad_creative_id") or item.get("ad_id") or item.get("creative_id") or f"ad_{idx+1}")

                # Build URL
                ad_url = item.get("details_link") or item.get("ad_url") or item.get("ad_snapshot_url")
                if not ad_url and advertiser_id and creative_id and not creative_id.startswith("ad_"):
                    ad_url = f"https://adstransparency.google.com/advertiser/{advertiser_id}/creative/{creative_id}"

                headline = item.get("snippet") or item.get("title") or f"{ad_format.upper()} ad campaign by {clean_term}"

                # Calculate render specs for React frontend
                render_specs = self._analyze_rendering_strategy(item, ad_url, ad_format)

                parsed_ads.append(
                    GoogleAdItem(
                        ad_id=creative_id,
                        advertiser_id=advertiser_id,
                        advertiser_name=item.get("advertiser") or item.get("advertiser_name") or clean_term,
                        format=ad_format,
                        platform=item.get("platform") or "GOOGLE_ADS",
                        first_shown=self._format_timestamp(item.get("first_shown")),
                        last_shown=self._format_timestamp(item.get("last_shown")),
                        ad_url=ad_url,
                        media_url=render_specs["media_url"],
                        youtube_id=render_specs["youtube_id"],
                        headline_or_body=headline,
                        render_type=render_specs["render_type"],
                        should_use_iframe=render_specs["should_use_iframe"],
                        embed_url=render_specs["embed_url"]
                    )
                )

            # 2. Universal Organic Fallback if no paid ads are found
            if not parsed_ads:
                print(f"[GOOGLE ADS SERVICE] No active Google Ads found for '{search_term}'")
                return []

            return parsed_ads

        except Exception as e:
            print(f"[GOOGLE ADS SERVICE ERROR] Failed for '{search_term}': {e}")
            return []

    def get_or_analyze_ads(self, competitor_id: UUID, company_id: UUID | None, competitor_name: str, search_term: str, db: Session) -> Dict[str, Any]:
        """
        1. Checks DB for existing latest Google Ads report.
        2. If missing: fetches ads via SerpApi -> calls Agent for strategy insights -> saves report to DB.
        """
        # 1. DB CHECK FIRST
        existing_report = db.query(GoogleAdsComparisonReport).filter(
            GoogleAdsComparisonReport.competitor_id == competitor_id,
            GoogleAdsComparisonReport.is_latest == True
        ).first()

        if existing_report:
            return {
                "source": "database_cache",
                "report_id": existing_report.id,
                "competitor_id": existing_report.competitor_id,
                "competitor_name": existing_report.competitor_name,
                "active_ads_count": existing_report.active_ads_count,
                "ads": existing_report.raw_ads_data,
                "insights": {
                    "ad_copy_strategy_gap": existing_report.ad_copy_strategy_gap,
                    "media_format_gap": existing_report.media_format_gap,
                    "positioning_summary": existing_report.positioning_summary,
                    "recommendations": existing_report.recommendations
                },
                 "version": existing_report.version,
                "updated_at": existing_report.updated_at
            }

        # 2. IF NOT IN DB: Fetch live ads
        ads = self.fetch_active_ads(search_term=search_term)
        raw_ads_list = [ad.model_dump(mode="json") if hasattr(ad, "model_dump") else ad for ad in ads]

        # 3. Call AI Agent to analyze ad strategy
        ai_insights = self.agent.analyze_ad_strategy(search_term=search_term, raw_ads=raw_ads_list)

        latest_report = (
            db.query(GoogleAdsComparisonReport)
            .filter(
                GoogleAdsComparisonReport.competitor_id == competitor_id
            )
            .order_by(GoogleAdsComparisonReport.version.desc())
            .first()
        )

        next_version = (
            1 if latest_report is None
            else latest_report.version + 1
        )

        # 5. Persist to PostgreSQL / Supabase
        try:

            # Mark previous report as old
            db.query(GoogleAdsComparisonReport).filter(
                GoogleAdsComparisonReport.competitor_id == competitor_id,
                GoogleAdsComparisonReport.is_latest == True,
            ).update(
                {"is_latest": False},
                synchronize_session=False,
            )

            new_report = GoogleAdsComparisonReport(
                competitor_id=competitor_id,
                company_id=company_id,
                competitor_name=competitor_name,
                active_ads_count=len(raw_ads_list),
                raw_ads_data=raw_ads_list,
                ad_copy_strategy_gap=ai_insights.get("ad_copy_strategy_gap"),
                media_format_gap=ai_insights.get("media_format_gap"),
                positioning_summary=ai_insights.get("positioning_summary"),
                recommendations=ai_insights.get("recommendations"),
                version=next_version,
                is_latest=True,
            )

            db.add(new_report)
            db.commit()

        except Exception:
            db.rollback()
            raise

        # ==========================================================
        # STEP 6 : Return response
        # ==========================================================
        return {
            "source": "live_agent_scan",
            "report_id": new_report.id,
            "competitor_id": new_report.competitor_id,
            "competitor_name": new_report.competitor_name,
            "active_ads_count": new_report.active_ads_count,
            "ads": new_report.raw_ads_data,
            "insights": {
                "ad_copy_strategy_gap": new_report.ad_copy_strategy_gap,
                "media_format_gap": new_report.media_format_gap,
                "positioning_summary": new_report.positioning_summary,
                "recommendations": new_report.recommendations,
            },
            "version": new_report.version,
            "updated_at": new_report.updated_at,
        }