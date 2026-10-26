import math
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from backend.app.models.content import ContentItem
from backend.app.models.user import User
from backend.app.schemas.content import ContentItemCreate, ContentItemUpdate


class ContentService:

    @classmethod
    def list_content(
        cls,
        db: Session,
        user: User,
        search: str | None = None,
        status_filter: str | None = None,
        category: str | None = None,
        is_favorite: bool | None = None,
        sort_by: str | None = "updated_at",
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """List content items with strict user data isolation, filtering, and pagination."""
        query = db.query(ContentItem).filter(ContentItem.user_id == user.id)

        # Keyword search
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    ContentItem.title.ilike(term),
                    ContentItem.body.ilike(term),
                    ContentItem.excerpt.ilike(term),
                )
            )

        # Status filter
        if status_filter and status_filter.lower() not in ["all", "all statuses"]:
            query = query.filter(ContentItem.status.ilike(status_filter.strip()))

        # Category/Platform filter
        if category and category.lower() not in ["all", "all platforms"]:
            if "linkedin" in category.lower():
                query = query.filter(ContentItem.platform.ilike("%linkedin%"))
            elif "blog" in category.lower():
                query = query.filter(
                    or_(
                        ContentItem.platform.ilike("%blog%"),
                        ContentItem.format.ilike("%guide%"),
                        ContentItem.format.ilike("%blog%"),
                    )
                )
            elif "newsletter" in category.lower():
                query = query.filter(
                    or_(
                        ContentItem.platform.ilike("%newsletter%"),
                        ContentItem.format.ilike("%newsletter%"),
                    )
                )
            elif "video" in category.lower():
                query = query.filter(
                    or_(
                        ContentItem.platform.ilike("%youtube%"),
                        ContentItem.format.ilike("%script%"),
                    )
                )
            elif "twitter" in category.lower() or "x" in category.lower():
                query = query.filter(
                    or_(
                        ContentItem.platform.ilike("%twitter%"),
                        ContentItem.platform.ilike("%x%"),
                    )
                )
            elif "draft" in category.lower():
                query = query.filter(ContentItem.status.ilike("Draft"))

        # Favorite filter
        if is_favorite is not None:
            query = query.filter(ContentItem.is_favorite == is_favorite)

        # Sorting
        if sort_by == "alphabetical" or sort_by == "title":
            query = query.order_by(ContentItem.title.asc())
        elif sort_by == "performance":
            query = query.order_by(desc(ContentItem.voice_match_pct))
        else:
            query = query.order_by(desc(ContentItem.updated_at))

        total = query.count()
        pages = max(1, math.ceil(total / limit)) if limit > 0 else 1
        offset = (max(1, page) - 1) * limit
        items = query.offset(offset).limit(limit).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    @classmethod
    def get_content_by_id(cls, db: Session, user: User, content_id: int) -> ContentItem:
        """Fetch single content item with isolation check."""
        item = (
            db.query(ContentItem)
            .filter(ContentItem.id == content_id, ContentItem.user_id == user.id)
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content item #{content_id} not found or access denied.",
            )
        return item

    @classmethod
    def create_content(cls, db: Session, user: User, data: ContentItemCreate) -> ContentItem:
        """Create a new content draft in the user's library."""
        words = len(data.body.split()) if data.body else 0
        excerpt = data.excerpt or (data.body[:180] + "..." if len(data.body) > 180 else data.body)

        item = ContentItem(
            user_id=user.id,
            title=data.title,
            body=data.body,
            excerpt=excerpt,
            format=data.format or "Social Post",
            platform=data.platform or "LinkedIn",
            status=data.status or "Draft",
            word_count=words,
            citations_count=3 if "citation" in data.body.lower() else 0,
            voice_match_pct=98.0,
            is_favorite=False,
            hero_graphic_url=data.hero_graphic_url,
            scheduled_at=data.scheduled_at,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def update_content(
        cls, db: Session, user: User, content_id: int, data: ContentItemUpdate
    ) -> ContentItem:
        """Update existing content draft."""
        item = cls.get_content_by_id(db, user, content_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "body" in update_dict and update_dict["body"] is not None:
            update_dict["word_count"] = len(update_dict["body"].split())
            if not update_dict.get("excerpt"):
                update_dict["excerpt"] = (
                    update_dict["body"][:180] + "..."
                    if len(update_dict["body"]) > 180
                    else update_dict["body"]
                )

        for key, value in update_dict.items():
            setattr(item, key, value)

        item.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def delete_content(cls, db: Session, user: User, content_id: int) -> dict:
        """Delete content item from library."""
        item = cls.get_content_by_id(db, user, content_id)
        db.delete(item)
        db.commit()
        return {"success": True, "message": f"Content #{content_id} deleted successfully."}

    @classmethod
    def toggle_favorite(cls, db: Session, user: User, content_id: int) -> ContentItem:
        """Toggle favorite star state on content item."""
        item = cls.get_content_by_id(db, user, content_id)
        item.is_favorite = not item.is_favorite
        item.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def bulk_action(cls, db: Session, user: User, action: str, content_ids: list[int]) -> dict:
        """Perform bulk operation on selected items."""
        items = (
            db.query(ContentItem)
            .filter(ContentItem.user_id == user.id, ContentItem.id.in_(content_ids))
            .all()
        )
        if action == "delete":
            for it in items:
                db.delete(it)
            db.commit()
            return {"success": True, "affected": len(items), "action": "deleted"}
        elif action == "favorite":
            for it in items:
                it.is_favorite = True
            db.commit()
            return {"success": True, "affected": len(items), "action": "favorited"}
        elif action == "schedule":
            for it in items:
                it.status = "Scheduled"
            db.commit()
            return {"success": True, "affected": len(items), "action": "scheduled"}
        return {"success": True, "affected": len(items), "action": action}
