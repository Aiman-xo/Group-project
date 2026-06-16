class URLClassifier:

    HIGH_PRIORITY = {
        "about": "company",
        "contact": "contact",
        "career": "career",
        "careers": "career",
        "jobs": "career",
        "hiring": "career",
        "product": "product",
        "products": "product",
        "service": "service",
        "services": "service",
        "pricing": "pricing",
        "solution": "solution",
        "solutions": "solution",
    }

    IGNORE = [
        "privacy",
        "terms",
        "cookie",
        "login",
        "signup",
        "/de/",
        "/fr/",
        "/ja/",
        "/ko/",
        "/zh/",
        ".zip",
        ".exe",
        ".msi",
        ".msix",
        ".tar",
        ".tar.gz",
        ".gz",
        ".pkg",
        ".dmg",
        ".deb",
        ".rpm",
    ]

    def classify(self, url: str):

        url_lower = url.lower()

        for word in self.IGNORE:
            if word in url_lower:
                return {
                    "category": "ignore",
                    "priority": "ignore"
                }

        for word, category in self.HIGH_PRIORITY.items():
            if word in url_lower:
                return {
                    "category": category,
                    "priority": "high"
                }

        return {
            "category": "other",
            "priority": "medium"
        }