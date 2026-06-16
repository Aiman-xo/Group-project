from app.agents.crawl_agent import CrawlAgent
from app.utils.url_classifier import URLClassifier

class CrawlerService:
    def __init__(self):
        self.agent = CrawlAgent()
        self.visited = set()
        self.classifier = URLClassifier()
    def crawl_site(self, start_url):

        MAX_PAGES = 50

        queue = [start_url]
        results = []
        while queue:
            
            if len(self.visited) >= MAX_PAGES:
                print(f"Reached max pages: {MAX_PAGES}")
                break

            current_url = queue.pop(0)
            if current_url in self.visited:
                continue
            self.visited.add(current_url)
            try:
                page_data = self.agent.crawl(current_url)
            except Exception as e:
                print(f"Failed: {current_url}")
                print(e)
                continue
            results.append(page_data)
            for link in page_data["links"]:
                if start_url not in link:
                    continue
                classification = self.classifier.classify(link)

                if (
                        classification["priority"] != "ignore"
                        and link not in self.visited
                        and link not in queue
                    ):
                        queue.append(link)
        return results