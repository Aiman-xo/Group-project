from pydantic import BaseModel, ConfigDict, HttpUrl
from typing import Optional


class GoogleAdItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ad_id: str
    advertiser_id: str | None = None
    advertiser_name: str | None = None
    format: str | None = None  # text, image, video
    platform: str | None = None  # SEARCH, YOUTUBE, DISPLAY
    first_shown: str | None = None
    last_shown: str | None = None

    ad_url: HttpUrl | None = None
    media_url: Optional[str] = None
    youtube_id: Optional[str] = None
    headline_or_body: Optional[str] = None
    headline_or_body: str | None = None

    # UI / Render Hints (Flattened for easy React consumption)
    render_type: Optional[str] = "text_card"  # 'youtube_embed' | 'iframe' | 'image' | 'text_card'
    should_use_iframe: bool = False
    embed_url: Optional[str] = None