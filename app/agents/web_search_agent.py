from urllib.parse import urlparse

import os
import requests
from dotenv import load_dotenv
import json
import time
# from google import genai
from groq import Groq

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
# client = genai.Client(
#     api_key=os.getenv("GEMINI_API_KEY")
# )
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

OFFICIAL_WEBSITE_BLACKLIST = {
    "linkedin.com",
    "glassdoor.com",
    "ambitionbox.com",
    "indeed.com",
    "quora.com",
    "reddit.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    "signalhire.com",
    "zoominfo.com",
    "rocketreach.co",
    "builtin.com",
    "goodfirms.co",
    "techbehemoths.com",
    "aeroleads.com",
    "clutch.co",
     "academy",
    "careers",
    "jobs",
    "admissions",
    "zaubacorp.com",
    "tofler.in",
    "tracxn.com",
    "indiamart.com",
    "crunchbase.com",
    "f6s.com",
    "justdial.com",
}


def is_blacklisted(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower()
        domain = domain.replace("www.", "")

        return any(
            blocked in domain
            for blocked in OFFICIAL_WEBSITE_BLACKLIST
        )

    except Exception:
        return True


def build_queries(
    industry: str,
    country: str,
    state: str,
    district: str,
    limit: int = 10,
):
    """
    Build fallback queries.

    Priority:
    1. District
    2. State
    3. Country
    """

    queries = []

    if district:
        queries.append(
            f"Top {limit} {industry} organizations in "
            f"{district}, {state}, {country}"
        )

    if state:
        queries.append(
            f"Top {limit} {industry} organizations in "
            f"{state}, {country}"
        )

    if country:
        queries.append(
            f"Top {limit} {industry} organizations in "
            f"{country}"
        )

    return queries




def search_companies(query: str):
    """
    Search Google using Serper API
    and return combined text for Gemini.
    """

    combined_text = ""

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "q": query,
        "num": 6,
    }

    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers=headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("organic", [])

        print("\n===== SERPER RESULTS =====")

        for index, result in enumerate(results, start=1):

            title = result.get("title", "")
            snippet = result.get("snippet", "")
            url = result.get("link", "")

            print(f"\nResult {index}")
            print(f"Title : {title}")
            print(f"URL   : {url}")
            print(f"Body  : {snippet}")

            combined_text += f"""
Title:
{title}

URL:
{url}

Body:
{snippet}

------------------------
"""

        print("\n===== END SERPER RESULTS =====")

    except Exception as e:
        print(f"Serper search failed: {e}")

    return combined_text

#--------------------------------------------------#
COMPETITOR_DISCOVERY_PROMPT = """
You are VoxIntel's Competitor Discovery Agent.

You act as an experienced market research analyst.

Your goal is to identify the most relevant competitors for a business operating in a specified industry and location.

Responsibilities:
1. Extract ONLY real organizations.
2. Exclude government departments, government schemes, missions, ministries, public portals, regulatory bodies, government-owned organizations, and public-sector entities unless the industry itself is government-focused.
3. Prioritize organizations with an actual operational presence in the specified location.
4. Include both multinational companies operating in the location and major regional companies headquartered there.
5. Do not exclude local leaders simply because they are smaller than MNCs.
6. Ignore blogs, review sites, directories, social media pages, and generic infrastructure providers such as AWS, Azure, and Google Cloud unless they are genuine competitors in the specified industry.
7. If fewer than the requested number of valid competitors exist in the specified location, gradually expand the search to the state level and then country level while clearly prioritizing local competitors first.
8. Return ONLY valid JSON arrays.
9. Never explain your reasoning.
10. When a district or city is specified, strongly prioritize organizations physically located in that district or city.
11. Do not include national or multinational companies unless search results clearly show an office, branch, delivery center, or operational presence in the specified district or city.


Industry Guidance:
- IT: prioritize software companies, IT services firms, SaaS companies, technology consulting firms, and major regional tech companies.
- Healthcare: prioritize hospitals, clinics, healthcare providers, diagnostic centers, and healthcare networks. Include pharmaceutical companies only if they are major competitors in the specified location.
- Education: prioritize schools, colleges, universities, coaching institutions, and educational organizations.
- Retail: prioritize retail chains, supermarkets, e-commerce businesses, and consumer retail brands.
- Hospitality: prioritize hotels, resorts, tourism businesses, and hospitality service providers.
- Real Estate: prioritize builders, developers, and property management companies.
- Restaurants: prioritize restaurants, food chains, cafes, and dining businesses.
- Manufacturing: prioritize manufacturers, industrial companies, factories, production facilities, and major regional manufacturers.
- Logistics: prioritize logistics providers, transportation companies, courier services, warehousing companies, and supply chain organizations.
- Banking and Finance: prioritize banks, financial institutions, NBFCs, insurance providers, fintech companies, and digital banking providers.
- For industries not explicitly listed, infer the most relevant competitor types based on the industry context and location.

Location Relevance Rules:

1. Only include organizations that have a clear operational presence in the specified district, city, or location.
2. Exclude government departments, government schemes, missions, ministries, public portals, and regulatory bodies.
3. Exclude parent companies if a specific local branch, facility, office, hospital, campus, store, or operating unit exists in the specified location.
4. Exclude organizations whose primary presence is in another district, city, or state unless they have a confirmed operational presence in the specified location.
5. Prioritize organizations headquartered in the specified location.
6. If insufficient competitors exist in the specified location, gradually expand the search to the state level and then country level.
7. Prefer competitors that appear repeatedly across multiple search results and trusted sources.
8. Return only real operating organizations relevant to the specified industry.
9. Exclude directories, listing websites, review platforms, aggregators, informational portals, and industry associations.
10. If no valid competitors are found in the specified location, return an empty list.

"""

