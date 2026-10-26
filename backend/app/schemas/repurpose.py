
from pydantic import BaseModel, Field


class RepurposedAsset(BaseModel):
    format_name: str
    channel: str
    headline: str
    content: str
    stats_label: str  # e.g. "Ready · 1,320 chars" or "Ready · 6 tweets"
    character_count: int
    word_count: int


class RepurposeRequest(BaseModel):
    source_content_id: int | None = None
    raw_text: str | None = None
    source_url: str | None = None
    target_formats: list[str] = Field(
        default=["linkedin", "x_thread", "video_script", "newsletter"],
        description="List of formats to synthesize",
    )
    tone: str | None = "Analytical & Direct"
    audience: str | None = "B2B SaaS Founders"


class RepurposeResponse(BaseModel):
    success: bool = True
    source_title: str
    source_word_count: int
    extracted_themes: list[str]
    assets: dict[str, RepurposedAsset]
