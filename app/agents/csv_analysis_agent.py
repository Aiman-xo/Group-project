import json
from groq import AsyncGroq
from app.core.config import GROQ_API_KEY
from app.utils.progress_tracker import update_csv_file_upload_progress



client = AsyncGroq(api_key=GROQ_API_KEY)
async def csv_analysis_agent(new_data:list , previous_data:list, company_slug:str, category:str):
    category_label = category.replace("_", " ").title() 
    if previous_data:
        user_prompt = f"""
    You are analyzing {category_label} performance data for an EdTech company.

    You have been given TWO versions of their {category_label} data:

    PREVIOUS VERSION:
    {json.dumps(previous_data, indent=2)}

    CURRENT VERSION:
    {json.dumps(new_data, indent=2)}

    Compare these two {category_label} datasets and provide:
    1. Overall growth or decline summary specific to {category_label}
    2. Which {category_label} metrics improved and by how much
    3. Which {category_label} metrics declined and by how much
    4. Key {category_label} problem areas that need attention
    5. Specific actionable recommendations based on the comparison
    6. Overall {category_label} health score (1-10) with justification
    """
    else:
        user_prompt = f"""
    You are analyzing {category_label} performance data for an EdTech company.

    This is their FIRST {category_label.upper()} DATA UPLOAD — no previous version exists for comparison.

    CURRENT DATA:
    {json.dumps(new_data, indent=2)}

    Analyze this {category_label} dataset and provide:
    1. Overall {category_label} performance summary
    2. Key strengths visible in the data
    3. Key weaknesses or problem areas
    4. Which metrics need immediate attention
    5. Specific actionable recommendations to improve {category_label} performance
    6. Overall {category_label} health score (1-10) with justification
    """

    system_prompt = f"""
        You are an expert business analyst specializing in EdTech companies.
        You are specifically analyzing their {category_label} data — focus your
        analysis, terminology, and recommendations on what matters for {category_label}
        (for example: for Sales data focus on revenue, conversion, deal velocity;
        for Production data focus on output, throughput, defect rates;
        for Inventory focus on stock levels, turnover, wastage — adapt to whatever
        metrics actually appear in the given data for this category).

        Your job is to analyze performance data and provide clear, actionable insights.
        Always be specific — reference actual numbers from the data, not vague generalities.
        Structure your response as a JSON object with these exact keys:
        {{
            "summary": "overall summary string",
            "growth_areas": ["list of areas that grew or are strong"],
            "problem_areas": ["list of areas that declined or need attention"],
            "recommendations": ["list of specific actionable recommendations"],
            "health_score": <integer 1-10>,
            "health_score_reason": "justification string",
            "metric_changes": {{
                "<metric_name>": {{
                    "previous": <number or null if first version>,
                    "current": <number>,
                    "change_percent": <float or null if first version>,
                    "trend": "up" | "down" | "stable"
                }}
            }}
        }}
        Return ONLY valid JSON, no extra text, no markdown backticks.
        """
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,  # lower = more consistent, less creative — good for analysis
    )
    update_csv_file_upload_progress(company_slug,80,'Calling llm model ...')
    raw_output = response.choices[0].message.content
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        import re
        # Stripping down the ``` json ``` markdown
        match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            raise ValueError(f"LLM returned non-JSON output: {raw_output}")
