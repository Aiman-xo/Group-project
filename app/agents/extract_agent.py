import re
from bs4 import BeautifulSoup


class ExtractAgent:
    """
    Cleans structural HTML down to dense, unique content tokens per page.
    Removes boilerplate text, structural layout strings, navigation, and visual noise
    to minimize LLM context window pressure while preserving data extraction accuracy.
    """

    PHONE_PATTERN = re.compile(
        r"""
        (?:\+?1[\s\-.]?[\(\[]?\d{3}[\)\]]?[\s\-.]?\d{3}[\s\-.]?\d{4})
        |
        (?:\+\d{1,3}[\s\-.]?(?:\d[\s\-.]?){6,14}\d)
        """,
        re.VERBOSE,
    )

    SOCIAL_DOMAINS = {
        "linkedin": "linkedin.com/",
        "github": "github.com/",
        "twitter": "twitter.com/",
        "facebook": "facebook.com/",
        "instagram": "instagram.com/",
        "youtube": "youtube.com/",
    }

    BOILERPLATE_PATTERNS = [
        re.compile(r"\ball rights reserved\b", re.I),
        re.compile(r"\bcopyright\b", re.I),
        re.compile(r"©", re.I),
        re.compile(r"\bprivacy polic", re.I),
        re.compile(r"\bcookie\b", re.I),
        re.compile(r"\bterms (of|and) (service|use|conditions)\b", re.I),
        re.compile(r"\bsitemap\b", re.I),
        re.compile(r"^\s*\d{4,}\s*$"),  # Bare zip/pin codes on standalone lines
    ]

    # Strips visual symbols, emojis, layout stars, and structural arrows
    UI_AND_EMOJI_PATTERN = re.compile(
        r"[\U0001F300-\U0001FAFF]|\u2192|[\u2600-\u26FF]|[\u2700-\u27BF]|\u2605"
    )

    # Identifies carousel or pagination tracking lines like "01 / 04"
    LAYOUT_NOISE_PATTERN = re.compile(r"^\s*\d+\s*/\s*\d+\s*$")

    MAX_CLEAN_TEXT_CHARS = 4000  # Safe token compression limit per page

    def extract(self, page: dict) -> dict:
        html = page.get("html", "")
        soup = BeautifulSoup(html, "lxml")

        # Pull contacts from full raw DOM text (since footer carries vital data)
        full_text_for_contacts = soup.get_text(separator=" ", strip=True)
        emails = sorted(
            set(
                re.findall(
                    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
                    full_text_for_contacts,
                )
            )
        )
        phones = sorted(
            {
                m.group(0).strip()
                for m in self.PHONE_PATTERN.finditer(full_text_for_contacts)
                if self._valid_phone(m.group(0))
            }
        )
        social_links = self._extract_social(soup)

        # Build highly compressed text payload
        clean_text = self._build_clean_text(html)

        return {
            "url": page.get("website_url"),
            "emails": emails,
            "phones": phones,
            "social_links": social_links,
            "clean_text": clean_text,
        }

    def _build_clean_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")

        # 1. Strip structural non-content HTML5 tags entirely
        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
                "iframe",
                "nav",
                "header",
                "footer",
                "form",
            ]
        ):
            tag.decompose()

        # 2. Aggressively target common header/footer/nav layout classes and ids
        # This solves modern sites that use <div> or <section> instead of semantic tags
        nav_and_footer_selectors = [
            # IDs
            '[id*="header"]',
            '[id*="footer"]',
            '[id*="nav"]',
            '[id*="menu"]',
            # Classes
            '[class*="header"]',
            '[class*="footer"]',
            '[class*="nav"]',
            '[class*="menu"]',
            '[class*="topbar"]',
            '[class*="sidebar"]',
        ]

        for selector in nav_and_footer_selectors:
            for element in soup.select(selector):
                element.decompose()

        # 3. Extract text line by line using standard newlines
        raw_text = soup.get_text(separator="\n")
        lines = [ln.strip() for ln in raw_text.split("\n")]
        lines = [ln for ln in lines if ln]  # Drop empty lines

        seen = set()
        cleaned_lines = []

        for line in lines:
            # Drop very short structural crumbs or dangling menu buttons
            if len(line) < 4:
                continue

            # Filter out boilerplate sentences
            if any(p.search(line) for p in self.BOILERPLATE_PATTERNS):
                continue

            # Drop layout structural pages ("01 / 04")
            if self.LAYOUT_NOISE_PATTERN.match(line):
                continue

            # Clean visual noise and UI arrows
            line = self.UI_AND_EMOJI_PATTERN.sub("", line).strip()

            # Re-verify length check post symbol stripping
            if len(line) < 4:
                continue

            # Deduplicate identical fragments within the same page
            key = line.lower()
            if key in seen:
                continue
            seen.add(key)

            cleaned_lines.append(line)

        clean_text = "\n".join(cleaned_lines)
        return clean_text[: self.MAX_CLEAN_TEXT_CHARS]

    def _extract_social(self, soup: BeautifulSoup) -> dict:
        social_links = {k: set() for k in self.SOCIAL_DOMAINS}
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            for platform, domain in self.SOCIAL_DOMAINS.items():
                if domain in href:
                    social_links[platform].add(href.split("?")[0].rstrip("/"))
        return {k: sorted(v) for k, v in social_links.items()}

    def _valid_phone(self, raw: str) -> bool:
        digits = re.sub(r"\D", "", raw)
        return 7 <= len(digits) <= 15