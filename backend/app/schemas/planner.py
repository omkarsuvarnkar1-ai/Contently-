from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScheduledPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(..., description="LinkedIn, X / Twitter, Blog, Newsletter")
    scheduled_time: datetime
    time_slot_label: str | None = "09:30 AM"
    status: str | None = "Scheduled"
    day_of_month: int | None = None
    content_id: int | None = None


class ScheduledPostUpdate(BaseModel):
    title: str | None = None
    platform: str | None = None
    scheduled_time: datetime | None = None
    time_slot_label: str | None = None
    status: str | None = None
    day_of_month: int | None = None


class ScheduledPostResponse(BaseModel):
    id: int
    user_id: int
    content_id: int | None = None
    title: str
    platform: str
    scheduled_time: datetime
    time_slot_label: str
    status: str
    day_of_month: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduledPostListResponse(BaseModel):
    items: list[ScheduledPostResponse]
    total: int
