from collections import Counter

def compute_instagram_stats(data: dict) -> dict:
    posts = data.get("latestPosts", [])
    total_likes = sum(p.get("likesCount") or 0 for p in posts)
    total_comments = sum(p.get("commentsCount") or 0 for p in posts)
    total_video_views = sum(p.get("videoViewCount") or 0 for p in posts if p.get("videoViewCount"))
    n = len(posts) or 1

    hashtag_counter = Counter(h for p in posts for h in p.get("hashtags", []))
    mention_counter = Counter(m for p in posts for m in p.get("mentions", []))
    content_types = Counter(p.get("type") for p in posts)

    top_post = max(posts, key=lambda p: p.get("likesCount") or 0, default=None)

    video_posts = [p for p in posts if p.get("videoViewCount")]
    top_video = max(video_posts, key=lambda p: p.get("videoViewCount") or 0, default=None)

    trimmed_posts = [
        {
            "id": p.get("id"),
            "shortCode": p.get("shortCode"),
            "type": p.get("type"),
            "caption": p.get("caption"),
            "hashtags": p.get("hashtags"),
            "timestamp": p.get("timestamp"),
            "likesCount": p.get("likesCount"),
            "commentsCount": p.get("commentsCount"),
            "videoViewCount": p.get("videoViewCount"),
            "url": p.get("url"),
        }
        for p in posts
    ]

    return {
        "instagram_id": data.get("id"),
        "username": data.get("username"),
        "full_name": data.get("fullName"),
        "biography": data.get("biography"),
        "followers_count": data.get("followersCount"),
        "follows_count": data.get("followsCount"),
        "posts_count": data.get("postsCount"),
        "verified": data.get("verified"),
        "is_business_account": data.get("isBusinessAccount"),
        "business_category_name": data.get("businessCategoryName"),
        "external_urls": data.get("externalUrls"),

        "analyzed_posts_count": len(posts),
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_video_views": total_video_views,
        "average_likes": int(round(total_likes / n)),
        "average_comments": int(round(total_comments / n)),
        "average_video_views": int(round(total_video_views / len(video_posts))) if video_posts else 0,
        "engagement_rate": round(((total_likes + total_comments) / n) / (data.get("followersCount") or 1) * 100, 2),

        "top_hashtags": hashtag_counter.most_common(10),
        "top_mentions": mention_counter.most_common(5),
        "content_type_stats": dict(content_types),
        "top_post": {"caption": top_post.get("caption"), "likes": top_post.get("likesCount"), "url": top_post.get("url")} if top_post else None,
        "top_video": {"caption": top_video.get("caption"), "views": top_video.get("videoViewCount"), "url": top_video.get("url")} if top_video else None,
        "latest_posts": trimmed_posts,
    }