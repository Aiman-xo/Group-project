from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class CompetitorAnalysisRequest(BaseModel):
    company_name: str
    slug: str

# Compare Analysis schema
class CompareAnalysisSchema(BaseModel):
    
    services: list[str] | None
    products: list[str] | None
    summary_text: str | None
    github:str | None
    linkedin:str | None
    youtube:str | None
    facebook:str | None
    email:str | None
    phone:str | None
    instagram:str | None
    rating_score:str | None
    review_source:str | None
    total_reviews:int | None
    positive_themes: list[str] | None
    negative_themes: list[str] | None
    community_insights: list[str] | None
    version: int
    created_at: datetime

    class Config:
        from_attributes = True