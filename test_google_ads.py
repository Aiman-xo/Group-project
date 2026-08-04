# test_google_ads.py
import json
from app.agents.google_ads_agent import GoogleAdsAgent
from app.models.competetor_analyser import GoogleAdsComparisonReport

def test_ads():
    agent = GoogleAdsAgent()
    
    # You can pass website_url or company_name
    target_url = "https://bridgeon.in/"
    target_name = "Bridgeon"
    
    print(f"\n--- Testing Google Ads Fetch for URL: {target_url} ---")
    
    results = agent.get_ad_intelligence(
        website_url=target_url, 
        company_name=target_name
    )
    
    print(f"\n[TERMINAL OUTPUT] Total Ads Found: {len(results)}\n")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    test_ads()

#If the company is running active paid Google Search Ads, format will be "text/search_ad".

#If they aren't running paid ads at that moment, format will be "brand_footprint".