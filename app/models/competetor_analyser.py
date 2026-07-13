from sqlalchemy import String,Column,Integer,Text,ForeignKey,ARRAY,DateTime,Boolean
from app.core.database import TenantBase
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime,timezone
from sqlalchemy.dialects.postgresql import JSONB
import uuid


class CompetetorAnalyser(TenantBase):
    __tablename__ = 'competitor_analyses'

    id = Column(UUID(as_uuid=True),unique=True, primary_key=True,nullable=False,default=uuid.uuid4)
    competitor_id = Column(UUID(as_uuid=True),ForeignKey('competitors.id'),nullable=True)
    competitor_name = Column(String,nullable=True)
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

class CompetitorComparison(TenantBase):
    __tablename__ = "competitor_comparison_reports"

    id = Column(UUID(as_uuid=True),unique=True, primary_key=True,nullable=False,index=True,default=uuid.uuid4)

    # link back to the competitor this comparison belongs to
    competitor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("competitor_analyses.id"),
        nullable=False,
        index=True
    )
    competitor_name = Column(String, nullable=False, index=True)
    data_freshness_note = Column(String, nullable=True)

    positioning_gap = Column(JSONB, nullable=False, default=dict)
    narrative_gap_analysis = Column(JSONB, nullable=False, default=dict)
    reputation = Column(JSONB, nullable=False, default=dict)
    social_presence_gap = Column(JSONB, nullable=False, default=dict)
    trajectory = Column(JSONB, nullable=False, default=list)
    recommendations = Column(JSONB, nullable=False, default=list)

    version = Column(Integer, nullable=False, default=1)
    is_latest = Column(Boolean, nullable=False, default=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )