from pydantic import BaseModel, Field


class KeywordDensityResult(BaseModel):
    keyword: str
    occurrences: int
    density_pct: float
    context: str = "Body context"
    status: str = "Ideal Range (1.5% - 2.5%)"


class SerpPreview(BaseModel):
    title: str
    description: str
    url: str
    title_char_count: int
    desc_char_count: int
    title_status: str = "Pixel length: 512px (Optimal)"
    desc_status: str = "No truncation expected"


class SeoAnalyzeRequest(BaseModel):
    content: str = Field(..., min_length=10)
    target_keyword: str | None = "AI in education"
    tracked_keywords: list[str] | None = None
    meta_title: str | None = None
    meta_description: str | None = None


class SeoAnalyzeResponse(BaseModel):
    seo_score: int
    word_count: int
    primary_target: KeywordDensityResult
    tracked_keywords: list[KeywordDensityResult]
    serp_preview: SerpPreview
    suggestions: list[str]


class SeoRewriteRequest(BaseModel):
    content: str | None = None
    current_title: str | None = None
    current_description: str | None = None
    target_keyword: str


class SeoRewriteResponse(BaseModel):
    success: bool = True
    suggested_title: str
    suggested_description: str
    target_keyword: str
