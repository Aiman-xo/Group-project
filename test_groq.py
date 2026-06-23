# test_groq.py

from app.agents.web_search_agent import (
    search_companies,
    extract_company_names,
)

query = "Top 6 IT organizations in Kozhikode, Kerala, India"

content = search_companies(query)

response = extract_company_names(
    content=content,
    industry="IT",
    district="Kozhikode",
    state="Kerala",
    country="India",
)

print(response)