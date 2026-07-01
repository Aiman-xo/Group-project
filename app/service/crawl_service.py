import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.agents.crawl_agent import CrawlAgent
from app.utils.url_classifier import URLClassifier

class CrawlerService:
    def __init__(self):
        self.agent = CrawlAgent()
        self.classifier = URLClassifier()
        self.executor = ThreadPoolExecutor(max_workers=4)

    def crawl_site(self, start_url):
        visited = set()
        base_match_url = start_url.rstrip("/")
        MAX_PAGES = 30

        CATEGORY_LIMITS = {
            "contact": 1,
            "pricing": 1,
            "company": 2,   # about, story pages
            "career": 2,    # jobs, hiring pages
            "product": 4,   # products/courses pages
            "service": 4,   # services pages
            "other": 3      # blogs, layout noise
        }

        category_counts = {k: 0 for k in CATEGORY_LIMITS}
        queue = [start_url]
        results = []
        
        while queue:
            if len(visited) >= MAX_PAGES:
                break

            current_url = queue.pop(0)

            # Normalize early to avoid tracking variants (e.g. trailing slashes)
            normalized_url = current_url.rstrip("/")
            if not normalized_url.startswith("http"): 
                normalized_url = current_url

            if normalized_url in visited:
                continue

            url_classification = self.classifier.classify(normalized_url)
            current_cat = url_classification["category"]

            # Double check category constraints before executing the browser crawl
            if current_cat in CATEGORY_LIMITS and category_counts[current_cat] >= CATEGORY_LIMITS[current_cat]:
                continue

            # Track normalized URL directly to prevent multi-hit requests
            visited.add(normalized_url)
            
            try:
                page_data = self.agent.crawl(normalized_url)
                page_data["category"] = current_cat
                category_counts[current_cat] += 1
            except Exception as e:
                print(f"Failed to crawl: {normalized_url} | Error: {e}")
                continue

            results.append(page_data)
            
            for link in page_data["links"]:
                if base_match_url not in link:
                    continue
                
                # Normalize child links before classifying or tracking them
                normalized_link = link.rstrip("/")
                if not normalized_link.startswith("http"):
                    normalized_link = link

                classification = self.classifier.classify(normalized_link)
                target_cat = classification["category"]

                # Do not queue if category quota is already exhausted
                if target_cat in CATEGORY_LIMITS and category_counts[target_cat] >= CATEGORY_LIMITS[target_cat]:
                    continue

                if (
                    classification["priority"] != "ignore"
                    and normalized_link not in visited
                    and normalized_link not in queue
                ):
                    if target_cat == "contact":
                        queue.insert(0, normalized_link)
                    else:
                        queue.append(normalized_link)
        return results

    async def run_async_crawl(self, start_url: str):
        """Wraps the synchronous scraper so FastAPI can offload it safely."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.crawl_site, start_url)