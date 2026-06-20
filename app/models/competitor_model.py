from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
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
