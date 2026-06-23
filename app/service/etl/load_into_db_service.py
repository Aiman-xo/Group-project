from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.competetor_analyser import CompetetorAnalyser
from app.models.company_model import ProfileDataAnalyser,Company
from app.core.logger import logger

def load_competitor_data_to_db(llm_output:dict,db:Session,competitor_id:str):
    try:
        existing = db.query(CompetetorAnalyser).filter(CompetetorAnalyser.competitor_id == competitor_id).order_by(CompetetorAnalyser.version.desc()).first()

        if not existing:
            new_analysis_record = CompetetorAnalyser(
                competitor_id = competitor_id,
                competitor_name = llm_output['competitor_name'],
                source_file = llm_output['source_file'],
                products = llm_output['products'],
                services = llm_output['services'],
                github = llm_output['github'],
                linkedin = llm_output['linkedin'],
                youtube = llm_output['youtube'],
                facebook = llm_output['facebook'],
                email = llm_output['email'],
                phone = llm_output['phone'],
                summary_text = llm_output['summary'],
                version=1,
                is_latest=True,
            )

            db.add(new_analysis_record)
            db.commit()
            return {
                'message':'new competitor record added!'
            }

        existing.is_latest = False

        # Cap versions at 3: delete the oldest record to keep history lean
        all_versions = db.query(CompetetorAnalyser).filter(
            CompetetorAnalyser.competitor_id == competitor_id
        ).order_by(CompetetorAnalyser.version.asc()).all()
        if len(all_versions) >= 3:
            db.delete(all_versions[0])
            db.flush()

        updated_analysis_record = CompetetorAnalyser(
            competitor_id = competitor_id,
            competitor_name = llm_output['competitor_name'],
            source_file = llm_output['source_file'],
            products = llm_output['products'],
            services = llm_output['services'],
            github = llm_output['github'],
            linkedin = llm_output['linkedin'],
            youtube = llm_output['youtube'],
            facebook = llm_output['facebook'],
            email = llm_output['email'],
            phone = llm_output['phone'],
            summary_text = llm_output['summary'],
            version=existing.version + 1,
            is_latest=True,
        )

        db.add(updated_analysis_record)
        db.commit()

        return{
            'message':'competitor record version updated and changed!'
        }

    except SQLAlchemyError as se:
        # 2. Critical for Databases: Roll back the transaction if database errors happen
        db.rollback()
        logger.error(f"Database error occurred while saving analysis for {competitor_id}: {str(se)}")
        return None
        
    except KeyError as ke:
        # 3. Handle data bugs gracefully if the LLM missing expected keys
        db.rollback()
        logger.error(f"Missing required key in llm_output dictionary: {str(ke)}")
        return None
        
    except Exception as e:
        # 4. Global catch-all wrapper to prevent worker threads from crashing
        db.rollback()
        logger.error(f"Unexpected error in load_data_to_db pipeline: {str(e)}")
        return None        
    

# =====================================================================================================================================
# SAVE TRANSFORMED DATA INTO PROFILEDATAANALYSER MODEL

def load_profile_data_to_db(llm_output:dict,db:Session,company_id:str=None):
    print('Called load into the db function=================================>>>>')
    try:
        existing_record = db.query(ProfileDataAnalyser).filter(ProfileDataAnalyser.company_id == company_id).order_by(ProfileDataAnalyser.version.desc()).first()

        if not existing_record:
            new_record = ProfileDataAnalyser(
                company_id = company_id,
                source_file = llm_output['source_file'],
                products = llm_output['products'],
                services = llm_output['services'],
                github = llm_output['github'],
                linkedin = llm_output['linkedin'],
                youtube = llm_output['youtube'],
                facebook = llm_output['facebook'],
                email = llm_output['email'],
                phone = llm_output['phone'],
                summary_text = llm_output['summary'],
                version=1,
                is_latest=True,
            )

            db.add(new_record)
            db.commit()
            return {
                'message':'new profile record added!'
            }

        existing_record.is_latest = False

        # Cap versions at 3: delete the oldest record to keep history lean
        all_versions = db.query(ProfileDataAnalyser).filter(
            ProfileDataAnalyser.company_id == company_id
        ).order_by(ProfileDataAnalyser.version.asc()).all()
        if len(all_versions) >= 3:
            db.delete(all_versions[0])
            db.flush()

        updated_analysis_record = ProfileDataAnalyser(
            company_id = company_id,
            source_file = llm_output['source_file'],
            products = llm_output['products'],
            services = llm_output['services'],
            github = llm_output['github'],
            linkedin = llm_output['linkedin'],
            youtube = llm_output['youtube'],
            facebook = llm_output['facebook'],
            email = llm_output['email'],
            phone = llm_output['phone'],
            summary_text = llm_output['summary'],
            version=existing_record.version + 1,
            is_latest=True,
        )

        db.add(updated_analysis_record)
        db.commit()

        return{
            'message':'profile record version updated and changed!'
        }




    except SQLAlchemyError as se:
        # 2. Critical for Databases: Roll back the transaction if database errors happen
        db.rollback()
        logger.error(f"Database error occurred while saving analysis for  {str(se)}")
        return None
    
    except KeyError as ke:
        # 3. Handle data bugs gracefully if the LLM missing expected keys
        db.rollback()
        logger.error(f"Missing required key in llm_output dictionary: {str(ke)}")
        return None
        
    except Exception as e:
        # 4. Global catch-all wrapper to prevent worker threads from crashing
        db.rollback()
        logger.error(f"Unexpected error in load_data_to_db pipeline: {str(e)}")
        return None  