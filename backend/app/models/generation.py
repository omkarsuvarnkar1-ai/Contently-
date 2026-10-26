from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


def utcnow():
    return datetime.now(UTC)


class GenerationHistory(Base):
    __tablename__ = "generation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    prompt_topic = Column(Text, nullable=False)
    channel = Column(String(100), default="linkedin")
    tone = Column(String(100), default="Analytical & Direct")
    audience = Column(String(100), default="B2B SaaS Founders")
    length = Column(String(50), default="medium")
    adherence_pct = Column(Integer, default=98)
    model_used = Column(String(100), default="Contently LLM-4x")

    generated_text = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    word_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="generations")
