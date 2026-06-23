from app.agents.web_search_agent import (
    build_queries,
    search_companies,
    extract_company_names,
    parse_company_response,
    get_official_website,
)


MIN_COMPETITORS = 6
MAX_COMPETITORS = 8


async def discover_competitors(
    industry: str,
    country: str = "",
    state: str = "",
    district: str = "",
):
    """
    Discover competitors using:

    District → State → Country

    Stop searching once MIN_COMPETITORS are found.
    Return at most MAX_COMPETITORS.
    """

    discovered = []

    seen_companies = set()
    seen_websites = set()

    queries = build_queries(
        industry=industry,
        country=country,
        state=state,
        district=district,
        limit=MAX_COMPETITORS,
    )

    used_query = ""

    for query in queries:

        print(f"\nSearching using: {query}")

        content = search_companies(query)

        if not content:
            continue

        gemini_response = extract_company_names(
            content=content,
            industry=industry,
            country=country,
            state=state,
            district=district,
            limit=MAX_COMPETITORS,
        )

        companies = parse_company_response(
            gemini_response
        )
        print(f"\nCompanies extracted from {query}:")
        print(companies)

        if not companies:
            continue

        for company in companies:

            # Maximum response limit
            if len(discovered) >= MAX_COMPETITORS:
                used_query = query
                break

            company_name = company.strip()

            company_key = company_name.lower()

            if company_key in seen_companies:
                continue

            official_url = get_official_website(
                company_name=company_name,
                industry=industry,
                state=state,
                country=country,
            )
            print(
                f"Verifying: {company_name} -> {official_url}"
            )

            if not official_url:
                continue

            website_key = official_url.lower()

            if website_key in seen_websites:
                continue

            location = ", ".join(
                part for part in [district, state, country]
                if part
            )

            discovered.append(
                {
                    "company_name": company_name,
                    "website_url": official_url,
                    "location": location,
                }
            )

            seen_companies.add(company_key)
            seen_websites.add(website_key)

        # If we found enough competitors,
        # stop fallback and return results.
        if len(discovered) >= MIN_COMPETITORS:
            used_query = query
            break

        # Save the latest query attempted
        used_query = query

    return {
        "query": used_query,
        "total_competitors": len(discovered),
        "competitors": discovered,
    }