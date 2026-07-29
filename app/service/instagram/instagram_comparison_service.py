from app.models.company_model import Company
from app.models.competitor_model import Competitor
from fastapi import HTTPException,status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.tasks.instagram_comparison_task import process_instagram_comparison
from uuid import UUID


def instagram_comparison_service(competitor_id:UUID,db:Session,current_company:Company):
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail='couldnt find competitor!')
    try:
        current_company_slug = current_company.slug
        competitor_slug = competitor.slug

        process_instagram_comparison.delay(current_company_slug,competitor_slug)

        return {'message':'comparing... please wait....'}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail='something went wrong')
