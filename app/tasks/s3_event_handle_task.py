# app/tasks/etl_tasks.py

from app.core.celery_config import celery_app
from app.utils.s3_filepath_extractor import extract_s3_metadata
# from app.service.etl.etl_pipeline_service import run_etl_pipeline
from app.tasks.process_etl_files import process_etl_file
from app.core.logger import logger
from app.core.config import REDIS_URL
import asyncio
import json
import redis as redis_client
from redis.retry import Retry
from redis.backoff import ExponentialBackoff


# ── Redis client (separate from Celery broker) ──────────────────────────
r = redis_client.from_url(REDIS_URL, ssl_cert_reqs=None, socket_timeout=10,
    socket_connect_timeout=10,
    socket_keepalive=True,
    retry_on_timeout=True,
    protocol=2,
    retry=Retry(ExponentialBackoff(), 3)
    
    )

EXPECTED_FILES = {
    "admin": 3,
    "competitor": 3,
}

# ────────────────────────────────────────────────────────────────────────
# TASK 1 — Called per SQS message (1 file at a time)

@celery_app.task(
    name="etl.handle_s3_event",
    bind=True,
    max_retries=3,
    default_retry_delay=30
)
def handle_s3_event_trigger(self,message_body:str):
    try:
        body = json.loads(message_body)
        records = body.get("Records") or body.get("RECORDS") or []

        if not records:
            logger.warning('SQS message had no Records, skipping...')
            return
        
        # This returns a dictionary with slug and folder_type ie admin/competitor.
        extracted_datas = extract_s3_metadata(records)
        if not extracted_datas:
            logger.warning("extract_s3_metadata returned None — bad S3 path, skipping message.")
            return
        logger.info(f"Received file: {extracted_datas['file_key']} | company: {extracted_datas['slug']} | folder: {extracted_datas['folder_type']}")

        if extracted_datas['folder_type'] == 'competitor' and extracted_datas['competitor_slug']:
            group_key = f"pending : {extracted_datas['slug']}:{extracted_datas['folder_type']}:{extracted_datas['competitor_slug']}"
            lock_key  = f"lock : {extracted_datas['slug']}:{extracted_datas['folder_type']}:{extracted_datas['competitor_slug']}"
        else:
            group_key = f"pending : {extracted_datas['slug']}:{extracted_datas['folder_type']}"
            lock_key  = f"lock : {extracted_datas['slug']}:{extracted_datas['folder_type']}"

        # push file into redis list
        r.rpush(group_key, extracted_datas['file_key'])
        r.expire(group_key, 3600)  # cleanup after 1 hour if stuck

        arrived = r.llen(group_key)
        expected = EXPECTED_FILES.get(extracted_datas['folder_type'], 3)

        logger.info(f"[{extracted_datas['slug']}/{extracted_datas['folder_type']}] {arrived}/{expected} files arrived")


        if arrived >= expected:
            # acquire lock — only one worker can win this
            # Lock is needed here because:
            # When file 3 arrives, TWO workers might BOTH see count=3
            # at the exact same millisecond and BOTH try to trigger ETL.
            # nx=True ensures only the FIRST worker that reaches here
            # can trigger ETL — the second worker gets None and skips.
            # This prevents duplicate ETL runs for the same company.
            lock_acquired = r.set(lock_key, "locked", nx=True, ex=60)

            if lock_acquired:
                all_files = [f.decode() for f in r.lrange(group_key, 0, -1)]
                r.delete(group_key)
                logger.info(f"All files collected for {extracted_datas['slug']}, triggering ETL: {all_files}")
                process_etl_file.delay(extracted_datas['slug'], extracted_datas['folder_type'], all_files, extracted_datas['competitor_slug'])
            else:
                logger.info(f"ETL already triggered for {extracted_datas['slug']}/{extracted_datas['folder_type']}, skipping duplicate.")

    except Exception as e:
        logger.error(f"handle_s3_event failed: {str(e)}")
        raise self.retry(exc=e)

