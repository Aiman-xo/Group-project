from pydantic import BaseModel


class CompetitorSearchRequest(BaseModel):
    industry: str
    country: str
    state: str
    district: str

class CompetitorResponse(BaseModel):
    query: str
    total_competitors: int
    competitors: list