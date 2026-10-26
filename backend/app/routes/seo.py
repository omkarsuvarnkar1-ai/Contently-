from fastapi import APIRouter, Depends

from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.seo import (
    SeoAnalyzeRequest,
    SeoAnalyzeResponse,
    SeoRewriteRequest,
    SeoRewriteResponse,
)
from backend.app.services.seo_service import SeoService

router = APIRouter(prefix="/api/seo", tags=["SEO Assistant"])


@router.post("/analyze", response_model=SeoAnalyzeResponse)
def analyze_content_seo(
    req: SeoAnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze text for keyword density, occurrences, SERP previews, and optimization score."""
    return SeoService.analyze_text(
        content=req.content,
        target_keyword=req.target_keyword or "AI in education",
        tracked_keywords=req.tracked_keywords,
        meta_title=req.meta_title,
        meta_description=req.meta_description,
    )


@router.post("/rewrite", response_model=SeoRewriteResponse)
async def rewrite_serp_metadata(
    req: SeoRewriteRequest,
    current_user: User = Depends(get_current_user),
):
    """Rewrite title and meta description for maximum CTR using AI adapter."""
    res = await SeoService.rewrite_serp(
        target_keyword=req.target_keyword,
        current_title=req.current_title,
        current_description=req.current_description,
    )
    return res
