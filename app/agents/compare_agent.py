from fastapi import HTTPException,status
from app.models.company_model import ProfileDataAnalyser
from app.models.competetor_analyser import CompetetorAnalyser
from sqlalchemy.orm import Session
from app.core.logger import logger
from groq import AsyncGroq
from app.core.config import GROQ_API_KEY
from app.schemas.analysis_schema import CompareAnalysisSchema
from app.utils.compare_agent_utils import diff_versions,build_user_message,parse_llm_json

# from app.core.multitenancy import get_authorized_tenant_db, get_current_company

client = AsyncGroq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a competitive intelligence analyst producing a report for a CEO and marketing team who have limited time to read it. Be direct, specific, and avoid generic filler. Every claim must be traceable to the data provided — do not invent facts.

Your task:
1. Structured comparison: compare services, products, social presence, and reputation fields between the two companies' current states. Identify what the competitor has that we don't, what we have that they don't, and overlap.
2. Narrative comparison: both sides include a full summary_text (latest version). Identify capability/positioning claims present in one summary but not the other's summary or structured fields, and differences in tone/positioning. Do NOT treat wording differences as meaningful — only substance.
3. Reputation analysis: compare ratings and themes. Identify exploitable weaknesses in the competitor and risk areas in our own standing.
4. Trajectory: using change history, describe the direction each company appears to be moving in. Only draw conclusions the change history supports.
5. Recommendations: give 3-5 specific, prioritized actions, each tied to a finding above. No generic advice.
6. Note the competitor data's most recent update date.

Return ONLY valid json, no markdown formatting, no code fences, no preamble. If any field has no supporting data, use an empty array or "insufficient data" rather than fabricating content.

Match this exact json structure:
{
  "competitor_name": "...",
  "data_freshness_note": "competitor data last updated <date>, may not reflect recent changes",
  "positioning_gap": {"competitor_has_we_dont": [], "we_have_competitor_doesnt": [], "overlap": []},
  "narrative_gap_analysis": {"competitor_summary_highlights": "", "our_summary_highlights": "", "things_they_have_we_dont": [], "things_we_have_they_dont": [], "tone_and_positioning_difference": ""},
  "reputation": {"us": {"rating": "", "praised_for": [], "criticized_for": []}, "competitor": {"rating": "", "praised_for": [], "criticized_for": []}, "exploitable_weakness": "", "our_risk_area": ""},
  "social_presence_gap": {"competitor_active_on": [], "we_active_on": [], "channels_competitor_has_we_lack": []},
  "trajectory": [{"date": "", "change": "", "signal": ""}],
  "recommendations": [{"action": "", "why": "", "priority": "high|medium|low"}]
}
"""

async def competitor_analyser_agent(competitor_id:str, company_id:str, db:Session):

    try:
        competitor_datas = db.query(CompetetorAnalyser).filter(CompetetorAnalyser.competitor_id == competitor_id).order_by(CompetetorAnalyser.version.desc()).all()
        registered_company_data = db.query(ProfileDataAnalyser).filter(ProfileDataAnalyser.company_id == company_id).order_by(ProfileDataAnalyser.version.desc()).all()

        if not competitor_datas or not registered_company_data:
            raise HTTPException(status_code=404, detail="No analysis history found")
        
        competitor_name = competitor_datas[0].competitor_name or "Unknown Competitor"
        
        competitor_json_data = [
            CompareAnalysisSchema.model_validate(row).model_dump(mode="json")
            for row in competitor_datas
        ]
        company_json_data = [
            CompareAnalysisSchema.model_validate(row).model_dump(mode="json")
            for row in registered_company_data
        ]

        competitor_payload = diff_versions(competitor_json_data)
        company_payload = diff_versions(company_json_data)

        user_message = build_user_message(competitor_name, competitor_payload, company_payload)

        response = await client.chat.completions.create(
            model='meta-llama/llama-4-scout-17b-16e-instruct',
            max_tokens=1024,
            response_format={'type':'json_object'},
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]
        )

        result = parse_llm_json(response.choices[0].message.content)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'couldnt fetch datas {e}')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f'couldnt fetch datas {e}')

