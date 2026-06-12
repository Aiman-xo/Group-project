from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.database import TenantBase

class CompanyProfile(TenantBase):
    __tablename__ = "company_profile"

    id = Column(UUID(as_uuid=True), primary_key=True)

    company_name = Column(String, nullable=False)

    website_url = Column(String, nullable=False)

    industry = Column(String)

    location = Column(String)

    description = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

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

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )