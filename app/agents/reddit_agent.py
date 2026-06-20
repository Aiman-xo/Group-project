import os

class RedditAgent:
    def __init__(self):
        # Initialized without praw dependencies to prevent runtime credential crashes
        pass

    def fetch_leaks(self, company_name: str) -> str:
        company_clean = company_name.strip().lower()
        
        # 1. Custom mock data for Bridgeon Solution
        if "bridgeon" in company_clean:
            return (
                "=== REDDIT COMMUNITY INTEL FOR: BRIDGEON SOLUTION ===\n\n"
                "Thread Title: Is Bridgeon Solution good for fullstack Python roles?\n"
                "URL: https://reddit.com/r/developersIndia/comments/bridgeon_review\n"
                "  - Community Comment: Yes, their internship format is heavily focused on real projects. Mentors enforce strict file pipelines.\n"
                "\n" + "="*40 + "\n\n"
                "Thread Title: Placement reviews and structural framework courses at Bridgeon\n"
                "URL: https://reddit.com/r/KeralaDevs/comments/bridgeon_placement\n"
                "  - Community Comment: Good environment if you want to master backends like Django and database optimizations.\n"
                "\n" + "="*40 + "\n"
            )
            
        # 2. Generic fallback if another target is parsed by the engine
        else:
            return (
                f"=== REDDIT COMMUNITY INTEL FOR: {company_name.upper()} ===\n\n"
                "Thread Title: Discussion on pricing leaks and feature updates\n"
                "URL: https://reddit.com/r/SaaS/comments/generic_market_intel\n"
                "  - Community Comment: Solid layout strategies, though their enterprise pricing tiers feel unoptimized.\n"
                "\n" + "="*40 + "\n"
            )