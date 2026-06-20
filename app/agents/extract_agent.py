import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class ExtractAgent:
    PHONE_PATTERN = re.compile(
        r"""
        (?:
            \+?1[\s\-.]?        
            [\(\[]?\d{3}[\)\]]? 
            [\s\-.]?            
            \d{3}
            [\s\-.]?
            \d{4}
        )
        |
        (?:
            \+\d{1,3}           
            [\s\-.]?
            (?:\d[\s\-.]?){6,14}\d  
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

    CAPABILITY_URL_SLUGS = {
        "service", "services", "solution", "solutions", "what-we-do", 
        "practice-area", "practice-areas", "capabilities", "offering", 
        "offerings", "expertise", "department", "departments", "faculty", 
        "faculties", "school", "schools", "specialty", "specialties"
    }
    
    DELIVERABLE_URL_SLUGS = {
        "product", "products", "platform", "platforms", "software", 
        "tool", "tools", "hardware", "app", "apps", "course", "courses", 
        "program", "programs", "degree", "degrees", "undergraduate", 
        "postgraduate", "academics", "treatment", "treatments", "clinical"
    }

    UNIVERSAL_BANNED_WORDS = {
        "our", "why", "about", "insight", "insights", "career", "careers", 
        "job", "jobs", "blog", "contact", "home", "pricing", "testimonial", 
        "testimonials", "case", "study", "studies", "culture", "team", "who", 
        "we", "history", "news", "event", "events", "resource", "resources", 
        "faq", "faqs", "learn", "more", "get", "started", "click", "here",
        "by", "author", "posted", "ceo", "director", "manager", "vp", "president",
        "leader", "leadership", "executive", "expert", "experts", "founder",
        "powering", "scale", "optimize", "accelerate", "transforming", "agentifying", 
        "driving", "maximizing", "building", "helping", "excellence", "enterprises",
        "follow", "links", "quick", "proud", "moment", "values", "activities", " PTA ", "pta"
    }

    # Match names starting with common academic or formal professional prefixes
    PERSON_PREFIX_PATTERN = re.compile(r"^(dr\.|mr\.|ms\.|prof\.|professor|vice\s+principal|principal)\s+", re.IGNORECASE)

    def extract(self, html: str) -> dict:
        soup = BeautifulSoup(html, "lxml")
        structural_soup = BeautifulSoup(html, "lxml")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        emails = sorted(set(re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)))
        raw_phones = [m.group(0) for m in self.PHONE_PATTERN.finditer(text)]
        phones = sorted({p.strip() for p in raw_phones if self._valid_phone(p)})

        social_links = {k: set() for k in self.SOCIAL_DOMAINS}
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            for platform, domain in self.SOCIAL_DOMAINS.items():
                if domain in href:
                    clean = href.split("?")[0].rstrip("/")
                    social_links[platform].add(clean)

        social_links = {k: sorted(v) for k, v in social_links.items()}
        
        # Raw extractions from markup tracks
        raw_caps = self.extract_structural_items(structural_soup, self.CAPABILITY_URL_SLUGS)
        raw_delivs = self.extract_structural_items(structural_soup, self.DELIVERABLE_URL_SLUGS)

        # Process and separate structural arrays
        capabilities = set()
        deliverables = set()
        people = set()

        # Combine all raw strings collected across text lines
        combined_raw_pool = set(raw_caps + raw_delivs)

        for item in combined_raw_pool:
            # 1. Route explicit human entities to their own bucket
            if self.PERSON_PREFIX_PATTERN.search(item):
                people.add(item)
                continue
            
            item_lower = item.lower()
            
            # Catch loose personal names lacking structural prefixes (e.g., Two or Three word capitalized groupings)
            # If a string contains keywords like 'department' or 'lab', it's safe structural data
            has_structural_keyword = any(k in item_lower for k in ["department", "lab", "service", "center", "centre", "solutions", "course", "degree", "program", "m.sc", "b.c.a", "b.sc", "b.com"])
            
            if not has_structural_keyword:
                # If it's a short 2-3 word phrase entirely composed of capitalized standard alpha strings, 
                # and lacks any structural operational words, drop it or flag as potential staff noise.
                words = item.split()
                if len(words) >= 2 and all(w[0].isupper() for w in words if w.isalpha()):
                    # Filter structural noise out safely
                    continue

            # 2. Separate remaining items dynamically into Capabilities vs Offerings
            if any(k in item_lower for k in ["department", "faculty", "school", "specialty", "service", "solutions", "lab", "library", "center", "centre"]):
                capabilities.add(item)
            else:
                deliverables.add(item)

        return {
            "emails": emails,
            "phones": phones,
            "social_links": social_links,
            "capabilities": sorted(list(capabilities)),  
            "deliverables": sorted(list(deliverables)),  
            "associated_people": sorted(list(people)) # Brand New Isolated Column Array
        }

    def _valid_phone(self, raw: str) -> bool:
        digits = re.sub(r"\D", "", raw)
        return 7 <= len(digits) <= 15

    def extract_structural_items(self, soup: BeautifulSoup, target_slugs: set) -> list:
        raw_items = set()

        nav_elements = soup.find_all(["nav", "header", "footer"])
        for wrapper in nav_elements:
            for link in wrapper.find_all("a", href=True):
                href = link["href"].lower()
                path_segments = set(urlparse(href).path.split("/"))
                if path_segments.intersection(target_slugs):
                    link_text = link.get_text(strip=True)
                    if self._is_valid_phrase(link_text, target_slugs):
                        raw_items.add(link_text)

        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            path = urlparse(href).path.strip("/")
            segments = [s for s in path.split("/") if s]
            if len(segments) >= 2 and segments[-2] in target_slugs:
                item_name = segments[-1].replace("-", " ").replace("_", " ").title()
                if self._is_valid_phrase(item_name, target_slugs):
                    raw_items.add(item_name)

        for noise in soup(["script", "style", "noscript"]):
            noise.decompose()
            
        for tag in soup.find_all(["h1", "h2", "h3"]):
            text = tag.get_text(strip=True)
            if self._is_valid_phrase(text, target_slugs):
                raw_items.add(text)

        normalized_items = set()
        for item in raw_items:
            words = item.split()
            cleaned_words = []
            for word in words:
                if word.upper() in {"AI", "ML", "CX", "IT", "ROI", "B2B", "B2C", "SAAS", "LLMOPS", "MLOPS", "CS", "BCA", "BSC", "MSC", "BCOM", "MCOM"}:
                    cleaned_words.append(word.upper())
                else:
                    cleaned_words.append(word.title())
                    
            clean_phrase = " ".join(cleaned_words)
            normalized_items.add(clean_phrase)

        return sorted(list(normalized_items))

    def _is_valid_phrase(self, text: str, target_slugs: set) -> bool:
        if not text or len(text) < 3:
            return False
            
        spaced_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        words = spaced_text.split()
        word_count = len(words)
        
        if word_count < 1 or word_count > 5:
            return False
            
        text_lower = spaced_text.lower()
        if word_count == 1 and text_lower in target_slugs:
            return False

        if re.search(r'\d{3,}', text): # Drop heavy date patterns but allow brief digits
            return False

        words_set = set(text_lower.split())
        if words_set.intersection(self.UNIVERSAL_BANNED_WORDS):
            return False

        return True