import json

# THESE ARE THE FIELDS ARE BEING CHECKED BY THE LLM
DIFFABLE_FIELDS = {
    "services", "products",
    "positive_themes", "negative_themes", "community_insights",
    "github", "linkedin", "youtube", "facebook", "instagram",
    "email", "phone", "rating_score", "total_reviews", "review_source"
}

# This utility function checks all the fields and detect if there is any changes if changed it add to the result object/dict and returns that dict.
# In this way we can reduce the token usage by removing duplicate field datas again and again giving to the llm model.
# Here it filters only fields that are changed.
def diff_versions(versions: list[dict]) -> dict:
    if not versions:
        return {}

    result = {"latest": versions[0], "changes": []}

    for i in range(len(versions) - 1):
        newer, older = versions[i], versions[i + 1]
        changed_fields = {
            key: {"from": older.get(key), "to": newer[key]}
            for key in DIFFABLE_FIELDS
            if newer.get(key) != older.get(key)
        }

        if changed_fields:
            result["changes"].append({
                "version": newer["version"],
                "date": str(newer["created_at"]),
                "changed": changed_fields
            })

    return result

# Here we are actually creating the user prompt with correct datas to be give to the llm 
# This sets up the competitor name and all the changed datas and pass directly to the llm in the agents/competitor_agent.py
def build_user_message(competitor_name: str, competitor_payload: dict, company_payload: dict) -> str:

    competitor_latest = competitor_payload.get("latest", {})
    company_latest = company_payload.get("latest", {})
    competitor_last_updated = competitor_latest.get("created_at", "unknown")

    return f"""Competitor name: {competitor_name}
        Competitor last updated: {competitor_last_updated}

        COMPETITOR — Current State:
        {json.dumps(competitor_latest, indent=2)}

        COMPETITOR — Change History:
        {json.dumps(competitor_payload.get("changes", []), indent=2)}

        OUR COMPANY — Current State:
        {json.dumps(company_latest, indent=2)}

        OUR COMPANY — Change History:
        {json.dumps(company_payload.get("changes", []), indent=2)}
    """

# What this function do is that this is a safety check that means whenever we say to an llm model to return the result in jsn sometimes it returns excellently
# But sometimes it returns with ``` json key:{} ``` this type of format so this function removes that header section and only returns proper json
def parse_llm_json(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned.strip())