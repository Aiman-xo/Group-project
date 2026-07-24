from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.core.config import (
    INSTAGRAM_APP_ID,
    INSTAGRAM_REDIRECT_URI,
)

router = APIRouter(
    prefix="/instagram",
    tags=["Instagram"]
)


@router.get("/connect")
async def connect_instagram():

    params = {
        "client_id": INSTAGRAM_APP_ID,
        "redirect_uri": INSTAGRAM_REDIRECT_URI,
        "response_type": "code",
        "scope": "instagram_business_basic,instagram_business_manage_insights",
    }

    auth_url = (
        "https://www.instagram.com/oauth/authorize?"
        + urlencode(params)
    )

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def instagram_callback(
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_reason: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
):
    # Temporary callback only for testing OAuth.
    # Do NOT exchange/store tokens yet.

    if error:
        return {
            "success": False,
            "error": error,
            "error_reason": error_reason,
            "error_description": error_description,
        }

    if not code:
        return {
            "success": False,
            "message": "Instagram did not return an authorization code.",
        }

    return {
        "success": True,
        "message": "Instagram authorization successful.",
        "code_received": True,
    }