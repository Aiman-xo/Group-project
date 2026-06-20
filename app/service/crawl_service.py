import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.agents.crawl_agent import CrawlAgent
from app.utils.url_classifier import URLClassifier

class CrawlerService:
    def __init__(self):
        self.agent = CrawlAgent()
        self.classifier = URLClassifier()
        # Allows running the synchronous Playwright scraper concurrently
        self.executor = ThreadPoolExecutor(max_workers=4)

    def crawl_site(self, start_url):
        visited = set()
        base_match_url = start_url.rstrip("/")
        MAX_PAGES = 30

        queue = [start_url]
        results = []
        
        while queue:
            if len(visited) >= MAX_PAGES:
                break

            current_url = queue.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)
            
            try:
                page_data = self.agent.crawl(current_url)
                classification = self.classifier.classify(current_url)
                page_data["category"] = classification["category"]
            except Exception as e:
                print(f"Failed to crawl: {current_url} | Error: {e}")
                continue

            results.append(page_data)
            
            for link in page_data["links"]:
                if base_match_url not in link:
                    continue
                
                classification = self.classifier.classify(link)

                if (
                    classification["priority"] != "ignore"
                    and link not in visited
                    and link not in queue
                ):
                    if classification["category"] == "contact":
                        queue.insert(0, link)
                    else:
                        queue.append(link)
        return results

    async def run_async_crawl(self, start_url: str):
        """Wraps the synchronous scraper so FastAPI can offload it safely."""
        loop = asyncio.get_event_loop()
        # Offloads the blocking crawl loop to a separate thread pool background track
        return await loop.run_in_executor(self.executor, self.crawl_site, start_url)