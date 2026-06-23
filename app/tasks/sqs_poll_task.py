# app/tasks/sqs_poll_task.py

import boto3
from app.core.celery_config import celery_app
from app.core.logger import logger
from app.core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    SQS_QUEUE_URL
)
from app.tasks.s3_event_handle_task import handle_s3_event_trigger

sqs = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

@celery_app.task(name="etl.poll_sqs_queue")
def poll_sqs_queue():
    logger.info("Polling SQS queue...")

    response = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=5,
    )

    messages = response.get("Messages", [])

    if not messages:
        logger.info("No messages in queue.")
        return

    for msg in messages:
        body           = msg["Body"]
        receipt_handle = msg["ReceiptHandle"]

        # dispatch each message to its own worker
        handle_s3_event_trigger.delay(body)
        logger.info("Dispatched message to handle_s3_event")

        # delete from SQS immediately so no duplicate processing
        sqs.delete_message(
            QueueUrl=SQS_QUEUE_URL,
            ReceiptHandle=receipt_handle
        )