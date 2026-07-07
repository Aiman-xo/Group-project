from app.models.competitor_model import Competitor
from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from app.core.logger import logger



async def get_competitor_datas(
    db:Session,
    page,
    limit
):
    try:
        page = int(page)
        limit = int(limit)
        
        offset = (page - 1) * limit
        competitors = db.query(Competitor).offset(offset).limit(limit).all()
        total = db.query(Competitor).count()

        return {
            'competitors':competitors,
            "total":total,
            "page":page,
            "limit":limit
        }
    except Exception as e:
        logger.error(f'Error fetching competitors: {e}')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Couldnt Fetch Competitors')