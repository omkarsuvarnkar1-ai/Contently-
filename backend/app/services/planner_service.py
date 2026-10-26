from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.planner import ScheduledPost
from backend.app.models.user import User
from backend.app.schemas.planner import ScheduledPostCreate, ScheduledPostUpdate


class PlannerService:

    @classmethod
    def list_posts(
        cls,
        db: Session,
        user: User,
        platform: str | None = None,
        month: int | None = None,
        year: int | None = None,
    ) -> list:
        """List scheduled posts with tenant isolation."""
        query = db.query(ScheduledPost).filter(ScheduledPost.user_id == user.id)

        if platform and platform.lower() not in ["all", "all platforms"]:
            query = query.filter(ScheduledPost.platform.ilike(f"%{platform.strip()}%"))

        return query.order_by(ScheduledPost.scheduled_time.asc()).all()

    @classmethod
    def create_post(cls, db: Session, user: User, data: ScheduledPostCreate) -> ScheduledPost:
        """Create a scheduled calendar post."""
        day = data.day_of_month or data.scheduled_time.day

        post = ScheduledPost(
            user_id=user.id,
            content_id=data.content_id,
            title=data.title,
            platform=data.platform,
            scheduled_time=data.scheduled_time,
            time_slot_label=data.time_slot_label or data.scheduled_time.strftime("%I:%M %p"),
            status=data.status or "Scheduled",
            day_of_month=day,
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        return post

    @classmethod
    def update_post(
        cls, db: Session, user: User, post_id: int, data: ScheduledPostUpdate
    ) -> ScheduledPost:
        """Update or reschedule post."""
        post = (
            db.query(ScheduledPost)
            .filter(ScheduledPost.id == post_id, ScheduledPost.user_id == user.id)
            .first()
        )
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheduled post #{post_id} not found.",
            )

        update_dict = data.model_dump(exclude_unset=True)
        if "scheduled_time" in update_dict and update_dict["scheduled_time"] is not None:
            st = update_dict["scheduled_time"]
            update_dict["day_of_month"] = st.day
            if not update_dict.get("time_slot_label"):
                update_dict["time_slot_label"] = st.strftime("%I:%M %p")

        for k, v in update_dict.items():
            setattr(post, k, v)

        db.commit()
        db.refresh(post)
        return post

    @classmethod
    def delete_post(cls, db: Session, user: User, post_id: int) -> dict:
        """Cancel scheduled post."""
        post = (
            db.query(ScheduledPost)
            .filter(ScheduledPost.id == post_id, ScheduledPost.user_id == user.id)
            .first()
        )
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheduled post #{post_id} not found.",
            )
        db.delete(post)
        db.commit()
        return {"success": True, "message": f"Post #{post_id} removed from schedule."}
