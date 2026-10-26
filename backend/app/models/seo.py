from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


def utcnow():
    return datetime.now(UTC)


class SeoAnalysis(Base):
    __tablename__ = "seo_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    content_id = Column(Integer, ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True)

    target_keyword = Column(String(255), nullable=False)
    density_pct = Column(Float, default=2.1)
    occurrences = Column(Integer, default=8)
    total_words = Column(Integer, default=1480)

    serp_meta_title = Column(String(255), default="AI in Education: Transforming Modern Classrooms with LLMs")
    serp_meta_description = Column(
        Text,
        default="Discover how universities and modern educators leverage AI tutoring agents to reduce grading time by 85% while boosting student inquiry.",
    )
    serp_url = Column(
        String(255),
        default="https://contently.ai > blog > ai-in-education-modern-classrooms",
    )
    seo_score = Column(Integer, default=92)
    suggestions = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="seo_analyses")
