import requests
import json
import time
from datetime import datetime


class RedditAgent:
    """
    Reddit Intelligence Agent — Universal Company Research Tool.

    Fetches real Reddit posts mentioning any company name.
    Output is deduplicated, noise-filtered, and structured for LLM summarization.

    Data source: Pullpush.io (community Pushshift replacement — no API key needed).
    Fallback:    Arctic Shift API (academic Reddit archive — no API key needed).

    Designed to plug into an S3-save + LLM summary pipeline.

    Usage (matches IntelService expectations):
        agent = RedditAgent()
        json_string = agent.fetch_leaks("Tesla")        # → str  (for S3 upload)
        llm_text    = agent.to_llm_text("Tesla")        # → str  (for LLM summarization)
    """

    PULLPUSH_URL     = "https://api.pullpush.io/reddit/search/submission/"
    ARCTIC_SHIFT_URL = "https://arctic-shift.photon-reddit.com/api/posts/search"

    # Subreddits that produce off-topic noise
    NOISE_SUBREDDITS = {
        # social/hookup
        "mallu__kambi", "r4r", "dirtyr4r", "gonewild",
        # meme/random
        "randomthoughts", "teenagers", "memes", "facepalm", "funny",
        # geography/travel (match company names by accident)
        "southjersey", "newjersey", "travel", "roadtrip", "cities",
        # design/cad (match product names by accident)
        "designscad", "autocad", "architecture", "engineering",
        # gaming (fan art, character names)
        "rainworld", "gaming", "patientgamers",
    }

    # Posts must contain at least one of these business-context signals
    # anywhere in title or snippet to be considered relevant
    BUSINESS_SIGNALS = {
        "review", "scam", "legit", "experience", "worth", "fee", "salary",
        "placement", "course", "bootcamp", "training", "job", "hire", "hiring",
        "refund", "complaint", "issue", "problem", "opinion", "thoughts",
        "rating", "recommend", "trust", "genuine", "feedback", "service",
        "product", "company", "startup", "interview", "work", "employee",
        "customer", "price", "cost", "quality", "support", "offer", "deal",
        "fraud", "expose", "warning", "avoid", "good", "bad", "terrible",
        "excellent", "worst", "best", "honest", "fake", "real", "joining",
        "campus", "batch", "program", "internship", "stipend", "founded",
    }

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    # ─────────────────────────────────────────────────────────────
    # PUBLIC — called by IntelService
    # ─────────────────────────────────────────────────────────────

    def fetch_leaks(self, company_name: str, limit: int = 50) -> str:
        """
        Fetch, deduplicate, and filter Reddit posts about company_name.
        Returns a JSON string — ready for direct S3 upload via upload_string_to_s3().

        Args:
            company_name: Any business name or domain (e.g. "Tesla", "zomato.com")
            limit:        Max posts to fetch (default 50)
        """
        result = self._fetch(company_name, limit)
        return json.dumps(result, indent=4)

    def to_llm_text(self, company_name: str, limit: int = 50) -> str:
        """
        Returns a plain-text formatted report of Reddit posts — optimised
        for LLM summarization (cleaner than passing raw JSON to the model).

        Args:
            company_name: Any business name or domain
            limit:        Max posts to fetch
        """
        result = self._fetch(company_name, limit)
        return self._format_for_llm(result)

    # ─────────────────────────────────────────────────────────────
    # INTERNAL FETCH PIPELINE
    # ─────────────────────────────────────────────────────────────

    def _fetch(self, company_name: str, limit: int) -> dict:
        """Core fetch — returns a clean dict."""
        clean_name = company_name.split(".")[0].strip()

        for source_fn in [self._fetch_pullpush, self._fetch_arctic_shift]:
            result = source_fn(clean_name, limit)
            if result["status"] == "ok":
                return self._clean(result, clean_name)

        return {
            "company_name":            clean_name,
            "source":                  "none",
            "fetched_at":              self._now(),
            "status":                  "all_sources_failed",
            "extracted_threads_count": 0,
            "duplicates_removed":      0,
            "reddit_insights":         [],
        }

    # ─────────────────────────────────────────────────────────────
    # SOURCE 1 — Pullpush.io
    # ─────────────────────────────────────────────────────────────

    def _fetch_pullpush(self, clean_name: str, limit: int) -> dict:
        payload = self._base(clean_name, "pullpush_io")
        try:
            resp = self._get(
                self.PULLPUSH_URL,
                params={
                    "q":         clean_name,
                    "size":      min(limit, 100),
                    "sort":      "desc",
                    "sort_type": "created_utc",
                },
            )
            if resp is None:
                payload["status"] = "error_request_failed"
                return payload
            if resp.status_code != 200:
                payload["status"] = f"error_http_{resp.status_code}"
                return payload

            for post in resp.json().get("data", []):
                payload["reddit_insights"].append(self._normalize(post))

            payload["extracted_threads_count"] = len(payload["reddit_insights"])
            payload["status"] = "ok" if payload["reddit_insights"] else "no_results"

        except Exception as e:
            payload["status"] = f"error_{type(e).__name__}"

        return payload

    # ─────────────────────────────────────────────────────────────
    # SOURCE 2 — Arctic Shift
    # ─────────────────────────────────────────────────────────────

    def _fetch_arctic_shift(self, clean_name: str, limit: int) -> dict:
        payload = self._base(clean_name, "arctic_shift")
        try:
            resp = self._get(
                self.ARCTIC_SHIFT_URL,
                params={
                    "q":     clean_name,
                    "limit": min(limit, 100),
                    "sort":  "created_utc",
                    "order": "desc",
                },
            )
            if resp is None:
                payload["status"] = "error_request_failed"
                return payload
            if resp.status_code != 200:
                payload["status"] = f"error_http_{resp.status_code}"
                return payload

            for post in resp.json().get("data", []):
                payload["reddit_insights"].append(self._normalize(post))

            payload["extracted_threads_count"] = len(payload["reddit_insights"])
            payload["status"] = "ok" if payload["reddit_insights"] else "no_results"

        except Exception as e:
            payload["status"] = f"error_{type(e).__name__}"

        return payload

    # ─────────────────────────────────────────────────────────────
    # CLEANING — deduplicate + filter noise
    # ─────────────────────────────────────────────────────────────

    def _clean(self, payload: dict, clean_name: str) -> dict:
        seen_links    = set()
        seen_titles   = set()
        clean_posts   = []
        removed_count = 0

        for post in payload["reddit_insights"]:

            # 1. Deduplicate by permalink
            link      = post.get("link", "") or ""
            norm_link = link.split("?")[0].rstrip("/")
            if norm_link in seen_links:
                removed_count += 1
                continue
            seen_links.add(norm_link)

            # 2. Deduplicate near-identical titles
            title_key = post.get("thread_title", "").strip().lower()
            if title_key in seen_titles:
                removed_count += 1
                continue
            seen_titles.add(title_key)

            # 3. Skip posts with no usable title
            title   = post.get("thread_title", "") or ""
            snippet = post.get("snippet", "") or ""
            if not title or title.strip() in ("[deleted]", "[removed]", ""):
                removed_count += 1
                continue

            # 4. Skip noise subreddits
            subreddit_raw = (post.get("subreddit") or "").lstrip("r/").lower()
            if subreddit_raw in self.NOISE_SUBREDDITS:
                removed_count += 1
                continue

            # 5. Company name MUST appear in the title specifically
            #    (body-only matches cause too many false positives for
            #    ambiguous/short company names like "Bridgeon", "Nova", etc.)
            name_lower = clean_name.lower()
            if name_lower not in title.lower():
                removed_count += 1
                continue

            # 6. Post must contain at least one business-context signal
            #    (filters out geography/fan-art/unrelated posts that happen
            #    to mention the company name in passing)
            combined = (title + " " + snippet).lower()
            has_signal = any(sig in combined for sig in self.BUSINESS_SIGNALS)
            if not has_signal:
                removed_count += 1
                continue

            # 8. Flag removed/deleted body (title still useful for LLM)
            if snippet.strip() in ("[removed]", "[deleted]", ""):
                post["snippet"]         = None
                post["content_removed"] = True
            else:
                post["content_removed"] = False

            clean_posts.append(post)

        payload["reddit_insights"]         = clean_posts
        payload["extracted_threads_count"] = len(clean_posts)
        payload["duplicates_removed"]      = removed_count
        payload["status"] = "ok" if clean_posts else "no_results"

        return payload

    # ─────────────────────────────────────────────────────────────
    # LLM TEXT FORMATTER
    # ─────────────────────────────────────────────────────────────

    def _format_for_llm(self, result: dict) -> str:
        """
        Converts the cleaned result dict into a plain-text block
        optimised for LLM summarization.
        """
        company    = result.get("company_name", "Unknown")
        status     = result.get("status", "unknown")
        count      = result.get("extracted_threads_count", 0)
        source     = result.get("source", "unknown")
        fetched_at = result.get("fetched_at", "")
        posts      = result.get("reddit_insights", [])

        lines = [
            f"== REDDIT SENTIMENT REPORT: {company.upper()} ==",
            f"Fetched: {fetched_at[:10]} | Posts: {count} | Source: {source} | Status: {status}",
            "",
        ]

        if status != "ok" or not posts:
            lines.append("No Reddit posts found for this company.")
            return "\n".join(lines)

        for i, post in enumerate(posts, 1):
            title     = post.get("thread_title", "Untitled")
            snippet   = post.get("snippet") or "[Content removed by Reddit]"
            subreddit = post.get("subreddit", "unknown")
            score     = post.get("score", 0)
            comments  = post.get("num_comments", 0)
            link      = post.get("link", "")

            # Convert Unix timestamp to readable date if present
            created = post.get("created_utc")
            date_str = ""
            if created:
                try:
                    date_str = datetime.utcfromtimestamp(float(created)).strftime("%Y-%m-%d")
                except Exception:
                    date_str = ""

            lines += [
                f"[{i}] {title}",
                f"    Subreddit : {subreddit}  |  Date: {date_str}  |  Score: {score}  |  Comments: {comments}",
                f"    Snippet   : {snippet[:300]}",
                f"    Link      : {link}",
                "",
            ]

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────

    def _normalize(self, post: dict) -> dict:
        permalink = post.get("permalink", "")
        return {
            "thread_title": (post.get("title") or "").strip(),
            "snippet":      (post.get("selftext") or "")[:500].strip(),
            "subreddit":    f"r/{post.get('subreddit', '')}",
            "score":        post.get("score"),
            "num_comments": post.get("num_comments"),
            "author":       post.get("author"),
            "created_utc":  post.get("created_utc"),
            "link":         f"https://reddit.com{permalink}" if permalink else None,
        }

    def _get(self, url: str, params: dict, retries: int = 3):
        backoff = 2
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(
                    url, params=params, headers=self.headers, timeout=12
                )
                if resp.status_code == 429:
                    print(f"  [!] Rate limited. Retrying in {backoff}s... ({attempt}/{retries})")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return resp
            except requests.exceptions.RequestException as e:
                print(f"  [!] Request error: {e}")
                if attempt == retries:
                    return None
                time.sleep(backoff)
                backoff *= 2
        return None

    def _base(self, company_name: str, source: str) -> dict:
        return {
            "company_name":            company_name,
            "source":                  source,
            "fetched_at":              self._now(),
            "status":                  "pending",
            "extracted_threads_count": 0,
            "reddit_insights":         [],
        }

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent = RedditAgent()

    # --- S3 path (used by IntelService) ---
    json_str = agent.fetch_leaks("brototype", limit=50)
    result   = json.loads(json_str)
    print(json_str)
    print(f"\n✓ {result['extracted_threads_count']} clean posts | "
          f"dupes removed: {result.get('duplicates_removed', 0)} | "
          f"source: {result['source']} | status: {result['status']}")

    # --- LLM path ---
    # llm_text = agent.to_llm_text("brototype")
    # print(llm_text)