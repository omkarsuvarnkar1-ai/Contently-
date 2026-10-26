import logging
import os
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.brand_kit import BrandKit
from backend.app.models.generation import GenerationHistory
from backend.app.models.user import User
from backend.app.schemas.generation import (
    AiConfigUpdateRequest,
    AiProviderInfo,
    AiStatusResponse,
    GenerateRequest,
    GenerateResponse,
    GenerationHistoryListResponse,
    RefineRequest,
    RefineResponse,
)
from backend.app.services.ai_service import AiService

router = APIRouter(prefix="/api/ai", tags=["AI Studio"])
logger = logging.getLogger("contently.ai_routes")


def _mask_key(key: str | None) -> str | None:
    if not key or len(key) < 6:
        return None
    return f"{key[:3]}...{key[-3:]}"


def _update_env_var(key: str, val: str):
    env_paths = [
        os.path.join(os.getcwd(), "backend", ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for p in env_paths:
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8") as f:
                    lines = f.readlines()
                found = False
                new_lines = []
                for line in lines:
                    if line.startswith(f"{key}="):
                        new_lines.append(f"{key}={val}\n")
                        found = True
                    else:
                        new_lines.append(line)
                if not found:
                    new_lines.append(f"{key}={val}\n")
                with open(p, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            except OSError as e:
                logger.warning("Could not persist key to %s: %s", p, str(e))


@router.get("/status", response_model=AiStatusResponse)
def get_ai_status():
    """Retrieve current AI provider readiness and configuration status."""
    return {
        "default_provider": settings.DEFAULT_AI_PROVIDER,
        "providers": {
            "openai": AiProviderInfo(
                name="OpenAI",
                configured=bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip()),
                model=settings.OPENAI_MODEL,
                key_hint=_mask_key(settings.OPENAI_API_KEY),
            ),
            "gemini": AiProviderInfo(
                name="Google Gemini",
                configured=bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip()),
                model=settings.GEMINI_MODEL,
                key_hint=_mask_key(settings.GEMINI_API_KEY),
            ),
            "anthropic": AiProviderInfo(
                name="Anthropic Claude",
                configured=bool(settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.strip()),
                model=settings.ANTHROPIC_MODEL,
                key_hint=_mask_key(settings.ANTHROPIC_API_KEY),
            ),
        },
    }


@router.post("/config", response_model=AiStatusResponse)
def update_ai_config(
    req: AiConfigUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """Dynamically configure real AI provider keys in memory and persistent .env."""
    if req.default_provider:
        prov = req.default_provider.strip().lower()
        if prov in ["openai", "gemini", "anthropic"]:
            settings.DEFAULT_AI_PROVIDER = prov
            _update_env_var("DEFAULT_AI_PROVIDER", prov)

    if req.openai_api_key is not None:
        key = req.openai_api_key.strip()
        settings.OPENAI_API_KEY = key
        _update_env_var("OPENAI_API_KEY", key)

    if req.gemini_api_key is not None:
        key = req.gemini_api_key.strip()
        settings.GEMINI_API_KEY = key
        _update_env_var("GEMINI_API_KEY", key)

    if req.anthropic_api_key is not None:
        key = req.anthropic_api_key.strip()
        settings.ANTHROPIC_API_KEY = key
        _update_env_var("ANTHROPIC_API_KEY", key)

    return get_ai_status()



@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_200_OK)
async def generate_ai_content(
    req: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Synthesize content asset using real AI provider adapter with brand voice calibration."""
    # Retrieve brand kit for prompt injection
    brand_kit = db.query(BrandKit).filter(BrandKit.user_id == current_user.id).first()
    positioning = brand_kit.positioning_statement if brand_kit else None
    preferred = [k.strip() for k in brand_kit.preferred_keywords.split(",") if k.strip()] if brand_kit else None
    forbidden = [k.strip() for k in brand_kit.forbidden_keywords.split(",") if k.strip()] if brand_kit else None

    # Call AI Provider Adapter
    res = await AiService.generate_content(
        prompt_topic=req.promptTopic,
        channel=req.channel or "linkedin",
        tone=req.tone or "Analytical & Direct",
        audience=req.audience or "B2B SaaS Founders",
        length=req.length or "medium",
        adherence_pct=req.adherence_pct or 98,
        provider=req.provider,
        brand_positioning=positioning,
        preferred_keywords=preferred,
        forbidden_keywords=forbidden,
    )

    # Save to GenerationHistory
    history = GenerationHistory(
        user_id=current_user.id,
        prompt_topic=req.promptTopic,
        channel=req.channel or "linkedin",
        tone=req.tone or "Analytical & Direct",
        audience=req.audience or "B2B SaaS Founders",
        length=req.length or "medium",
        adherence_pct=req.adherence_pct or 98,
        model_used=res["model_used"],
        generated_text=res["generated_text"],
        tokens_used=res["tokens_used"],
        word_count=res["word_count"],
    )
    db.add(history)
    db.commit()

    return {
        "success": True,
        "generated_text": res["generated_text"],
        "prompt_topic": req.promptTopic,
        "channel": req.channel or "linkedin",
        "tone": req.tone or "Analytical & Direct",
        "audience": req.audience or "B2B SaaS Founders",
        "model_used": res["model_used"],
        "tokens_used": res["tokens_used"],
        "word_count": res["word_count"],
        "read_time_mins": res["read_time_mins"],
        "brand_match_pct": res["brand_match_pct"],
        "created_at": datetime.now(UTC),
    }


@router.post("/refine", response_model=RefineResponse)
async def refine_content(
    req: RefineRequest,
    current_user: User = Depends(get_current_user),
):
    """Refine existing text into punchy, shorten, or framework structures."""
    refined = await AiService.refine_content(text=req.text, refine_type=req.refine_type)
    return {
        "success": True,
        "refined_text": refined,
        "refine_type": req.refine_type,
    }


@router.get("/history", response_model=GenerationHistoryListResponse)
def get_generation_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch user's previous generation events."""
    items = (
        db.query(GenerationHistory)
        .filter(GenerationHistory.user_id == current_user.id)
        .order_by(desc(GenerationHistory.created_at))
        .limit(limit)
        .all()
    )
    total = (
        db.query(GenerationHistory)
        .filter(GenerationHistory.user_id == current_user.id)
        .count()
    )
    return {"items": items, "total": total}
