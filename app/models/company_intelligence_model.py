from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import TenantBase


class CompanyIntelligence(TenantBase):
    __tablename__ = "company_intelligence"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    business_summary = Column(
        Text,
        nullable=True
    )

    target_market = Column(
        Text,
        nullable=True
    )

    products_services = Column(
        Text,
        nullable=True
    )

    strengths = Column(
        Text,
        nullable=True
    )

    weaknesses = Column(
        Text,
        nullable=True
    )

    technology_stack = Column(
        Text,
        nullable=True
    )

    location = Column(
        String,
        nullable=True
    )

    full_analysis = Column(
        Text,
        nullable=True
    )

    report_url = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )