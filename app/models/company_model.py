from app.core.database import PublicBase,TenantBase
from sqlalchemy import Column,String,Integer,Boolean,ForeignKey,ARRAY,Text,DateTime
from datetime import datetime,timezone
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Numeric

import uuid

class Company(PublicBase):
    __tablename__ = 'companies'
    __table_args__ = {"schema": "public"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        nullable=False,
        default=uuid.uuid4
    )
    email:str = Column(String,unique=True,index=True,nullable=False)
    company_name:str = Column(String,nullable=False)
    website_link:str = Column(String,nullable=True)
    industry:str = Column(String,nullable=False)
    password:str = Column(String,nullable=False)

    schema_name = Column(String, unique=True, nullable=True)

    slug = Column(String, unique=True, nullable=True)

    is_verified:bool = Column(Boolean,default=False,nullable=False,server_default="false")


class ProfileDataAnalyser(TenantBase):
    __tablename__ = 'company_profile_datas'

    id = Column(UUID(as_uuid=True),unique=True, primary_key=True,nullable=False,default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True),nullable=True)

    source_file = Column(String,nullable=True)
    services = Column(ARRAY(Text),nullable=True)
    products = Column(ARRAY(Text),nullable=True)
    tech_stacks = Column(ARRAY(Text),nullable=True)
    github = Column(String,nullable=True)
    linkedin = Column(String,nullable=True)
    youtube = Column(String,nullable=True)
    facebook = Column(String,nullable=True)
    email = Column(String(255),nullable=True)
    phone = Column(String(20),nullable=True)
    summary_text = Column(Text,nullable=True)

    instagram = Column(String, nullable=True)

    # Reputation/reviews (3rd file)
    rating_score = Column(String, nullable=True)  # or Numeric, see note below
    total_reviews = Column(Integer, nullable=True)
    review_source = Column(String, nullable=True)
    positive_themes = Column(ARRAY(Text), nullable=True)
    negative_themes = Column(ARRAY(Text), nullable=True)

    # Community/reddit insights (2nd file)
    community_insights = Column(ARRAY(Text), nullable=True)
    
    # versions for storing the data only when there is change and we can track the version.
    version = Column(Integer,nullable=False,default=0)
    is_latest = Column(Boolean,default=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

class CSVDatas(TenantBase):
    __tablename__ = 'csv_data_analyse_table'
    
    id = Column(UUID(as_uuid=True),unique=True, primary_key=True,nullable=False,default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True),nullable=True)
    version = Column(Integer, nullable=False) 
    raw_csv_s3_key = Column(String, nullable=True)
    parsed_data = Column(JSONB, nullable=False)

    summary = Column(Text,nullable=True)
    health_score = Column(Integer, nullable=True)
    health_score_reason = Column(Text, nullable=True)

    growth_areas = Column(JSONB, nullable=True)
    problem_areas = Column(JSONB, nullable=True)
    recommendations = Column(JSONB, nullable=True)
    metric_changes = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    ) 

class InstagramAnalysis(TenantBase):
    __tablename__ = "instagram_analysis"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        nullable=False,
        default=uuid.uuid4
    )

    company_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    # =====================================================
    # Instagram Profile
    # =====================================================

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


    # =====================================================
    # Analyzed Posts Summary
    # =====================================================

    analyzed_posts_count = Column(
        Integer,
        nullable=False,
        default=0
    )

    total_likes = Column(
        Integer,
        nullable=False,
        default=0
    )

    total_comments = Column(
        Integer,
        nullable=False,
        default=0
    )

    total_video_views = Column(
        Integer,
        nullable=False,
        default=0
    )


    # =====================================================
    # Average Engagement
    # =====================================================

    average_likes = Column(
        Integer,
        nullable=False,
        default=0
    )

    average_comments = Column(
        Integer,
        nullable=False,
        default=0
    )

    average_video_views = Column(
        Integer,
        nullable=False,
        default=0
    )

    engagement_rate = Column(
        Numeric(10, 2),
        nullable=True
    )


    # =====================================================
    # Content Type Analysis
    #
    # Example:
    # {
    #     "Image": {
    #         "count": 8,
    #         "likes": 2500,
    #         "comments": 5,
    #         "average_likes": 312.5
    #     },
    #     "Video": {...},
    #     "Sidecar": {...}
    # }
    # =====================================================

    content_type_stats = Column(
        JSONB,
        nullable=True
    )


    # =====================================================
    # Hashtag Analysis
    #
    # Example:
    # [
    #   {"hashtag": "ERP", "count": 8},
    #   {"hashtag": "businesssoftware", "count": 7}
    # ]
    # =====================================================

    top_hashtags = Column(
        JSONB,
        nullable=True
    )


    # =====================================================
    # Mention Analysis
    #
    # Example:
    # [
    #   {"username": "neptonglobal", "count": 3}
    # ]
    # =====================================================

    top_mentions = Column(
        JSONB,
        nullable=True
    )


    # =====================================================
    # Top Performing Post
    # =====================================================

    top_post = Column(
        JSONB,
        nullable=True
    )


    # =====================================================
    # Top Video
    # =====================================================

    top_video = Column(
        JSONB,
        nullable=True
    )


    # =====================================================
    # Latest analyzed posts
    # =====================================================

    latest_posts = Column(
        JSONB,
        nullable=True
    )


    # =====================================================
    # Source
    # =====================================================

    source_file = Column(
        String,
        nullable=True
    )


    # =====================================================
    # Analysis Version
    # =====================================================

    version = Column(
        Integer,
        nullable=False,
        default=1
    )

    is_latest = Column(
        Boolean,
        nullable=False,
        default=True
    )


    # =====================================================
    # Timestamps
    # =====================================================

    last_analyzed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )