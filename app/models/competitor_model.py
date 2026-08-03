from sqlalchemy import Column, String, Text, DateTime, Boolean,Integer,ForeignKey,Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime,timezone
import uuid
from app.core.database import TenantBase

class Competitor(TenantBase):
    __tablename__ = "competitors"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    company_name = Column(
        String,
        nullable=False
    )

    website_url = Column(
        String,
        nullable=False,
        unique=True
    )

    industry = Column(
        String,
        nullable=True
    )

    location = Column(
        String,
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    slug = Column(String, unique=True, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class InstagramCompetitorProfile(TenantBase):
    __tablename__ = "instagram_competitor_profile"

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid.uuid4)

    competitor_id = Column(UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False, index=True)

    # Profile (same shape as InstagramAnalysis)
    instagram_id = Column(String, nullable=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    biography = Column(Text, nullable=True)
    followers_count = Column(Integer, nullable=True)
    follows_count = Column(Integer, nullable=True)
    posts_count = Column(Integer, nullable=True)
    verified = Column(Boolean, nullable=True)
    is_business_account = Column(Boolean, nullable=True)
    business_category_name = Column(String, nullable=True)
    external_urls = Column(JSONB, nullable=True)

    # Computed engagement
    analyzed_posts_count = Column(Integer, nullable=False, default=0)
    total_likes = Column(Integer, nullable=False, default=0)
    total_comments = Column(Integer, nullable=False, default=0)
    total_video_views = Column(Integer, nullable=False, default=0)
    average_likes = Column(Integer, nullable=False, default=0)
    average_comments = Column(Integer, nullable=False, default=0)
    average_video_views = Column(Integer, nullable=False, default=0)
    engagement_rate = Column(Numeric(10, 2), nullable=True)

    content_type_performance = Column(JSONB, nullable=True)
    posting_frequency_per_week = Column(Numeric(10, 2),nullable=True,default=0)
    has_external_links = Column(Boolean,nullable=True)
    avg_hashtags_per_post = Column(Numeric(10, 2), nullable=True)
    avg_caption_length = Column(Numeric(10, 2), nullable=True)

    content_type_stats = Column(JSONB, nullable=True)
    top_hashtags = Column(JSONB, nullable=True)
    top_mentions = Column(JSONB, nullable=True)
    top_post = Column(JSONB, nullable=True)
    top_video = Column(JSONB, nullable=True)

    # NOT storing full latest_posts here — see note below

    # LLM-generated highlights (new — this is what's different from InstagramAnalysis)
    strongest_content_type = Column(String, nullable=True)
    standout_themes = Column(JSONB, nullable=True)
    top_post_insight = Column(Text, nullable=True)
    notable_traits = Column(JSONB, nullable=True)

    latest_posts = Column(JSONB,nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_latest = Column(Boolean, nullable=False, default=True)
    last_analyzed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))