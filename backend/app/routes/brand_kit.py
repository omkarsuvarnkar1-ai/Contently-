from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.brand_kit import (
    AddKeywordRequest,
    BrandKitResponse,
    BrandKitUpdate,
)
from backend.app.services.brand_service import BrandService

router = APIRouter(prefix="/api/brand-kit", tags=["Brand Kit"])


@router.get("", response_model=BrandKitResponse)
def get_brand_kit(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retrieve brand voice kit, linguistic calibrators, and lexicon."""
    return BrandService.get_or_create(db, current_user)


@router.put("", response_model=BrandKitResponse)
def update_brand_kit(
    data: BrandKitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update brand voice parameters, sliders, or positioning anchor."""
    return BrandService.update(db, current_user, data)


@router.post("/keywords/preferred", response_model=BrandKitResponse)
def add_preferred_keyword(
    req: AddKeywordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new preferred lexicon term."""
    return BrandService.add_keyword(db, current_user, req.keyword, kind="preferred")


@router.delete("/keywords/preferred/{keyword}", response_model=BrandKitResponse)
def remove_preferred_keyword(
    keyword: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a preferred lexicon term."""
    return BrandService.remove_keyword(db, current_user, keyword, kind="preferred")


@router.post("/keywords/forbidden", response_model=BrandKitResponse)
def add_forbidden_keyword(
    req: AddKeywordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Block a buzzword or cliché phrase."""
    return BrandService.add_keyword(db, current_user, req.keyword, kind="forbidden")


@router.delete("/keywords/forbidden/{keyword}", response_model=BrandKitResponse)
def remove_forbidden_keyword(
    keyword: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unblock a cliché phrase."""
    return BrandService.remove_keyword(db, current_user, keyword, kind="forbidden")
