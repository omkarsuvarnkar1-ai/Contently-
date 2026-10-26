from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PersonaItem(BaseModel):
    name: str
    role_weight: str
    description: str
    tags: list[str]


class BrandKitResponse(BaseModel):
    id: int
    user_id: int
    brand_name: str
    alias_id: str
    industry_verticals: str
    positioning_statement: str
    formality_pct: int
    density_pct: int
    edge_pct: int
    tech_depth_pct: int
    preferred_keywords: list[str]
    forbidden_keywords: list[str]
    personas: list[PersonaItem] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrandKitUpdate(BaseModel):
    brand_name: str | None = None
    alias_id: str | None = None
    industry_verticals: str | None = None
    positioning_statement: str | None = None
    formality_pct: int | None = Field(None, ge=0, le=100)
    density_pct: int | None = Field(None, ge=0, le=100)
    edge_pct: int | None = Field(None, ge=0, le=100)
    tech_depth_pct: int | None = Field(None, ge=0, le=100)
    preferred_keywords: list[str] | None = None
    forbidden_keywords: list[str] | None = None


class AddKeywordRequest(BaseModel):
    keyword: str = Field(..., min_length=1)
