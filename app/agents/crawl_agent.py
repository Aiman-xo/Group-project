import re
from urllib.parse import urljoin, urldefrag, urlparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


class CrawlAgent:

    def crawl(self, url: str) -> dict:
        """Crawls a target page and extracts structural architecture, metadata,

        and link footprints for corporate comparison engine profiling.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                # Execute realistic page load timeouts
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)  # Gentle wait for hydration
                html = page.content()
            except Exception as e:
                browser.close()
                raise e
            finally:
                browser.close()

        soup = BeautifulSoup(html, "lxml")

        # 1. Structural Metadata Core Extraction
        title = soup.title.string.strip() if soup.title else None
        
        description = None
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "").strip()

        # Capture primary visual text highlights
        headings = [
            h.get_text(strip=True)
            for h in soup.find_all(["h1", "h2"])
            if h.get_text(strip=True)
        ]

        # 2. Intelligent Link Analysis Engine
        internal_links = []
        external_links = []
        parsed_base = urlparse(url)
        base_domain = parsed_base.netloc.replace("www.", "")

        for link in soup.find_all("a", href=True):
            raw_href = link["href"].strip()
            
            # Skip UI interaction links or void actions
            if not raw_href or raw_href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            full_url = urljoin(url, raw_href)
            full_url, _ = urldefrag(full_url)
            full_url = full_url.rstrip("/")

            parsed_target = urlparse(full_url)
            target_domain = parsed_target.netloc.replace("www.", "")

            # Group links into internal domain vs external network links
            if base_domain in target_domain:
                if full_url not in internal_links:
                    internal_links.append(full_url)
            else:
                if full_url not in external_links:
                    external_links.append(full_url)

        # 3. Detect Technical Product Footprints
        # Scan scripts to check what tech stack they rely on (e.g. HubSpot, Marketo, Google Analytics)
        tech_footprints = []
        script_sources = [s.get("src", "") for s in soup.find_all("script", src=True)]
        for src in script_sources:
            for platform in ["analytics", "hubspot", "marketo", "hotjar", "intercom", "salesforce"]:
                if platform in src.lower() and platform not in tech_footprints:
                    tech_footprints.append(platform)

        return {
            "website_url": url,
            "title": title,
            "meta_description": description,
            "headings": headings[:20],
            "links": internal_links[:50],        # Internal paths for your queue loop
            "external_outbound": external_links, # Links pointing to partners/tools
            "tech_stack_footprints": tech_footprints,
            "html": html
        }