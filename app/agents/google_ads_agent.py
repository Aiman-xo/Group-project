# from typing import List, Dict, Any
# from urllib.parse import urlparse
# from app.service.google_ads_service import GoogleAdsService

# class GoogleAdsAgent:
#     def __init__(self):
#         self.service = GoogleAdsService()

#     def _extract_domain_or_name(self, website_url: str = "", company_name: str = "") -> str:
#         """Extracts clean domain (e.g. 'brototype.com') or falls back to company name."""
#         if website_url:
#             website_url = website_url.strip()
#             # Ensure URL has scheme for urlparse
#             if not website_url.startswith(("http://", "https://")):
#                 website_url = f"https://{website_url}"
                
#             netloc = urlparse(website_url).netloc or website_url
#             # Clean www. prefix but keep the full domain name (e.g., 'scaler.com')
#             clean_domain = netloc.replace("www.", "").strip("/")
            
#             if clean_domain:
#                 return clean_domain

#         return company_name.strip()

#     def get_ad_intelligence(self, website_url: str = "", company_name: str = "") -> List[Dict[str, Any]]:
#         target_term = self._extract_domain_or_name(website_url=website_url, company_name=company_name)
        
#         if not target_term:
#             print("[GOOGLE ADS AGENT] Warning: Neither website_url nor company_name was provided.")
#             return []

#         ads = self.service.fetch_active_ads(search_term=target_term)
        
#         # Safely convert Pydantic models to JSON dictionaries
#         return [ad.model_dump(mode="json") for ad in ads]

import json
import logging
from typing import List, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class GoogleAdsAgent:
    """
    Agent responsible for analyzing competitor ad creatives, fetching raw intelligence,
    and generating strategy insights (ad copy gaps, media formats, positioning summaries).
    """

    def _extract_domain_or_name(self, website_url: str = "", company_name: str = "") -> str:
        """Extracts clean domain (e.g. 'brototype.com') or falls back to company name."""
        if website_url:
            website_url = website_url.strip()
            if not website_url.startswith(("http://", "https://")):
                website_url = f"https://{website_url}"
                
            netloc = urlparse(website_url).netloc or website_url
            clean_domain = netloc.replace("www.", "").strip("/")
            
            if clean_domain:
                return clean_domain

        return company_name.strip()

    def get_ad_intelligence(self, website_url: str = "", company_name: str = "") -> List[Dict[str, Any]]:
        """
        Fetches active ads directly via GoogleAdsService for quick testing/standalone usage.
        """
        # Lazy import inside method to completely prevent circular imports
        from app.service.google_ads_service import GoogleAdsService

        target_term = self._extract_domain_or_name(website_url=website_url, company_name=company_name)
        
        if not target_term:
            logger.warning("[GOOGLE ADS AGENT] Neither website_url nor company_name was provided.")
            return []

        service = GoogleAdsService()
        ads = service.fetch_active_ads(search_term=target_term)
        
        # Safely convert Pydantic models to JSON dictionaries
        return [ad.model_dump(mode="json") if hasattr(ad, "model_dump") else ad for ad in ads]

    def analyze_ad_strategy(self, search_term: str, raw_ads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes raw ad items to generate competitive insights.
        Called by GoogleAdsService.get_or_analyze_ads().
        """
        if not raw_ads:
            return {
                "ad_copy_strategy_gap": f"No active paid ad campaigns detected for '{search_term}'. They may rely purely on organic search or social media traffic.",
                "media_format_gap": "No creative formats (image/video) detected.",
                "positioning_summary": f"Minimal digital ad presence for '{search_term}'.",
                "recommendations": [
                    f"Launch targeted Google Search Ads capturing high-intent search keywords for {search_term}.",
                    "Build responsive search ads (RSAs) emphasizing USPs, pricing, or trial offers."
                ]
            }

        formats_found = list({ad.get("format", "unknown") for ad in raw_ads})
        render_types = list({ad.get("render_type", "text_card") for ad in raw_ads})
        
        has_video = "youtube_embed" in render_types or any("video" in f.lower() for f in formats_found)
        has_image = "image" in render_types or any("image" in f.lower() for f in formats_found)

        if has_video and has_image:
            media_gap = f"{search_term} utilizes a balanced mix of both image banner and video creative formats across Google Display/YouTube."
        elif has_video:
            media_gap = f"{search_term} heavily favors video campaigns, leaving display banner placements open for competitors."
        elif has_image:
            media_gap = f"{search_term} relies primarily on static/image ads. They currently lack video campaigns on YouTube/Google Display."
        else:
            media_gap = f"{search_term} primarily uses standard search/text ad copies without rich visual assets."

        snippets = [ad.get("headline_or_body", "") for ad in raw_ads if ad.get("headline_or_body")]
        combined_text = " | ".join(snippets[:5]) if snippets else "Generic promotion"

        ad_copy_gap = f"Analyzed {len(raw_ads)} active ad creative(s). Key messaging focus: '{combined_text[:150]}...'"
        positioning = f"Active market presence with primary ad formats: {', '.join(formats_found)}."

        recommendations = [
            f"Differentiate ad copy by targeting pain points missed in {search_term}'s headline messaging.",
            "Test video ads if competitor is only using image formats (or vice-versa).",
            "Optimize landing page conversions to outrank their domain on Google Search."
        ]

        return {
            "ad_copy_strategy_gap": ad_copy_gap,
            "media_format_gap": media_gap,
            "positioning_summary": positioning,
            "recommendations": recommendations
        }