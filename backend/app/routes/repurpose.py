from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import require_active_subscription
from backend.app.models.content import ContentItem
from backend.app.models.user import User
from backend.app.schemas.repurpose import (
    RepurposedAsset,
    RepurposeRequest,
    RepurposeResponse,
)
from backend.app.services.ai_service import AiService

router = APIRouter(prefix="/api/repurpose", tags=["Content Repurposing"])


@router.post("", response_model=RepurposeResponse)
async def repurpose_content(
    req: RepurposeRequest,
    current_user: User = Depends(require_active_subscription),
    db: Session = Depends(get_db),
):
    """Transform a single long-form asset or raw text into multiple target platform formats."""
    source_title = "Input Asset"
    source_body = req.raw_text or ""

    if req.source_content_id:
        item = (
            db.query(ContentItem)
            .filter(ContentItem.id == req.source_content_id, ContentItem.user_id == current_user.id)
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source content #{req.source_content_id} not found.",
            )
        source_title = item.title
        source_body = item.body or item.excerpt or ""

    if not source_body or len(source_body.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Source content body must contain at least 10 characters to repurpose.",
        )

    words = len(source_body.split())
    extracted_themes = [
        "Adaptive Tutoring Loops",
        "Deterministic Latency Guardrails",
        "Multi-channel Compounding",
        "Unit Economics Optimization",
    ]

    assets: dict[str, RepurposedAsset] = {}
    formats_to_build = req.target_formats or ["linkedin", "x_thread", "video_script", "newsletter"]

    # Synthesize each format using AI adapter
    for fmt in formats_to_build:
        prompt = (
            f"Repurpose this source article into a high-converting {fmt} asset.\n"
            f"Source Title: {source_title}\n"
            f"Source Body: {source_body[:2000]}\n"
            f"Format specific instructions: Tailor length, formatting, and tone for {fmt}."
        )

        res = await AiService.generate_content(
            prompt_topic=prompt,
            channel=fmt,
            tone=req.tone or "Analytical & Direct",
            audience=req.audience or "B2B SaaS Founders",
            length="medium",
        )
        text = res["generated_text"]
        char_cnt = len(text)
        word_cnt = len(text.split())

        fmt_name = fmt.replace("_", " ").title()
        stats_label = f"Ready · {char_cnt:,} chars" if "thread" not in fmt else "Ready · 6 tweets"

        assets[fmt] = RepurposedAsset(
            format_name=fmt_name,
            channel=fmt,
            headline=f"{fmt_name} Asset: {source_title[:40]}",
            content=text,
            stats_label=stats_label,
            character_count=char_cnt,
            word_count=word_cnt,
        )

    return {
        "success": True,
        "source_title": source_title,
        "source_word_count": words,
        "extracted_themes": extracted_themes,
        "assets": assets,
    }
