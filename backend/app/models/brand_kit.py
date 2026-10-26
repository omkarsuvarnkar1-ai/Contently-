from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


def utcnow():
    return datetime.now(UTC)


class BrandKit(Base):
    __tablename__ = "brand_kits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    brand_name = Column(String(255), default="Contently / Omkar")
    alias_id = Column(String(50), default="#001")
    industry_verticals = Column(Text, default="B2B SaaS, Artificial Intelligence, Developer Tools")
    positioning_statement = Column(
        Text,
        default="High-leverage AI-native content strategy for modern B2B founders and engineering leads",
    )

    # Tone & Linguistic Calibrators
    formality_pct = Column(Integer, default=70)
    density_pct = Column(Integer, default=85)
    edge_pct = Column(Integer, default=90)
    tech_depth_pct = Column(Integer, default=75)

    # Vocabulary & Governance (comma-separated or JSON string)
    preferred_keywords = Column(
        Text,
        default="leverage,paradigm shift,deterministic,first-principles,signal-to-noise ratio,operational velocity",
    )
    forbidden_keywords = Column(
        Text,
        default="game-changer,unleash,delve,supercharge,revolutionary,in today's fast-paced world",
    )

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="brand_kit")
