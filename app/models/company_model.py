from app.core.database import PublicBase
from sqlalchemy import Column,String,Integer,Boolean
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