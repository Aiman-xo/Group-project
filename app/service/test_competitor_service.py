import asyncio

from app.service.website_url_service import (
    discover_competitors,
)


async def main():

    response = await discover_competitors(
        industry="IT",
        country="India",
        state="Kerala",
        district=" Kozhikode",
    )

    print("\n===== FINAL RESPONSE =====")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())