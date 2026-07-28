from apify_client import ApifyClient
from app.core.config import APIFY_TOKEN


class InstagramAgent:
    """
    Handles communication with the Apify Instagram Scraper.
    Responsible only for fetching and cleaning Instagram data.
    """

    ACTOR_ID = "apify/instagram-scraper"

    def __init__(self):
        self.client = ApifyClient(APIFY_TOKEN)

    def scrape_profile(self, instagram_url: str) -> dict | None:
        """
        Scrape Instagram profile and return cleaned data.
        """

        run_input = {
            "addParentData": False,
            "directUrls": [instagram_url],
            "resultsLimit": 1,
            "resultsType": "details",
            "searchLimit": 10,
            "searchType": "hashtag"
        }

        run = self.client.actor(self.ACTOR_ID).call(run_input=run_input)

        dataset_id = run["defaultDatasetId"]

        items = list(
            self.client.dataset(dataset_id).iterate_items()
        )

        if not items:
            return None

        profile = items[0]

        # Keep only latest 30 posts
        latest_posts = sorted(
            profile.get("latestPosts", []),
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:30]

        # Keep only useful fields from each post
        cleaned_posts = []

        for post in latest_posts:
            cleaned_posts.append({
                "id": post.get("id"),
                "shortCode": post.get("shortCode"),
                "type": post.get("type"),
                "productType": post.get("productType"),
                "caption": post.get("caption"),
                "hashtags": post.get("hashtags", []),
                "mentions": post.get("mentions", []),
                "timestamp": post.get("timestamp"),
                "likesCount": post.get("likesCount"),
                "commentsCount": post.get("commentsCount"),
                "videoViewCount": post.get("videoViewCount"),
                "url": post.get("url"),
            })

        # Return only useful profile fields
        return {
            "id": profile.get("id"),
            "username": profile.get("username"),
            "fullName": profile.get("fullName"),
            "biography": profile.get("biography"),
            "followersCount": profile.get("followersCount"),
            "followsCount": profile.get("followsCount"),
            "postsCount": profile.get("postsCount"),
            "verified": profile.get("verified"),
            "isBusinessAccount": profile.get("isBusinessAccount"),
            "businessCategoryName": profile.get("businessCategoryName"),
            "externalUrls": profile.get("externalUrls", []),
            "latestPosts": cleaned_posts,
        }