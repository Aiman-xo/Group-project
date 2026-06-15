from pydantic import BaseModel

class CrawlResult(BaseModel):
    website_url: str
    title: str | None = None
    meta_description: str | None = None
    headings: list[str] = []
    links: list[str] = []