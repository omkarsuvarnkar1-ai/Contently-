import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://localhost:8000"

    @property
    def cors_origins_list(self) -> list[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return []

    # PostgreSQL Connection Settings
    # Can be specified directly as DATABASE_URL or through individual POSTGRES_* variables
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/contently_db"
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "contently_db"

    @model_validator(mode="after")
    def assemble_db_url(self):
        # If granular postgres variables are set, construct standard connection string
        if self.POSTGRES_USER and self.POSTGRES_PASSWORD:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        # Normalize postgres:// to postgresql:// for SQLAlchemy compatibility
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return self

    # Security & Tokens
    JWT_SECRET_KEY: str = "contently_super_secret_jwt_key_replace_in_production_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Seeded Demo User
    DEMO_USER_EMAIL: str = "demo@contently.local"
    DEMO_USER_PASSWORD: str = "ContentlyDemo123!"
    DEMO_USER_NAME: str = "Omkar Sharma"
    DEMO_USER_ROLE: str = "Pro Creator"
    DEMO_USER_AVATAR: str = (
        "https://lh3.googleusercontent.com/aida-public/AB6AXuDJ9-i1Rr_McZcEqHc300dlnvuSl4X_Jr1rT14gwFcUXtv77NmEtv6OO15aZDoL77BbQt8I0v6Gwm8gjSzG2mxICW1gndG6NwIaZk4ydrYnQqO4TYzUfv3OpPvhd6q5CSiTp_f1L9KFMsZCMXcQ8XiwS815pzIOaNc-69wDKmVt4Yz8Gg5uZ2cFsnBljp66brow6kVCYb64xr8tZZsprLOgT4x0Z6q5CPuKpgVUvuc"
    )

    # AI Provider Settings
    DEFAULT_AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # OAuth 2.0 Providers (Google & GitHub)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/auth/google/callback"

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:3000/api/auth/github/callback"

    # Social & External integrations (Optional)
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = "http://localhost:8000/api/integrations/linkedin/callback"

    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    # Razorpay Subscription & Payment Settings
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    RAZORPAY_CURRENCY: str = "INR"
    RAZORPAY_PLAN_PRO_MONTHLY: str = ""
    RAZORPAY_PLAN_PRO_YEARLY: str = ""
    PUBLIC_APP_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
