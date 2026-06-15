from app.service.crawl_service import CrawlerService

crawler = CrawlerService()

data = crawler.crawl_site(
    "https://fastapi.tiangolo.com"
)

print(f"Pages crawled: {len(data)}")

for page in data[:5]:
    print(page["website_url"])