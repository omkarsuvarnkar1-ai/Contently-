
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.content import (
    BulkActionRequest,
    ContentItemCreate,
    ContentItemResponse,
    ContentItemUpdate,
    ContentListResponse,
)
from backend.app.services.content_service import ContentService

router = APIRouter(prefix="/api/content", tags=["Content"])


@router.get("", response_model=ContentListResponse)
def list_content_library(
    search: str | None = Query(None, description="Keyword search in title and body"),
    status: str | None = Query(None, description="Filter by status: Draft, Saved, Scheduled, Published, Needs Review"),
    category: str | None = Query(None, description="Filter by platform/category: LinkedIn, Blogs, Newsletters, Video Scripts, Twitter / X"),
    is_favorite: bool | None = Query(None, description="Filter favorites"),
    sort_by: str | None = Query("updated_at", description="Sort by: updated_at, performance, title"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List content items with user isolation, filtering, and pagination."""
    return ContentService.list_content(
        db=db,
        user=current_user,
        search=search,
        status_filter=status,
        category=category,
        is_favorite=is_favorite,
        sort_by=sort_by,
        page=page,
        limit=limit,
    )


@router.post("", response_model=ContentItemResponse, status_code=status.HTTP_201_CREATED)
def create_content_draft(
    data: ContentItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new draft in user's content library."""
    return ContentService.create_content(db=db, user=current_user, data=data)


@router.get("/{content_id}", response_model=ContentItemResponse)
def get_content_detail(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single content item detail."""
    return ContentService.get_content_by_id(db=db, user=current_user, content_id=content_id)


@router.put("/{content_id}", response_model=ContentItemResponse)
@router.patch("/{content_id}", response_model=ContentItemResponse)
def update_content_item(
    content_id: int,
    data: ContentItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update content item fields, body, status, or schedule."""
    return ContentService.update_content(
        db=db, user=current_user, content_id=content_id, data=data
    )


@router.delete("/{content_id}")
def delete_content_item(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a content item."""
    return ContentService.delete_content(db=db, user=current_user, content_id=content_id)


@router.post("/{content_id}/favorite", response_model=ContentItemResponse)
def toggle_content_favorite(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle starred/favorite state."""
    return ContentService.toggle_favorite(db=db, user=current_user, content_id=content_id)


@router.post("/bulk-action")
def bulk_content_action(
    req: BulkActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute bulk operation (delete, favorite, schedule) on selected content items."""
    return ContentService.bulk_action(
        db=db, user=current_user, action=req.action, content_ids=req.content_ids
    )
