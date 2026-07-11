from sqlalchemy import String,Column,Integer,Text,ForeignKey,ARRAY,DateTime,Boolean
from app.core.database import TenantBase
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime,timezone
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
