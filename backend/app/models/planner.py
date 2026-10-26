from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


def utcnow():
    return datetime.now(UTC)


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    content_id = Column(Integer, ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    platform = Column(String(100), nullable=False)  # LinkedIn, X / Twitter, Blog, Newsletter
    scheduled_time = Column(DateTime, nullable=False)
    time_slot_label = Column(String(50), default="09:30 AM")
    status = Column(String(50), default="Scheduled")
    day_of_month = Column(Integer, default=20)

    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="scheduled_posts")
    content = relationship("ContentItem", back_populates="scheduled_posts")
