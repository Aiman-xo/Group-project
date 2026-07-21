from groq import AsyncGroq,GroqError
from app.core.logger import logger
import json
from app.core.config import GROQ_API_KEY



async def transform(raw_data: dict):
    """
    raw_data: dict with keys:
        'raw_data'    -> the raw text extracted from the file
        'source_file' -> the original file path
    """

    client = AsyncGroq(api_key=GROQ_API_KEY)
    raw_response_json_data = None

    try:
        response = await client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            max_tokens=1024,
            response_format={'type':'json_object'},
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert Market Intelligence and Data Extraction AI. Your task is to process raw, "
                        "unstructured content from multiple sources about a competitor — website content, review/rating "
                        "aggregator data, and community discussion data — and extract precise, structured data.\n\n"
                        "CRITICAL RULES:\n"
                        "1. Extract ONLY information explicitly stated in the provided text. Never hallucinate or invent details.\n"
                        "2. If a specific field (like a URL, email, phone, or rating) is not present in the text, return null "
                        "for that field (or an empty array [] for list fields). Do not make up plausible values.\n"
                        "3. For 'products' and 'services', distinguish carefully:\n"
                        "   - Products: Tangible goods, software platforms, tools, or physical items sold.\n"
                        "   - Services: Consulting, custom development, support, training, or solutions provided.\n"
                        "4. Some input sources may indicate failure or contain zero results (e.g. a status field showing "
                        "'all_sources_failed', or empty insight lists). Treat these as having no data — do not invent "
                        "content to fill that section.\n"
                        "5. Distinguish direct company claims (from the company's own website) from third-party statements "
                        "(from review platforms or community discussions). Do not blend review-site or community commentary "
                        "into 'summary' as if it were the company's own claim — keep 'summary' focused on who they are and "
                        "what they do, and route reputation/sentiment data into the dedicated fields instead.\n"
                        "6. For 'rating_score', extract the numeric value exactly as stated (e.g. '4.1'), as a string. "
                        "If multiple conflicting scores appear across sources, use the most recent or most frequently "
                        "repeated one.\n"
                        "7. For 'positive_themes' and 'negative_themes', extract short recurring themes (e.g. 'good work "
                        "culture', 'below-market pay'), not full quoted sentences."
                    )
                },
                # "industries_served": ["List of industries/sectors they target, e.g. Telecom, Healthcare. Return empty array [] if none found."],
                {
                    "role": "user",
                    "content": f"""
                    Analyze the raw competitor content provided below and extract the information into a valid JSON object matching the exact schema specifications.

                    ### RAW CONTENT TO ANALYZE:
                    ---
                    {raw_data['raw_data']}
                    ---

                    ### TARGET JSON SCHEMA:
                    {{
                    "company_name": "Official name of the company or entity described in the content."
                    "summary": "A detailed 2-3 paragraph professional summary of who they are, their market positioning, and what they do, based only on their own website/company content.",
                    "products": ["List of distinct products, platforms, or tools they offer. Return empty array [] if none found."],
                    "services": ["List of capabilities, consulting offerings, or professional services they provide. Return empty array [] if none found."],
                    
                    "github": "The absolute GitHub organization/user URL, or null if missing.",
                    "youtube": "The absolute YouTube channel URL, or null if missing.",
                    "linkedin": "The absolute LinkedIn company/personal URL, or null if missing.",
                    "facebook": "The absolute Facebook page URL, or null if missing.",
                    "instagram": "The absolute Instagram URL, or null if missing.",
                    "email": "The primary contact email address found, or null if missing.",
                    "phone": "The primary contact phone number found, or null if missing.",
                    "rating_score": "Numeric rating as stated (e.g. '4.1'), as a string, or null if none found.",
                    "total_reviews": "Total review count as an integer, or null if none found.",
                    "review_source": "Name of the platform reviews came from, e.g. AmbitionBox, or null if none found.",
                    "positive_themes": ["Short recurring positive themes from reviews. Return empty array [] if none found."],
                    "negative_themes": ["Short recurring negative/constructive themes from reviews. Return empty array [] if none found."],
                    "community_insights": ["Notable discussion points or sentiments from community sources like Reddit. Return empty array [] if none found or if the source indicates failure."]
                    }}

                    Return ONLY the raw JSON object. Do not include markdown formatting code blocks like ```json ... ```. Ensure the JSON is completely valid and parseable.
                    """
                }]
        )

        raw_response_json_data = response.choices[0].message.content

        # this returns the result as a python dictionary
        parsed_data = json.loads(raw_response_json_data)
        parsed_data["source_file"] = raw_data['source_file']
        return parsed_data

    except GroqError as ge:
        logger.error(f'GROQ API ERROR OCCURED {str(ge)}')
        return None
    
    except json.JSONDecodeError as je:
        # Catches cases where the model returns an incomplete or broken JSON string
        logger.error(f"Failed to parse LLM response as JSON. Raw data: {raw_response_json_data}. Error: {str(je)}")
        return None
    
    except Exception as e:
        # Catch-all for unexpected index errors or unexpected system bugs
        logger.error(f"An unexpected error occurred during transform: {str(e)}")
        return None
