import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


def validate_email_str(value: str | None) -> str | None:
    if value is None:
        return None
    val = value.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", val):
        raise ValueError(f"'{value}' is not a valid email address.")
    return val


class UserBase(BaseModel):
    email: str
    full_name: str
    role: str = "Pro Creator"
    avatar_url: str | None = None
    handle: str | None = "omkar_builds"
    bio: str | None = None


class UserCreate(BaseModel):
    email: str | None = None
    workEmail: str | None = None
    full_name: str | None = None
    fullName: str | None = None
    name: str | None = None
    password: str = Field(..., min_length=6)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: dict):
        if not isinstance(data, dict):
            return data
        # Normalize email / workEmail
        raw_email = data.get("email") or data.get("workEmail")
        if raw_email:
            data["email"] = validate_email_str(raw_email)
        # Normalize name / fullName / full_name
        if not data.get("full_name"):
            data["full_name"] = data.get("fullName") or data.get("name") or "Creator"
        return data


class UserLogin(BaseModel):
    email: str | None = None
    workEmail: str | None = None
    username: str | None = None
    password: str

    @model_validator(mode="before")
    @classmethod
    def normalize_login(cls, data: dict):
        if not isinstance(data, dict):
            return data
        raw_email = data.get("email") or data.get("workEmail") or data.get("username")
        if raw_email:
            data["email"] = validate_email_str(raw_email)
        return data


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    name: str | None = None
    role: str
    avatar_url: str | None = None
    avatar: str | None = None
    handle: str | None = None
    bio: str | None = None
    oauth_provider: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def set_aliases(self):
        self.name = self.full_name
        self.avatar = self.avatar_url
        return self


class OAuthRequest(BaseModel):
    provider: str = Field(..., description="OAuth provider: google or github")
    email: str
    name: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    provider_id: str | None = None
    access_token: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_oauth(cls, data: dict):
        if not isinstance(data, dict):
            return data
        raw_email = data.get("email") or data.get("workEmail")
        if raw_email:
            data["email"] = validate_email_str(raw_email)
        if not data.get("name") and data.get("full_name"):
            data["name"] = data.get("full_name")
        return data


class AuthResponse(BaseModel):
    success: bool = True
    token: str
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    is_new: bool = False


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    name: str | None = None
    bio: str | None = None
    handle: str | None = None
    avatar_url: str | None = None


class SettingsUpdate(BaseModel):
    default_engine: str | None = None
    creativity_temperature: float | None = None
    auto_save_drafts: bool | None = None
    brand_voice_sync: bool | None = None


class SettingsResponse(BaseModel):
    default_engine: str
    creativity_temperature: float
    auto_save_drafts: bool
    brand_voice_sync: bool
