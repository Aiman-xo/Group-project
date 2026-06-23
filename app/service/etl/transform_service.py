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
            model='llama-3.1-8b-instant',
            max_tokens=1024,
            response_format={'type':'json_object'},
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert Market Intelligence and Data Extraction AI. Your task is to process raw, "
                        "unstructured text content from a competitor's web page or profile and extract precise, structured data.\n\n"
                        "CRITICAL RULES:\n"
                        "1. Extract ONLY information explicitly stated in the provided text. Never hallucinate or invent details.\n"
                        "2. If a specific field (like a URL, email, or phone number) is not present in the text, return null for that field. Do not make up plausible links.\n"
                        "3. For 'products' and 'services', distinguish carefully:\n"
                        "   - Products: Tangible goods, software platforms, tools, or physical items sold.\n"
                        "   - Services: Consulting, custom development, support, training, or solutions provided.\n"
                        "4. For social media links and contact info, scan thoroughly. Ensure URLs are fully formed if present."
                    )
                },
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
                    "competitor_name": "Official name of the company or competitor.",
                    "summary": "A detailed 2-3 paragraph professional summary of who they are, their market positioning, and what they do based on the text.",
                    "products": ["List of distinct products, platforms, or tools they offer. Return empty array [] if none found."],
                    "services": ["List of capabilities, consulting offerings, or professional services they provide. Return empty array [] if none found."],
                    "github": "The absolute GitHub organization/user URL, or null if missing.",
                    "youtube": "The absolute YouTube channel URL, or null if missing.",
                    "linkedin": "The absolute LinkedIn company/personal URL, or null if missing.",
                    "facebook": "The absolute Facebook page URL, or null if missing.",
                    "email": "The primary contact email address found, or null if missing.",
                    "phone": "The primary contact phone number found, or null if missing."
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
