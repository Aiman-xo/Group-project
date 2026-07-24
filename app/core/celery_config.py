# app/core/celery_app.py

import os
# Disable macOS fork safety check to prevent crash when billiard/celery forks workers
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

from celery import Celery
import ssl
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "group_project",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL"),
    include=[
        "app.tasks.s3_event_handle_task",
        "app.tasks.process_etl_files",
        "app.tasks.sqs_poll_task",
        "app.tasks.process_csv_file_task"
        ]   # ← where your tasks live
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,    # lets you see when task is picked u

    broker_use_ssl={
        "ssl_cert_reqs": ssl.CERT_NONE 
    },
    redis_backend_use_ssl={
        "ssl_cert_reqs": ssl.CERT_NONE 
    },
    broker_transport_options={
        "socket_timeout": 10,
        "socket_connect_timeout": 10,
        "retry_on_timeout": True,
    },
    # ── SQS Polling via Celery Beat ─────────────────────────────────────────

    beat_schedule={
        "poll-sqs-every-30-seconds": {
            "task": "etl.poll_sqs_queue",   # ← polling task (below)
            "schedule": 30.0,               # every 30 seconds
        }
    }
)

