# import os
# import requests
# from typing import List
# from dotenv import load_dotenv
# from app.schemas.google_ads_schema import GoogleAdItem

# load_dotenv()

# class GoogleAdsService:
#     def __init__(self):
#         self.serper_api_key = os.getenv("SERPER_API_KEY", "")

#     def fetch_active_ads(self, search_term: str) -> List[GoogleAdItem]:
#         if not self.serper_api_key:
#             print("[GOOGLE ADS SERVICE] Warning: SERPER_API_KEY not set.")
#             return []

#         url = "https://google.serper.dev/search"
#         headers = {
#             "X-API-KEY": self.serper_api_key,
#             "Content-Type": "application/json"
#         }

#         # Dynamic query: Works for any industry (EdTech, E-commerce, SaaS, Real Estate, etc.)
#         payload = {
#             "q": search_term,
#             "gl": "in"  # Country code
#         }

#         try:
#             response = requests.post(url, headers=headers, json=payload, timeout=15)
#             response.raise_for_status()
#             data = response.json()

#             parsed_ads = []
            
#             # 1. Capture live sponsored Google Ads (If running active paid campaigns)
#             ads_list = data.get("ads", [])
#             for idx, ad in enumerate(ads_list):
#                 parsed_ads.append(
#                     GoogleAdItem(
#                         ad_id=f"ad_search_{idx+1}",
#                         advertiser_name=ad.get("title") or search_term,
#                         format="text/search_ad",
#                         platform="GOOGLE_SEARCH",
#                         ad_url=ad.get("link"),
#                         headline_or_body=f"{ad.get('title', '')} - {ad.get('snippet', '')}"
#                     )
#                 )

#             # 2. Universal Fallback: If company has NO active paid ads right now, 
#             # capture their core brand presence / search footprint
#             if not parsed_ads:
#                 organic_results = data.get("organic", [])[:3]
#                 for idx, org in enumerate(organic_results):
#                     parsed_ads.append(
#                         GoogleAdItem(
#                             ad_id=f"brand_footprint_{idx+1}",
#                             advertiser_name=search_term,
#                             format="brand_footprint",
#                             format_type="ORGANIC",
#                             platform="GOOGLE_SEARCH",
#                             ad_url=org.get("link"),
#                             headline_or_body=f"{org.get('title', '')} - {org.get('snippet', '')}"
#                         )
#                     )

#             return parsed_ads

#         except Exception as e:
#             print(f"[GOOGLE ADS SERVICE ERROR] Failed for '{search_term}': {e}")
#             return []


from datetime import datetime
import os
import requests
from urllib.parse import urlparse
from typing import List, Optional
from dotenv import load_dotenv
from app.schemas.google_ads_schema import GoogleAdItem

load_dotenv()

class GoogleAdsService:
    def __init__(self):
        self.serp_api_key = os.getenv("SERP_API_KEY", "")

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
#-------------------------------------------------------------------
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
#-------------------------------------------------------------------
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
    #-------------------------------------------------------------------

    def fetch_active_ads(self, search_term: str) -> List[GoogleAdItem]:
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
                # Format
                ad_format = item.get("creative_format") or item.get("format") or "unknown"
                
                # Advertiser & Creative IDs
                advertiser_id = item.get("advertiser_id")
                creative_id = str(item.get("ad_creative_id") or item.get("ad_id") or item.get("creative_id") or f"ad_{idx+1}")

                # Build URL (SerpApi uses 'details_link'; construct dynamically if missing)
                ad_url = item.get("details_link") or item.get("ad_url") or item.get("ad_snapshot_url")
                if not ad_url and advertiser_id and creative_id and not creative_id.startswith("ad_"):
                    ad_url = f"https://adstransparency.google.com/advertiser/{advertiser_id}/creative/{creative_id}"

                # Extract headline/body/snippet or create fallback string
                headline = item.get("snippet") or item.get("title") or f"{ad_format.upper()} ad campaign by {clean_term}"

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
                        headline_or_body=headline
                    )
                )

            # 2. Universal Organic Fallback if no paid ads are found
            if not parsed_ads:
                search_params = {
                    "engine": "google",
                    "q": clean_term,
                    "gl": "in",
                    "api_key": self.serp_api_key
                }
                search_res = requests.get(url, params=search_params, timeout=15)
                search_data = search_res.json()
                
                organic_results = search_data.get("organic_results", [])[:3]
                for idx, org in enumerate(organic_results):
                    parsed_ads.append(
                        GoogleAdItem(
                            ad_id=f"brand_footprint_{idx+1}",
                            advertiser_id=None,
                            advertiser_name=clean_term,
                            format="brand_footprint",
                            platform="GOOGLE_SEARCH",
                            first_shown=None,
                            last_shown=None,
                            ad_url=org.get("link"),
                            headline_or_body=f"{org.get('title', '')} - {org.get('snippet', '')}"
                        )
                    )

            return parsed_ads

        except Exception as e:
            print(f"[GOOGLE ADS SERVICE ERROR] Failed for '{search_term}': {e}")
            return []