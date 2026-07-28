from pydantic import BaseModel, field_validator
from urllib.parse import urlparse


class InstagramUrlUpdate(BaseModel):
    instagram_url: str

    @field_validator("instagram_url")
    @classmethod
    def validate_instagram_url(cls, value: str):
        value = value.strip()

        try:
            parsed = urlparse(value)

            if parsed.scheme not in ("http", "https"):
                raise ValueError("Instagram URL must use http or https")

            hostname = (parsed.hostname or "").lower()

            if hostname not in {
                "instagram.com",
                "www.instagram.com"
            }:
                raise ValueError(
                    "Please enter a valid Instagram profile URL"
                )

            path = parsed.path.strip("/")

            if not path:
                raise ValueError(
                    "Instagram profile username is missing"
                )

            return value

        except ValueError:
            raise
        except Exception:
            raise ValueError(
                "Please enter a valid Instagram profile URL"
            )