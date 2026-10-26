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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)
    oauth_provider = Column(String(50), nullable=True, index=True)
    oauth_id = Column(String(255), nullable=True, index=True)
    role = Column(String(100), default="Pro Creator")
    avatar_url = Column(Text, nullable=True)
    handle = Column(String(100), default="omkar_builds")
    bio = Column(
        Text,
        default="Founding creator & AI technologist crafting multi-channel distribution systems.",
    )

    # Preferences & Settings
    default_engine = Column(String(100), default="Contently LLM-4x Balanced (Fine-tuned)")
    creativity_temperature = Column(Float, default=0.70)
    auto_save_drafts = Column(Boolean, default=True)
    brand_voice_sync = Column(Boolean, default=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="owner", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    contents = relationship("ContentItem", back_populates="user", cascade="all, delete-orphan")
    generations = relationship("GenerationHistory", back_populates="user", cascade="all, delete-orphan")
    brand_kit = relationship("BrandKit", back_populates="user", uselist=False, cascade="all, delete-orphan")
    scheduled_posts = relationship("ScheduledPost", back_populates="user", cascade="all, delete-orphan")
    seo_analyses = relationship("SeoAnalysis", back_populates="user", cascade="all, delete-orphan")


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), default="Contently Workspace")
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at = Column(DateTime, default=utcnow)

    owner = relationship("User", back_populates="workspace")
