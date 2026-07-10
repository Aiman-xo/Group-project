from pydantic import BaseModel

class CompetitorAnalysisRequest(BaseModel):
    company_name: str
    slug: str