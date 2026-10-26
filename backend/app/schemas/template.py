from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TemplateResponse(BaseModel):
    id: int
    title: str
    category: str
    format: str
    version: str
    description: str
    formula_preview_label: str
    formula_preview: str
    engagement_metric: str
    usage_count: int
    sample_body: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TemplateListResponse(BaseModel):
    items: list[TemplateResponse]
    total: int
