from collections import Counter, defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.company_model import InstagramAnalysis
from app.utils.instagram_comparison_utils import compute_posting_frequency,compute_content_type_performance,sort_posts_by_recency,MAX_POSTS_ANALYZED
from sqlalchemy import text


class AdminInstagramProcessor:

    def process(
        self,
        db: Session,
        company_id,
        instagram_data: dict,
        source_file: str,
    ) -> InstagramAnalysis:
         
        raw_posts = instagram_data.get("latestPosts") or []
        posts = sort_posts_by_recency(raw_posts)[:MAX_POSTS_ANALYZED] 

        # =====================================================
        # Basic totals
        # =====================================================

        analyzed_posts_count = len(posts)
        n = analyzed_posts_count or 1 

        total_likes = sum(
            post.get("likesCount") or 0
            for post in posts
        )

        total_comments = sum(
            post.get("commentsCount") or 0
            for post in posts
        )

        # Only videos where view count is actually available
        videos_with_views = [
            post
            for post in posts
            if post.get("videoViewCount") is not None
        ]

        total_video_views = sum(
            post.get("videoViewCount") or 0
            for post in videos_with_views
        )

        posting_frequency_per_week = compute_posting_frequency(posts=posts)
        content_type_performance = compute_content_type_performance(posts=posts)
        avg_hashtags_per_post = round(sum(len(p.get("hashtags") or []) for p in posts) / n, 2)
        avg_caption_length = round(sum(len(p.get("caption") or "") for p in posts) / n, 1)

        # =====================================================
        # Averages
        # =====================================================

        average_likes = (
            round(total_likes / analyzed_posts_count)
            if analyzed_posts_count
            else 0
        )

        average_comments = (
            round(total_comments / analyzed_posts_count)
            if analyzed_posts_count
            else 0
        )

        average_video_views = (
            round(total_video_views / len(videos_with_views))
            if videos_with_views
            else 0
        )

        # =====================================================
        # Engagement Rate
        # =====================================================

        followers_count = instagram_data.get("followersCount") or 0

        engagement_rate = 0.0

        if followers_count > 0 and analyzed_posts_count > 0:
            engagement_rate = (
                (total_likes + total_comments)
                / (followers_count * analyzed_posts_count)
            ) * 100

        engagement_rate = round(engagement_rate, 2)

        # =====================================================
        # Hashtags
        # =====================================================

        hashtag_counter = Counter()

        for post in posts:
            hashtags = post.get("hashtags") or []

            for hashtag in hashtags:
                if hashtag:
                    hashtag_counter[hashtag.lower()] += 1

        top_hashtags = [
            {
                "hashtag": hashtag,
                "count": count,
            }
            for hashtag, count in hashtag_counter.most_common(10)
        ]

        # =====================================================
        # Mentions
        # =====================================================

        mention_counter = Counter()

        for post in posts:
            mentions = post.get("mentions") or []

            for mention in mentions:
                if mention:
                    mention_counter[mention.lower()] += 1

        top_mentions = [
            {
                "username": username,
                "count": count,
            }
            for username, count in mention_counter.most_common(10)
        ]

        # =====================================================
        # Content type statistics
        # =====================================================

        content_types = defaultdict(
            lambda: {
                "count": 0,
                "likes": 0,
                "comments": 0,
                "video_views": 0,
            }
        )

        for post in posts:

            content_type = post.get("type") or "Unknown"

            stats = content_types[content_type]

            stats["count"] += 1
            stats["likes"] += post.get("likesCount") or 0
            stats["comments"] += post.get("commentsCount") or 0
            stats["video_views"] += post.get("videoViewCount") or 0

        content_type_stats = {}

        for content_type, stats in content_types.items():

            count = stats["count"]

            content_type_stats[content_type] = {
                **stats,
                "average_likes": (
                    round(stats["likes"] / count, 2)
                    if count
                    else 0
                ),
                "average_comments": (
                    round(stats["comments"] / count, 2)
                    if count
                    else 0
                ),
            }

        # =====================================================
        # Top Post
        # =====================================================

        top_post = None

        if posts:
            top_post = max(
                posts,
                key=lambda post: (
                    (post.get("likesCount") or 0)
                    + (post.get("commentsCount") or 0)
                )
            )

        # =====================================================
        # Top Video
        # =====================================================

        video_posts = [
            post
            for post in posts
            if post.get("videoViewCount") is not None
        ]

        top_video = None

        if video_posts:
            top_video = max(
                video_posts,
                key=lambda post: post.get("videoViewCount") or 0
            )

        # =====================================================
        # Version
        # =====================================================

        current_version = (
            db.query(func.max(InstagramAnalysis.version))
            .filter(
                InstagramAnalysis.company_id == company_id
            )
            .scalar()
        )

        new_version = (current_version or 0) + 1

        # Mark previous analysis as not latest
        db.query(InstagramAnalysis).filter(
            InstagramAnalysis.company_id == company_id,
            InstagramAnalysis.is_latest.is_(True),
        ).update(
            {"is_latest": False},
            synchronize_session=False,
        )

        # =====================================================
        # Create analysis
        # =====================================================

        analysis = InstagramAnalysis(
            company_id=company_id,

            instagram_id=instagram_data.get("id"),
            username=instagram_data.get("username"),
            full_name=instagram_data.get("fullName"),
            biography=instagram_data.get("biography"),

            followers_count=followers_count,
            follows_count=instagram_data.get("followsCount"),
            posts_count=instagram_data.get("postsCount"),

            verified=instagram_data.get("verified"),
            is_business_account=instagram_data.get(
                "isBusinessAccount"
            ),
            business_category_name=instagram_data.get(
                "businessCategoryName"
            ),

            external_urls=instagram_data.get("externalUrls") or [],
            has_external_links = bool(instagram_data.get("externalUrls")),
            analyzed_posts_count=analyzed_posts_count,

            total_likes=total_likes,
            total_comments=total_comments,
            total_video_views=total_video_views,

            average_likes=average_likes,
            average_comments=average_comments,
            average_video_views=average_video_views,

            engagement_rate=str(engagement_rate),

            content_type_performance=content_type_performance,
            posting_frequency_per_week=posting_frequency_per_week,
            avg_hashtags_per_post=avg_hashtags_per_post,
            avg_caption_length=avg_caption_length,

            content_type_stats=content_type_stats,
            top_hashtags=top_hashtags,
            top_mentions=top_mentions,

            top_post=top_post,
            top_video=top_video,

            latest_posts=posts,

            source_file=source_file,

            version=new_version,
            is_latest=True,
        )

        try:
            db.add(analysis)
            db.commit()
            db.refresh(analysis)

            print(
                f"[INSTAGRAM PROCESSOR] Analysis saved "
                f"for company {company_id}, version {new_version}"
            )

            return analysis

        except Exception:
            db.rollback()
            raise