import re
from bs4 import BeautifulSoup


class ExtractAgent:

    # Matches real phone formats:
    #   +1-858-712-8966  /  (858) 712-8966  /  +44 20 7946 0958  /  858.712.8966
    # Requires at least one separator (space/dash/dot/parens) so raw digit runs don't match.
    PHONE_PATTERN = re.compile(
        r"""
        (?:
            \+?1[\s\-.]?        # optional US country code
            [\(\[]?\d{3}[\)\]]? # area code, optional parens/brackets
            [\s\-.]             # separator (required between area + prefix)
            \d{3}
            [\s\-.]
            \d{4}
        )
        |
        (?:
            \+(?!1\b)\d{1,3}    # international country code (non-US)
            [\s\-.]
            [\d\s\-\.]{6,14}    # local number (flexible formatting)
        )
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

    JOB_KEYWORDS = [
        "engineer",
        "developer",
        "architect",
        "manager",
        "analyst",
        "scientist",
        "designer",
        "consultant",
        "specialist",
        "intern",
    ]

    def extract(self, html: str,url: str) -> dict:

        soup = BeautifulSoup(html, "lxml")

        # Pull visible text (skip script/style noise)
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        # ── Emails ──────────────────────────────────────────────────────────
        emails = sorted(
            set(
                re.findall(
                    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
                    text,
                )
            )
        )

        # ── Phones ──────────────────────────────────────────────────────────
        raw_phones = self.PHONE_PATTERN.findall(text)
        phones = sorted(
            {p.strip() for p in raw_phones if self._valid_phone(p)}
        )

        # ── Social links (from <a href> only) ────────────────────────────────
        social_links: dict[str, list[str]] = {k: set() for k in self.SOCIAL_DOMAINS}

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            for platform, domain in self.SOCIAL_DOMAINS.items():
                if domain in href:
                    # Normalise: drop query strings & trailing slashes
                    clean = href.split("?")[0].rstrip("/")
                    social_links[platform].add(clean)

        social_links = {k: sorted(v) for k, v in social_links.items()}

        job_roles = self.extract_job_roles(
            soup
        )

        return {
            "emails": emails,
            "phones": phones,
            "social_links": social_links,
            "job_roles": job_roles,
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _valid_phone(self, raw: str) -> bool:
        """Accept only if digit count is 7–15 (E.164 range)."""
        digits = re.sub(r"\D", "", raw)
        return 7 <= len(digits) <= 15
    

    def extract_job_roles(self, soup):

        job_roles = set()

        for tag in soup.find_all(
            ["h1", "h2", "h3", "h4", "li"]
        ):

            text = tag.get_text(
                strip=True
            )

            text_lower = text.lower()

            for keyword in self.JOB_KEYWORDS:

                if keyword in text_lower:

                    job_roles.add(text)

                    break

        return sorted(job_roles)