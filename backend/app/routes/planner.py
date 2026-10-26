
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.planner import (
    ScheduledPostCreate,
    ScheduledPostListResponse,
    ScheduledPostResponse,
    ScheduledPostUpdate,
)
from backend.app.services.planner_service import PlannerService

router = APIRouter(prefix="/api/planner", tags=["Content Planner"])


@router.get("/posts", response_model=ScheduledPostListResponse)
def list_scheduled_posts(
    platform: str | None = Query(None, description="LinkedIn, X / Twitter, Blog, Newsletter"),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2024),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve scheduled posts for calendar view with platform filtering."""
    posts = PlannerService.list_posts(
        db=db, user=current_user, platform=platform, month=month, year=year
    )
    return {"items": posts, "total": len(posts)}


@router.post("/posts", response_model=ScheduledPostResponse, status_code=status.HTTP_201_CREATED)
def schedule_new_post(
    data: ScheduledPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Schedule a post on the planner calendar."""
    return PlannerService.create_post(db=db, user=current_user, data=data)


@router.patch("/posts/{post_id}", response_model=ScheduledPostResponse)
@router.put("/posts/{post_id}", response_model=ScheduledPostResponse)
def update_scheduled_post(
    post_id: int,
    data: ScheduledPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reschedule or update post details."""
    return PlannerService.update_post(db=db, user=current_user, post_id=post_id, data=data)


@router.delete("/posts/{post_id}")
def cancel_scheduled_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel and delete scheduled post from calendar."""
    return PlannerService.delete_post(db=db, user=current_user, post_id=post_id)
