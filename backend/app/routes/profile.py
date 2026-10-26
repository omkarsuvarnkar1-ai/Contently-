from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.user import (
    ProfileUpdate,
    SettingsResponse,
    SettingsUpdate,
    UserResponse,
)

router = APIRouter(prefix="/api/profile", tags=["Profile & Settings"])


@router.get("", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Retrieve creator profile details."""
    return current_user


@router.put("", response_model=UserResponse)
def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile information, handle, bio, or avatar."""
    if data.full_name or data.name:
        current_user.full_name = data.full_name or data.name
    if data.bio is not None:
        current_user.bio = data.bio
    if data.handle is not None:
        current_user.handle = data.handle
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url

    current_user.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/settings", response_model=SettingsResponse)
def get_user_settings(current_user: User = Depends(get_current_user)):
    """Retrieve creator engine settings and toggles."""
    return {
        "default_engine": current_user.default_engine,
        "creativity_temperature": current_user.creativity_temperature,
        "auto_save_drafts": current_user.auto_save_drafts,
        "brand_voice_sync": current_user.brand_voice_sync,
    }


@router.put("/settings", response_model=SettingsResponse)
def update_user_settings(
    data: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update default LLM engine core, temperature, or automation toggles."""
    if data.default_engine is not None:
        current_user.default_engine = data.default_engine
    if data.creativity_temperature is not None:
        current_user.creativity_temperature = data.creativity_temperature
    if data.auto_save_drafts is not None:
        current_user.auto_save_drafts = data.auto_save_drafts
    if data.brand_voice_sync is not None:
        current_user.brand_voice_sync = data.brand_voice_sync

    current_user.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(current_user)

    return {
        "default_engine": current_user.default_engine,
        "creativity_temperature": current_user.creativity_temperature,
        "auto_save_drafts": current_user.auto_save_drafts,
        "brand_voice_sync": current_user.brand_voice_sync,
    }
