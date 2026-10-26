from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from backend.app.core.database import Base


def utcnow():
    return datetime.now(UTC)


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="social", index=True)  # social, longform, newsletters, video
    format = Column(String(100), default="LinkedIn • High CTR")
    version = Column(String(50), default="v2.4")
    description = Column(Text, nullable=False)
    formula_preview_label = Column(String(100), default="Formula Preview")
    formula_preview = Column(Text, nullable=False)
    engagement_metric = Column(String(100), default="4.2x Avg Engagement")
    usage_count = Column(Integer, default=1840)
    sample_body = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow)
