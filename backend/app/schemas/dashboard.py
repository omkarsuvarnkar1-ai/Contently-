
from pydantic import BaseModel

from backend.app.schemas.content import ContentItemResponse


class MetricTile(BaseModel):
    value: int
    change_label: str
    subtext: str
    sparkline: str | None = None


class VoiceCalibrationDial(BaseModel):
    name: str = "Omkar-Default"
    directness_pct: int = 96
    hook_potency_pct: int = 92
    story_resonance_pct: int = 88
    description: str = "Your linguistic model scores highest in authoritativeness and technical clarity."


class AiRecommendation(BaseModel):
    badge: str = "AI Content Recommendation"
    headline: str = "Ready to create?"
    body: str = (
        "Your recent LinkedIn and Twitter content performs 3.4x better with question-based hooks and concise 3-bullet structures."
    )
    metric_basis: str = "Based on 42,910 audience impressions"


class DashboardStatsResponse(BaseModel):
    content_created: MetricTile
    saved_content: MetricTile
    scheduled: MetricTile
    ai_generations: MetricTile
    voice_calibration: VoiceCalibrationDial
    ai_recommendation: AiRecommendation


class DashboardOverviewResponse(BaseModel):
    stats: DashboardStatsResponse
    recent_content: list[ContentItemResponse]
