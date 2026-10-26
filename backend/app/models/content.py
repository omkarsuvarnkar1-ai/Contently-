from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


def utcnow():
    return datetime.now(UTC)


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False, default="")
    excerpt = Column(Text, nullable=True)

    # Format: Social Post, Thought Piece, Viral Thread, Long-form Guide, Multi-image Caption, Email Newsletter, YouTube Script
    format = Column(String(100), default="Social Post")

    # Platform: LinkedIn, Twitter / X, Blog, Newsletter, YouTube, Instagram
    platform = Column(String(100), default="LinkedIn")

    # Status: Draft, Saved, Scheduled, Published, Needs Review
    status = Column(String(50), default="Draft", index=True)

    word_count = Column(Integer, default=0)
    citations_count = Column(Integer, default=0)
    voice_match_pct = Column(Float, default=98.0)
    is_favorite = Column(Boolean, default=False, index=True)
    hero_graphic_url = Column(Text, nullable=True)

    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = relationship("User", back_populates="contents")
    scheduled_posts = relationship("ScheduledPost", back_populates="content", cascade="all, delete-orphan")
