import re
import requests
from bs4 import BeautifulSoup
import json

class GoogleReviewAgent:
    """
    Mines search engine descriptions for aggregated trust metrics dynamically 
    across multiple platforms (AmbitionBox, Glassdoor, Indeed, Facebook, etc.)
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.constructive_keywords = ["average", "moderate", "low", "but", "however", "satisfaction", "disappointed", "poor", "issue", "1.0", "2.0", "3.0"]
        self.entertainment_noise = ["netflix", "bridgerton", "season", "episode", "drama", "romantic", "fairytale", "tv show", "cast"]

    def extract_summary(self, company_name: str) -> dict:
        query = f"{company_name.strip()} reviews"
        url = f"https://html.duckduckgo.com/html/?q={query}"
        
        payload = {
            "company_name": company_name,
            "rating_score": "N/A",
            "total_reviews": 0,
            "source": "multi_platform_fallback",  # Dynamic fallback label
            "extracted_url": url,
            "insights": {
                "positive_or_general": [],
                "constructive_or_negative": []
            }
        }

        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                payload["status"] = "error"
                return payload

            soup = BeautifulSoup(response.text, "lxml")
            snippets = soup.find_all("a", class_="result__snippet")
            
            highest_review_count = 0
            detected_sources = []
            
            for snippet in snippets:
                text = snippet.get_text()
                
                # Filter out apps and entertainment noise
                if any(word in text.lower() for word in ["app", "download", "apk", "google play"]) or any(word in text.lower() for word in self.entertainment_noise):
                    continue

                # --- 1. Identify Source Dynamically ---
                for platform in ["ambitionbox", "glassdoor", "indeed", "facebook", "mouthshut", "google"]:
                    if platform in text.lower() and platform not in detected_sources:
                        detected_sources.append(platform)

                # --- 2. Universal Rating Extract (Handles 3.7/5, 4.2 stars, Rating: 4) ---
                rating_match = re.search(
                    r"(?:rating[:\-]?\s*|rated\s*)([1-5]\.\d|[1-5])(?:/5)?|"
                    r"([1-5]\.\d|[1-5])\s*(?:out of 5|/5|stars)|"
                    r"([1-5]\.\d)\s*based on", 
                    text, re.I
                )
                
                # --- 3. Universal Count Extract ---
                count_match = re.search(r"\b(\d+)\b(?:\s+\w+){0,4}\s+(?:reviews|votes|ratings|voters)", text, re.I)
                
                # Checks if it looks like an authoritative structural summary phrase
                is_overall_phrase = any(phrase in text.lower() for phrase in ["is rated", "overall rating", "overall score", "stars on", "reviews and salaries"])

                if rating_match:
                    score = rating_match.group(1) or rating_match.group(2) or rating_match.group(3)
                    if score:
                        if is_overall_phrase or payload["rating_score"] == "N/A":
                            payload["rating_score"] = score.strip()
                
                if count_match:
                    current_count = int(count_match.group(1))
                    if current_count > highest_review_count:
                        highest_review_count = current_count
                        payload["total_reviews"] = highest_review_count

            # --- 4. Sentiment Sorting & Analysis ---
            for snippet in snippets:
                text_clean = snippet.get_text().strip()
                if len(text_clean) <= 20 or any(word in text_clean.lower() for word in self.entertainment_noise):
                    continue

                if any(word in text_clean.lower() for word in self.constructive_keywords):
                    if text_clean not in payload["insights"]["constructive_or_negative"]:
                        payload["insights"]["constructive_or_negative"].append(text_clean)
                else:
                    if text_clean not in payload["insights"]["positive_or_general"]:
                        payload["insights"]["positive_or_general"].append(text_clean)

            # Update status and source signature output cleanly
            if payload["rating_score"] != "N/A":
                payload["status"] = "success"
                if detected_sources:
                    payload["source"] = f"aggregated ({', '.join(detected_sources)})"

        except Exception as e:
            payload["status"] = "error"

        return payload

if __name__ == "__main__":
    agent = GoogleReviewAgent()
    output_data = agent.extract_summary("brototype")
    print(json.dumps(output_data, indent=4))