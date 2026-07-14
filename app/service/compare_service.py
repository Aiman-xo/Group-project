from app.models.competetor_analyser import CompetitorComparison, CompetetorAnalyser
from app.agents.compare_agent import competitor_analyser_agent
from sqlalchemy.orm import Session
from sqlalchemy import UUID
from app.core.logger import logger
from sqlalchemy.exc import SQLAlchemyError


async def run_compare_agent(competitor_id: UUID, company_id: UUID, db: Session):

    print('====================================== Comparing agent called ======================================')
    try:
        
        competitor_analysis = (
            db.query(CompetetorAnalyser)
            .filter(CompetetorAnalyser.competitor_id == competitor_id)
            .order_by(CompetetorAnalyser.version.desc())
            .first()
        )
        if not competitor_analysis:
            logger.error(f"No competitor analysis record found for competitor_id: {competitor_id}")
            return {
                "message": "Comparison skipped: competitor analysis data not found."
            }

        print('====================================== Comparing started ======================================')
        
        llm_compare_output = await competitor_analyser_agent(competitor_id=competitor_id, company_id=company_id, db=db)

        
        existing = (
            db.query(CompetitorComparison)
            .join(CompetetorAnalyser, CompetitorComparison.competitor_id == CompetetorAnalyser.id)
            .filter(CompetetorAnalyser.competitor_id == competitor_id)
            .order_by(CompetitorComparison.version.desc())
            .first()
        )

        if not existing:
            new_compared_data = CompetitorComparison(
                competitor_id = competitor_analysis.id,
                competitor_name = llm_compare_output['competitor_name'],
                data_freshness_note = llm_compare_output['data_freshness_note'],
                positioning_gap = llm_compare_output['positioning_gap'],
                narrative_gap_analysis = llm_compare_output['narrative_gap_analysis'],
                reputation = llm_compare_output['reputation'],
                social_presence_gap = llm_compare_output['social_presence_gap'],
                trajectory = llm_compare_output['trajectory'],
                recommendations = llm_compare_output['recommendations'],
                version = 1,
                is_latest = True
            )

            db.add(new_compared_data)
            db.commit()
            return {
                'message':'new competitor comparison record added!'
            }

        # Deactivate all previous versions
        db.query(CompetitorComparison).filter(
            CompetitorComparison.competitor_id.in_(
                db.query(CompetetorAnalyser.id).filter(CompetetorAnalyser.competitor_id == competitor_id)
            )
        ).update({"is_latest": False}, synchronize_session=False)
        db.flush()

        # Cap versions at 3
        all_versions = db.query(CompetitorComparison).filter(
            CompetitorComparison.competitor_id.in_(
                db.query(CompetetorAnalyser.id).filter(CompetetorAnalyser.competitor_id == competitor_id)
            )
        ).order_by(CompetitorComparison.version.asc()).all()

        if len(all_versions) >= 3:
            db.delete(all_versions[0])
            db.flush()
        
        updated_compared_data = CompetitorComparison(
            competitor_id = competitor_analysis.id,
            competitor_name = llm_compare_output['competitor_name'],
            data_freshness_note = llm_compare_output['data_freshness_note'],
            positioning_gap = llm_compare_output['positioning_gap'],
            narrative_gap_analysis = llm_compare_output['narrative_gap_analysis'],
            reputation = llm_compare_output['reputation'],
            social_presence_gap = llm_compare_output['social_presence_gap'],
            trajectory = llm_compare_output['trajectory'],
            recommendations = llm_compare_output['recommendations'],
            version=existing.version + 1,
            is_latest=True,
        )
        db.add(updated_compared_data)
        db.commit()

        return {
            'message':'competitor record version updated and changed!'
        }
    
    except SQLAlchemyError as se:
        db.rollback()
        logger.error(f"Database error occurred while saving comparison data for competitor_id {competitor_id}: {str(se)}")
        return None
        
    except KeyError as ke:
        db.rollback()
        logger.error(f"Missing required key in llm_compare_output dictionary: {str(ke)}")
        return None
        
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in compare_service : {str(e)}")
        return None