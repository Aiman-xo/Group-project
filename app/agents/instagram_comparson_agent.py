import json
from groq import AsyncGroq
from app.core.config import GROQ_API_KEY

client = AsyncGroq(api_key=GROQ_API_KEY)
async def instagram_comparing_agent(registered_company_insta_stats:dict,competitor_insta_stats:dict):
    system_prompt = """You are a competitive social media intelligence analyst.
        You will receive precomputed Instagram statistics for two accounts: a registered
        company and one of its competitors. Each input includes aggregated metrics
        (engagement rate, content-type performance, posting frequency, hashtag usage)
        AND a trimmed list of recent individual posts for reference — you can cite
        specific posts/captions/hashtags directly when relevant.

        All numeric fields are precomputed exactly from the underlying data — treat
        them as ground truth. Do not recompute, estimate, or override them; use them
        as given.

        Note on engagement_rate: for accounts with a small follower base, this figure
        can exceed 100% (average engagement per post is larger than the follower
        count). Values over 100% are not necessarily a positive signal — they can
        indicate an unusually engaged small audience OR inflated/inauthentic
        engagement (bots, engagement pods, purchased likes). If you see a value over
        100%, flag this ambiguity explicitly rather than treating it as straightforwardly
        excellent performance.

        Your job:
        1. Write a brief (2-3 sentence) overall summary of how the registered company
        stacks up against the competitor on Instagram — the single most important
        takeaway, in plain language a non-technical founder could skim in seconds.
        2. Compare the two accounts across engagement, content strategy, posting
        frequency/cadence (use posting_frequency_per_week), and audience size.
        3. Use content_type_performance (avg likes/comments per post type: Video,
        Image, Sidecar, etc.) to identify which specific content format is driving
        the competitor's engagement, and compare it against the registered
        company's own content_type_performance.
        4. Identify concrete gaps and opportunities for the registered company
        relative to the competitor.
        5. Based specifically on which content type/format performs best for the
        competitor (per content_type_performance and their top posts), recommend
        concrete content formats or themes the registered company could test —
        grounded in what is demonstrably working for the competitor, not generic
        social media advice.
        6. Separately, summarize only the competitor's noteworthy individual traits
        (their strongest content angle, what's driving their top-performing post,
        dominant themes/hashtags) — skip anything unremarkable or redundant with
        the comparison section.

        Respond with ONLY valid JSON matching this schema, no prose outside the JSON:

        {
        "summary": "string",
        "comparison": {
            "engagement_gap": "string",
            "content_strategy_gap": "string",
            "audience_gap": "string",
            "posting_cadence_gap": "string",
            "positioning_summary": "string",
            "recommendations": ["string", "string"]
        },
        "content_recommendations": ["string", "string"],
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