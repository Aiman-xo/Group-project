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
                    "User-Agent": "Mozilla/5.0"
                },
                follow_redirects=True
            )

        if response.status_code < 400:
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