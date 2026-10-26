from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.app.models.brand_kit import BrandKit
from backend.app.models.user import User
from backend.app.schemas.brand_kit import BrandKitUpdate


class BrandService:

    DEFAULT_PERSONAS = [
        {
            "name": "Technical Founders & CTOs",
            "role_weight": "Primary Target (Weight: 60%)",
            "description": "Zero patience for marketing hand-waving. Cares about resilient architectural trade-offs, reproducible benchmarks, deterministic latency, and engineering unit economics.",
            "tags": ["Direct Tone", "Architecture ROI", "Code First"],
        },
        {
            "name": "Growth & Product Marketers",
            "role_weight": "Secondary Target (Weight: 40%)",
            "description": "Focused on distribution speed, organic resonance loops, conversion multipliers, and multi-channel pipeline velocity.",
            "tags": ["Conversion Hook", "Growth Velocity", "Metrics Driven"],
        },
    ]

    @classmethod
    def get_or_create(cls, db: Session, user: User) -> dict:
        """Fetch or initialize user's brand voice kit."""
        kit = db.query(BrandKit).filter(BrandKit.user_id == user.id).first()
        if not kit:
            kit = BrandKit(
                user_id=user.id,
                brand_name=f"Contently / {user.full_name.split()[0]}",
                alias_id="#001",
                industry_verticals="B2B SaaS, Artificial Intelligence, Developer Tools",
                positioning_statement="High-leverage AI-native content strategy for modern B2B founders and engineering leads",
                formality_pct=70,
                density_pct=85,
                edge_pct=90,
                tech_depth_pct=75,
                preferred_keywords="leverage,paradigm shift,deterministic,first-principles,signal-to-noise ratio,operational velocity",
                forbidden_keywords="game-changer,unleash,delve,supercharge,revolutionary,in today's fast-paced world",
            )
            db.add(kit)
            db.commit()
            db.refresh(kit)

        preferred = [k.strip() for k in kit.preferred_keywords.split(",") if k.strip()]
        forbidden = [k.strip() for k in kit.forbidden_keywords.split(",") if k.strip()]

        return {
            "id": kit.id,
            "user_id": kit.user_id,
            "brand_name": kit.brand_name,
            "alias_id": kit.alias_id,
            "industry_verticals": kit.industry_verticals,
            "positioning_statement": kit.positioning_statement,
            "formality_pct": kit.formality_pct,
            "density_pct": kit.density_pct,
            "edge_pct": kit.edge_pct,
            "tech_depth_pct": kit.tech_depth_pct,
            "preferred_keywords": preferred,
            "forbidden_keywords": forbidden,
            "personas": cls.DEFAULT_PERSONAS,
            "created_at": kit.created_at,
            "updated_at": kit.updated_at,
        }

    @classmethod
    def update(cls, db: Session, user: User, data: BrandKitUpdate) -> dict:
        """Update brand voice calibration parameters."""
        kit = db.query(BrandKit).filter(BrandKit.user_id == user.id).first()
        if not kit:
            cls.get_or_create(db, user)
            kit = db.query(BrandKit).filter(BrandKit.user_id == user.id).first()

        update_dict = data.model_dump(exclude_unset=True)

        if "preferred_keywords" in update_dict and update_dict["preferred_keywords"] is not None:
            kit.preferred_keywords = ",".join(update_dict["preferred_keywords"])
            del update_dict["preferred_keywords"]

        if "forbidden_keywords" in update_dict and update_dict["forbidden_keywords"] is not None:
            kit.forbidden_keywords = ",".join(update_dict["forbidden_keywords"])
            del update_dict["forbidden_keywords"]

        for k, v in update_dict.items():
            setattr(kit, k, v)

        kit.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(kit)

        return cls.get_or_create(db, user)

    @classmethod
    def add_keyword(cls, db: Session, user: User, keyword: str, kind: str = "preferred") -> dict:
        """Add a keyword to either preferred or forbidden registry."""
        kit = db.query(BrandKit).filter(BrandKit.user_id == user.id).first()
        if not kit:
            cls.get_or_create(db, user)
            kit = db.query(BrandKit).filter(BrandKit.user_id == user.id).first()

        field = "preferred_keywords" if kind == "preferred" else "forbidden_keywords"
        current_list = [k.strip() for k in getattr(kit, field).split(",") if k.strip()]

        cleaned = keyword.strip()
        if cleaned and cleaned not in current_list:
            current_list.append(cleaned)
            setattr(kit, field, ",".join(current_list))
            kit.updated_at = datetime.now(UTC)
            db.commit()
            db.refresh(kit)

        return cls.get_or_create(db, user)

    @classmethod
    def remove_keyword(cls, db: Session, user: User, keyword: str, kind: str = "preferred") -> dict:
        """Remove a keyword from registry."""
        kit = db.query(BrandKit).filter(BrandKit.user_id == user.id).first()
        if not kit:
            return cls.get_or_create(db, user)

        field = "preferred_keywords" if kind == "preferred" else "forbidden_keywords"
        current_list = [k.strip() for k in getattr(kit, field).split(",") if k.strip()]

        cleaned = keyword.strip().lower()
        new_list = [k for k in current_list if k.lower() != cleaned]

        setattr(kit, field, ",".join(new_list))
        kit.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(kit)

        return cls.get_or_create(db, user)
