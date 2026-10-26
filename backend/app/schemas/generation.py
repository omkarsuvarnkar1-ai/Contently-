from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    promptTopic: str = Field(..., min_length=3, description="Topic and core thesis for generation")
    channel: str | None = "linkedin"
    tone: str | None = "Analytical & Direct"
    audience: str | None = "B2B SaaS Founders"
    length: str | None = "medium"
    adherence_pct: int | None = 98
    provider: str | None = None


class GenerateResponse(BaseModel):
    success: bool = True
    generated_text: str
    prompt_topic: str
    channel: str
    tone: str
    audience: str
    model_used: str
    tokens_used: int
    word_count: int
    read_time_mins: float
    brand_match_pct: float
    created_at: datetime


class RefineRequest(BaseModel):
    text: str = Field(..., min_length=5)
    refine_type: str = Field(..., description="punchy | shorten | framework")


class RefineResponse(BaseModel):
    success: bool = True
    refined_text: str
    refine_type: str


class GenerationHistoryItem(BaseModel):
    id: int
    prompt_topic: str
    channel: str
    tone: str
    audience: str
    model_used: str
    generated_text: str
    tokens_used: int
    word_count: int
    adherence_pct: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerationHistoryListResponse(BaseModel):
    items: list[GenerationHistoryItem]
    total: int


class AiProviderInfo(BaseModel):
    name: str
    configured: bool
    model: str
    key_hint: str | None = None


class AiStatusResponse(BaseModel):
    default_provider: str
    providers: dict[str, AiProviderInfo]


class AiConfigUpdateRequest(BaseModel):
    default_provider: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    anthropic_api_key: str | None = None

