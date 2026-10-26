
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.content import ContentItemResponse
from backend.app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardStatsResponse,
)
from backend.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_metrics(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retrieve workspace metric tiles, voice calibration dial, and AI recommendation."""
    stats = DashboardService.get_dashboard_stats(db, current_user)
    return stats


@router.get("/recent", response_model=list[ContentItemResponse])
def get_recent_content(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve recent content table records for the dashboard."""
    recent = DashboardService.get_recent_content(db, current_user, limit=limit)
    return recent


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retrieve combined dashboard metrics and recent content in a single payload."""
    stats = DashboardService.get_dashboard_stats(db, current_user)
    recent = DashboardService.get_recent_content(db, current_user, limit=10)
    return {"stats": stats, "recent_content": recent}
