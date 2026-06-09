def normalize_url(url: str) -> str:
    url = url.strip()

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        url = f"https://{url}"

    return url