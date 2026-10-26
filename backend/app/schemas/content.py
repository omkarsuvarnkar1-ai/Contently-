from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContentItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field("", description="Draft body text or markdown")
    format: str | None = "Social Post"
    platform: str | None = "LinkedIn"
    status: str | None = "Draft"
    excerpt: str | None = None
    hero_graphic_url: str | None = None
    scheduled_at: datetime | None = None


class ContentItemUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    format: str | None = None
    platform: str | None = None
    status: str | None = None
    excerpt: str | None = None
    hero_graphic_url: str | None = None
    is_favorite: bool | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None


class ContentItemResponse(BaseModel):
    id: int
    user_id: int
    title: str
    body: str
    excerpt: str | None = None
    format: str
    platform: str
    status: str
    word_count: int
    citations_count: int
    voice_match_pct: float
    is_favorite: bool
    hero_graphic_url: str | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentListResponse(BaseModel):
    items: list[ContentItemResponse]
    total: int
    page: int
    limit: int
    pages: int


class BulkActionRequest(BaseModel):
    action: str  # "delete", "favorite", "schedule", "move_to_collection"
    content_ids: list[int]
    scheduled_at: datetime | None = None
    collection_name: str | None = None
