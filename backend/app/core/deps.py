from datetime import UTC

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.user import User

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the current authenticated user from Bearer header or cookie."""
    token = None

    if credentials:
        token = credentials.credentials
    elif "Authorization" in request.headers:
        auth_header = request.headers["Authorization"]
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()
    elif "contently_token" in request.cookies:
        token = request.cookies["contently_token"]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def require_active_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Enforce active subscription status for protected premium features."""
    from datetime import datetime

    from backend.app.models.billing import Subscription

    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    now = datetime.now(UTC).replace(tzinfo=None)

    if sub and sub.status in ("active", "authenticated"):
        current_end_naive = sub.current_end.replace(tzinfo=None) if (sub.current_end and sub.current_end.tzinfo) else sub.current_end
        if not current_end_naive or current_end_naive >= now:
            return current_user

    # If demo/grandfathered Pro Creator without active cancellation
    if current_user.role == "Pro Creator" and (not sub or sub.status != "cancelled"):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail="Active Pro Creator subscription required to access this feature. Please visit Profile & Settings to upgrade.",
    )
