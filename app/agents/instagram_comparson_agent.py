import json
from groq import AsyncGroq
from app.core.config import GROQ_API_KEY

client = AsyncGroq(api_key=GROQ_API_KEY)
async def instagram_comparing_agent(registered_company_insta_stats:dict,competitor_insta_stats:dict):
    system_prompt = """You are a competitive social media intelligence analyst.
        You will receive precomputed Instagram statistics for two accounts: a registered
        company and one of its competitors. Both inputs are already-aggregated summaries,
        not raw post data.

        Your job:
        1. Compare the two accounts across engagement, content strategy, posting focus,
        and audience size.
        2. Identify concrete gaps and opportunities for the registered company relative
        to the competitor.
        3. Separately, summarize only the competitor's noteworthy individual traits
        (their strongest content angle, what's driving their top-performing post,
        dominant themes/hashtags) — skip anything unremarkable or redundant with
        the comparison section.

        Respond with ONLY valid JSON matching this schema, no prose outside the JSON:

        {
        "comparison": {
            "engagement_gap": "string",
            "content_strategy_gap": "string",
            "audience_gap": "string",
            "positioning_summary": "string",
            "recommendations": ["string", "string"]
        },
        "competitor_highlights": {
            "strongest_content_type": "string",
            "standout_themes": ["string"],
            "top_post_insight": "string",
            "notable_traits": ["string"]
        }
        }
    """
    user_prompt = json.dumps({
        "registered_company": registered_company_insta_stats,
        "competitor": competitor_insta_stats
    }, indent=2)

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    
    raw_output = response.choices[0].message.content
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        import re
        # Stripping down the ``` json ``` markdown
        match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                raise ValueError(f"LLM returned unparseable JSON: {raw_output}")
        else:
            raise ValueError(f"LLM returned non-JSON output: {raw_output}")