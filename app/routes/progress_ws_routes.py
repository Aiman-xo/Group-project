import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as redis
from app.core.config import REDIS_URL

router = APIRouter(tags=["Progress WebSocket"])

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)


@router.websocket("/ws/progress/{company_id}")
async def websocket_progress(websocket: WebSocket, company_id: str):
    await websocket.accept()

    try:
        last_sent = None

        while True:
            progress_data = await redis_client.get(
                f"crawl_progress:{company_id}"
            )

            if progress_data and progress_data != last_sent:
                await websocket.send_text(progress_data)
                last_sent = progress_data

                parsed = json.loads(progress_data)

                # stop when completed or failed
                if parsed["progress"] in [100, -1]:
                    await redis_client.delete(f"crawl_progress:{company_id}")
                    break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for {company_id}")

    finally:
        await websocket.close()

@router.websocket('/ws/progress/etl/{company_slug}')
async def etl_websocket_progress(websocket:WebSocket, company_slug:str):
    await websocket.accept()

    try:
        last_sent = None

        while True:
            progress_data = await redis_client.get(
                f"etl_progress:{company_slug}"
            )

            if progress_data and progress_data != last_sent:
                await websocket.send_text(progress_data)
                last_sent = progress_data

                parsed = json.loads(progress_data)

                # stop when completed or failed
                if parsed["progress"] in [100, -1]:
                    await redis_client.delete(f"etl_progress:{company_slug}")
                    break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for {company_slug}")

    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass


# CSV upload progress tracker websocket route
@router.websocket('/ws/progress/csv_upload/{company_slug}')
async def csv_upload_websocket_progress(websocket:WebSocket, company_slug:str):
    await websocket.accept()

    try:
        last_sent = None

        while True:
            progress_data = await redis_client.get(
                f"csv_upload:{company_slug}"
            )

            if progress_data and progress_data != last_sent:
                await websocket.send_text(progress_data)
                last_sent = progress_data

                parsed = json.loads(progress_data)

                # stop when completed or failed
                if parsed["progress"] in [100, -1]:
                    await redis_client.delete(f"csv_upload:{company_slug}")
                    break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for {company_slug}")

    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass