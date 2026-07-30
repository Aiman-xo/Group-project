# from typing import List, Dict, Any
# from app.service.google_ads_service import GoogleAdsService
# from urllib.parse import urlparse


# class GoogleAdsAgent:
#     def __init__(self):
#         self.service = GoogleAdsService()

#     def _extract_domain_or_name(self, website_url: str = "", company_name: str = "") -> str:
#         """Extracts clean brand term or domain for ad lookup."""
#         if website_url:
#             # e.g., 'https://www.brototype.com/courses' -> 'brototype'
#             netloc = urlparse(website_url).netloc or website_url
#             clean_domain = netloc.replace("www.", "").split(".")[0]
#             if clean_domain:
#                 return clean_domain
        
#         return company_name

#     def get_ad_intelligence(self, website_url: str = "", company_name: str = "") -> List[Dict[str, Any]]:
#         target_term = self._extract_domain_or_name(website_url=website_url, company_name=company_name)
        
#         ads = self.service.fetch_active_ads(search_term=target_term)
#         return [ad.model_dump(mode="json") for ad in ads]

from typing import List, Dict, Any
from urllib.parse import urlparse
from app.service.google_ads_service import GoogleAdsService

class GoogleAdsAgent:
    def __init__(self):
        self.service = GoogleAdsService()

    def _extract_domain_or_name(self, website_url: str = "", company_name: str = "") -> str:
        """Extracts clean domain (e.g. 'brototype.com') or falls back to company name."""
        if website_url:
            website_url = website_url.strip()
            # Ensure URL has scheme for urlparse
            if not website_url.startswith(("http://", "https://")):
                website_url = f"https://{website_url}"
                
            netloc = urlparse(website_url).netloc or website_url
            # Clean www. prefix but keep the full domain name (e.g., 'scaler.com')
            clean_domain = netloc.replace("www.", "").strip("/")
            
            if clean_domain:
                return clean_domain

        return company_name.strip()

    def get_ad_intelligence(self, website_url: str = "", company_name: str = "") -> List[Dict[str, Any]]:
        target_term = self._extract_domain_or_name(website_url=website_url, company_name=company_name)
        
        if not target_term:
            print("[GOOGLE ADS AGENT] Warning: Neither website_url nor company_name was provided.")
            return []

        ads = self.service.fetch_active_ads(search_term=target_term)
        
        # Safely convert Pydantic models to JSON dictionaries
        return [ad.model_dump(mode="json") for ad in ads]