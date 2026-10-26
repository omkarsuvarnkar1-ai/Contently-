import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.user import AuthResponse, OAuthRequest, UserCreate, UserLogin, UserResponse
from backend.app.services.auth_service import AuthService

logger = logging.getLogger("contently.auth")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Register a new creator account."""
    result = AuthService.signup(db, user_in)
    user = result["user"]
    token = result["token"]

    # Also set secure HTTP-only cookie for optional browser session support
    response.set_cookie(
        key="contently_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )

    return {
        "success": True,
        "token": token,
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "is_new": True,
    }


@router.post("/login", response_model=AuthResponse)
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticate and obtain JWT access token."""
    result = AuthService.login(db, credentials)
    user = result["user"]
    token = result["token"]

    response.set_cookie(
        key="contently_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )

    return {
        "success": True,
        "token": token,
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "is_new": False,
    }


@router.post("/oauth", response_model=AuthResponse)
def oauth_auth(oauth_in: OAuthRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate or register a creator account using OAuth (Google or GitHub)."""
    result = AuthService.oauth_login_or_signup(db, oauth_in)
    user = result["user"]
    token = result["token"]
    is_new = result.get("is_new", False)

    response.set_cookie(
        key="contently_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )

    return {
        "success": True,
        "token": token,
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "is_new": is_new,
    }


@router.get("/providers")
def get_auth_providers():
    """Check which OAuth identity providers are configured."""
    return {
        "google": {
            "enabled": bool(settings.GOOGLE_CLIENT_ID),
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        },
        "github": {
            "enabled": bool(settings.GITHUB_CLIENT_ID),
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
        },
    }


@router.get("/google/authorize")
def google_authorize():
    """Initiate Google OAuth2 authentication flow."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth is not configured on this server. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env, or use interactive one-click OAuth.",
        )
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: Session = Depends(get_db)):
    """Process Google OAuth callback with auth code exchange."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth credentials are missing in server settings.",
        )

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(token_url, data=token_data)
        if token_resp.status_code != 200:
            logger.error("Google token exchange error: %s", token_resp.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google OAuth token exchange failed: {token_resp.text}",
            )
        token_json = token_resp.json()
        access_token = token_json.get("access_token")

        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retrieve Google user profile.",
            )
        info = userinfo_resp.json()

    oauth_req = OAuthRequest(
        provider="google",
        email=info.get("email"),
        name=info.get("name") or info.get("given_name"),
        avatar_url=info.get("picture"),
        provider_id=info.get("sub"),
    )
    result = AuthService.oauth_login_or_signup(db, oauth_req)
    token = result["token"]

    redirect = RedirectResponse(f"/dashboard?oauth_success=1&provider=google&token={token}")
    redirect.set_cookie(
        key="contently_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return redirect


@router.get("/github/authorize")
def github_authorize():
    """Initiate GitHub OAuth flow."""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub OAuth is not configured on this server. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env, or use interactive one-click OAuth.",
        )
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "user:email read:user",
    }
    url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/github/callback")
async def github_callback(code: str = Query(...), db: Session = Depends(get_db)):
    """Process GitHub OAuth callback with code exchange."""
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub OAuth credentials are missing in server settings.",
        )

    token_url = "https://github.com/login/oauth/access_token"
    token_headers = {"Accept": "application/json"}
    token_data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(token_url, headers=token_headers, data=token_data)
        if token_resp.status_code != 200:
            logger.error("GitHub token exchange error: %s", token_resp.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub OAuth token exchange failed: {token_resp.text}",
            )
        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=token_json.get("error_description", "Failed to retrieve access token from GitHub."),
            )

        auth_headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        user_resp = await client.get("https://api.github.com/user", headers=auth_headers)
        if user_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch GitHub user info.")
        gh_user = user_resp.json()

        email = gh_user.get("email")
        if not email:
            emails_resp = await client.get("https://api.github.com/user/emails", headers=auth_headers)
            if emails_resp.status_code == 200:
                emails_list = emails_resp.json()
                for em in emails_list:
                    if em.get("primary") and em.get("verified"):
                        email = em.get("email")
                        break
                if not email and emails_list:
                    email = emails_list[0].get("email")

        if not email:
            email = f"{gh_user.get('login')}@users.noreply.github.com"

    oauth_req = OAuthRequest(
        provider="github",
        email=email,
        name=gh_user.get("name") or gh_user.get("login"),
        avatar_url=gh_user.get("avatar_url"),
        provider_id=str(gh_user.get("id")),
    )
    result = AuthService.oauth_login_or_signup(db, oauth_req)
    token = result["token"]

    redirect = RedirectResponse(f"/dashboard?oauth_success=1&provider=github&token={token}")
    redirect.set_cookie(
        key="contently_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return redirect


@router.post("/logout")
def logout(response: Response):
    """Log out current session and delete cookie."""
    response.delete_cookie("contently_token")
    return {"success": True, "message": "Logged out of Contently session successfully."}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Fetch profile of currently authenticated user."""
    return current_user