#--------------------------------------------------------------#

def extract_company_names(
    content: str,
    industry: str,
    country: str = "",
    state: str = "",
    district: str = "",
    limit: int = 6,
):
    """
    Use Groq  to extract prominent competitors
    from Serper search results.
    """

    if not content.strip():
        return "[]"

    location = ", ".join(
        [
            part
            for part in [district, state, country]
            if part
        ]
    )

    prompt = f"""


Goal:
Find the top {limit} competitors.

Industry:
{industry}

Location:
{location}


Output format:

[
    "Company 1",
    "Company 2"
]

Search Results:

{content}
"""

    for attempt in range(3):

        try:

            print(f"Prompt Length: {len(prompt)}")

            response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": COMPETITOR_DISCOVERY_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            )

            return (
                response.choices[0]
                .message.content
                .strip()
            )

        except Exception as e:

            print(
                f"Groq attempt {attempt+1}/3 failed: {e}"
            )

            if attempt < 2:
                time.sleep(3)

    return "[]"

def parse_company_response(
    response_text: str,
):
    """
    Convert Groq  JSON into Python list.
    """

    try:

        cleaned = (
            response_text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        companies = json.loads(cleaned)

        if not isinstance(companies, list):
            return []

        results = []
        seen = set()

        for company in companies:

            if not isinstance(company, str):
                continue

            company = company.strip()

            if not company:
                continue

            key = company.lower()

            if key in seen:
                continue

            seen.add(key)

            results.append(company)

        return results

    except Exception as e:

        print(
            f"Failed to parse Groq response: {e}"
        )

        return []
    
#------------------------------------------#

def get_official_website(
    company_name: str,
    industry: str,
    state: str = "",
    country: str = "",
):
    """
    Find official website using Serper.

    Strategy:
    1. Search Google for "<company> official website".
    2. Ignore blacklisted domains.
    3. Prefer domains matching the company name.
    4. Return homepage URL.
    """

    query = (
        f"{company_name} "
        f"{industry} "
        f"{state} "
        f"{country} "
        f"official website"
    )

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "q": query,
        "num": 10,
    }

    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers=headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("organic", [])

    except Exception as e:
        print(
            f"Official website lookup failed: {e}"
        )
        return None

    # company_key = (
    #     company_name.lower()
    #     .replace(" ", "")
    #     .replace(".", "")
    #     .replace("-", "")
    # )

    fallback_homepage = None

    print(f"\nVerifying website for: {company_name}")

    IGNORE_WORDS = {
        "it",
        "software",
        "softwares",
        "lab",
        "labs",
        "info",
        "infotech",
        "technologies",
        "technology",
        "solutions",
        "solution",
        "services",
        "service",
        "systems",
        "system",
        "private",
        "pvt",
        "ltd",
        "limited",
        "company",
        "inc",
        "hospital",
        "hospitals",
        "group",
    }


    for result in results:

        url = result.get("link")

        if not url:
            continue

        if is_blacklisted(url):
            continue

        parsed = urlparse(url)

        domain = (
            parsed.netloc.lower()
            .replace("www.", "")
        )

        homepage = (
            f"{parsed.scheme}://{domain}"
        )


        print(
            f"Checking: {homepage}"
        )

        # Best Match
      
        if fallback_homepage is None:
            fallback_homepage = homepage

        company_words = [
            word.lower()
            for word in company_name.split()
            if len(word) > 2
            and word.lower() not in IGNORE_WORDS
        ]

        score = sum(
            1
            for word in company_words
            if word in domain
        )

        required_score = 1

        if score >= required_score:
            print(
                f"Matched: {homepage}"
            )
            return homepage

    if fallback_homepage:
        print(
            f"Fallback used: {fallback_homepage}"
        )
        return fallback_homepage

    print(
        f"No valid official website found for {company_name}"
    )

    return None