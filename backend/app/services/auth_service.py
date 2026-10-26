from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.app.models.brand_kit import BrandKit
from backend.app.models.user import User, Workspace
from backend.app.schemas.user import OAuthRequest, UserCreate, UserLogin


class AuthService:

    @classmethod
    def get_or_create_demo_user(cls, db: Session) -> User:
        """Ensure default demo account is initialized in database."""
        user = db.query(User).filter(User.email == settings.DEMO_USER_EMAIL).first()
        if not user:
            hashed = hash_password(settings.DEMO_USER_PASSWORD)
            user = User(
                email=settings.DEMO_USER_EMAIL,
                full_name=settings.DEMO_USER_NAME,
                hashed_password=hashed,
                role=settings.DEMO_USER_ROLE,
                avatar_url=settings.DEMO_USER_AVATAR,
                handle="omkar_builds",
                bio="Founding creator & AI technologist crafting multi-channel distribution systems.",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Workspace
            workspace = Workspace(name="Omkar's Workspace", owner_id=user.id)
            db.add(workspace)

            # Brand Kit
            brand_kit = BrandKit(
                user_id=user.id,
                brand_name="Contently / Omkar",
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
            db.add(brand_kit)
            db.commit()
            db.refresh(user)

        return user

    @classmethod
    def signup(cls, db: Session, user_in: UserCreate) -> dict:
        """Register a new user account with hashed password and isolated workspace."""
        email = (user_in.email or "").strip().lower()
        if not email or "@" not in email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="A valid email address is required.",
            )

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists. Please log in.",
            )

        hashed = hash_password(user_in.password)
        name = user_in.full_name or "Creator"

        user = User(
            email=email,
            full_name=name,
            hashed_password=hashed,
            role="Pro Creator",
            avatar_url=settings.DEMO_USER_AVATAR,
            handle=email.split("@")[0],
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Isolated workspace for the new user
        workspace = Workspace(name=f"{name}'s Workspace", owner_id=user.id)
        db.add(workspace)

        # Brand Kit for new user
        brand_kit = BrandKit(
            user_id=user.id,
            brand_name=f"{name} Brand",
            alias_id="#001",
            industry_verticals="Technology, Content Strategy",
            positioning_statement=f"High-leverage content for {name}'s audience",
        )
        db.add(brand_kit)
        db.commit()

        token = create_access_token(user.id)
        return {"user": user, "token": token}

    @classmethod
    def login(cls, db: Session, credentials: UserLogin) -> dict:
        """Authenticate user credentials and return access token."""
        email = (credentials.email or "").strip().lower()
        password = credentials.password

        # If logging in with demo credentials, ensure demo user exists
        if email == settings.DEMO_USER_EMAIL.lower():
            user = cls.get_or_create_demo_user(db)
        else:
            user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Account not found.",
            )

        if not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This account was created via {user.oauth_provider or 'OAuth'} authentication. Please sign in with {user.oauth_provider or 'OAuth'}.",
            )

        if not verify_password(password, user.hashed_password):
            # Special hint if demo email was used with wrong password
            if email == settings.DEMO_USER_EMAIL.lower():
                detail = f"Invalid password. Demo password is {settings.DEMO_USER_PASSWORD}"
            else:
                detail = "Invalid email or password."
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail,
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is currently disabled.",
            )

        token = create_access_token(user.id)
        return {"user": user, "token": token}

    @classmethod
    def oauth_login_or_signup(cls, db: Session, oauth_data: OAuthRequest) -> dict:
        """Authenticate or automatically register a user via OAuth (Google, GitHub)."""
        provider = (oauth_data.provider or "").strip().lower()
        if provider not in ("google", "github"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: '{provider}'. Supported providers: google, github",
            )

        email = (oauth_data.email or "").strip().lower()
        if not email or "@" not in email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="A valid email is required from the OAuth provider.",
            )

        provider_id = oauth_data.provider_id
        user = None

        # 1. Search by oauth_provider + oauth_id if provider_id given
        if provider_id:
            user = db.query(User).filter(
                User.oauth_provider == provider,
                User.oauth_id == str(provider_id),
            ).first()

        # 2. Search by email if not found
        if not user:
            user = db.query(User).filter(User.email == email).first()

        is_new = False
        if user:
            # Update oauth link if missing
            if not user.oauth_provider:
                user.oauth_provider = provider
            if provider_id and not user.oauth_id:
                user.oauth_id = str(provider_id)
            if oauth_data.avatar_url and (not user.avatar_url or "lh3.googleusercontent" in user.avatar_url):
                user.avatar_url = oauth_data.avatar_url
            db.commit()
            db.refresh(user)
        else:
            # Register brand new OAuth user
            is_new = True
            name = (oauth_data.name or oauth_data.full_name or email.split("@")[0].replace(".", " ").title()).strip()
            handle_base = email.split("@")[0].lower()

            # Ensure unique handle
            handle = handle_base
            suffix = 1
            while db.query(User).filter(User.handle == handle).first():
                handle = f"{handle_base}_{suffix}"
                suffix += 1

            avatar = oauth_data.avatar_url or settings.DEMO_USER_AVATAR

            import secrets
            dummy_password_hash = hash_password(secrets.token_urlsafe(32))

            user = User(
                email=email,
                full_name=name,
                hashed_password=dummy_password_hash,
                oauth_provider=provider,
                oauth_id=str(provider_id) if provider_id else None,
                role="Pro Creator",
                avatar_url=avatar,
                handle=handle,
                bio=f"Content creator using {provider.capitalize()} on Contently.",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Isolated workspace
            workspace = Workspace(name=f"{name}'s Workspace", owner_id=user.id)
            db.add(workspace)

            # Brand Kit
            brand_kit = BrandKit(
                user_id=user.id,
                brand_name=f"{name} Brand",
                alias_id="#001",
                industry_verticals="Technology, Content Strategy",
                positioning_statement=f"High-leverage content for {name}'s audience",
            )
            db.add(brand_kit)
            db.commit()
            db.refresh(user)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is currently disabled.",
            )

        token = create_access_token(user.id)
        return {"user": user, "token": token, "is_new": is_new}
