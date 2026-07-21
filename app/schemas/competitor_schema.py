from uuid import UUID
from datetime import datetime
from typing import Optional,List

from pydantic import BaseModel, ConfigDict


class CompetitorCreate(BaseModel):
    company_name: str
    website_url: str
    industry: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


class CompetitorUpdate(BaseModel):
    company_name: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CompetitorResponse(BaseModel):
    id: UUID
    company_name: str
    website_url: str
    industry: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    slug: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
 
    model_config = ConfigDict(from_attributes=True)

class CompetitorReturnResponse(BaseModel):
    competitors: List[CompetitorResponse]
    total:int
    page:int
    limit:int



