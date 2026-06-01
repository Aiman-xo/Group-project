from app.core.database import Base
from sqlalchemy import Column,String,Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Company(Base):
    __tablename__ = 'companies'

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