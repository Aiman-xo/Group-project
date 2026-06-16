from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urldefrag


class CrawlAgent:

    def crawl(self, url: str):

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            page.wait_for_timeout(3000)

            html = page.content()

            browser.close()

        soup = BeautifulSoup(
            html,
            "lxml"
        )

        title = (
            soup.title.string.strip()
            if soup.title
            else None
        )

        description = None

        meta = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        if meta:
            description = meta.get("content")

        headings = [
            h.get_text(strip=True)
            for h in soup.find_all(
                ["h1", "h2"]
            )
        ]

        links = []

        for link in soup.find_all(
            "a",
            href=True
        ):
            full_url = urljoin(
                url,
                link["href"]
            )

            full_url, _ = urldefrag(full_url)

            full_url = full_url.rstrip("/")
            
            if full_url not in links:
                links.append(full_url)

        return {
            "website_url": url,
            "title": title,
            "meta_description": description,
            "headings": headings[:20],
            "links": links[:50],
            "html": html
        }