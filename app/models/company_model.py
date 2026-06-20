from app.core.database import PublicBase,TenantBase
from sqlalchemy import Column,String,Integer,Boolean,ForeignKey,ARRAY,Text,DateTime
from datetime import datetime,timezone
from sqlalchemy.dialects.postgresql import UUID

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

    source_file = Column(String,nullable=False)
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