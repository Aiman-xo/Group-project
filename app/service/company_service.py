import httpx

from fastapi import HTTPException, status
from app.core.url_utils import normalize_url


async def check_company_url(url: str):
    # Add protocol if user enters google.com
    url = normalize_url(url)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                follow_redirects=True
            )

            #  INDENTED INSIDE: Runs safely while the client context is alive
            if response.status_code < 400 or response.status_code == 403:
                return {
                    "valid": True,
                    "message": "Website reachable"
                }

            return {
                "valid": False,
                "message": f"Website returned status code {response.status_code}"
            }

    except httpx.ConnectError:
        return {
            "valid": False,
            "message": "Unable to connect to website"
        }

    except httpx.TimeoutException:
        return {
            "valid": False,
            "message": "Website request timed out"
        }

    except httpx.InvalidURL:
        return {
            "valid": False,
            "message": "Invalid website URL"
        }

    except Exception as e:
        print(f"URL Validation Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate website URL"
        )