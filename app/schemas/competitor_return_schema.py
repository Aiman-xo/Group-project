from pydantic import BaseModel
from typing import List

class CompetitorReturn(BaseModel):
    id:str
    company_name:str
    website_url:str
    industry:str
    location:str

    class Config:
        from_attributes = True 

class CompetitorReturnResponse(BaseModel):
    competitors: List[CompetitorReturn]
    total:int
    page:int
    limit:int