# Purpose: FastAPI dependencies for user authentication, role checks, and IP extraction.
# Security: Enforces deny-by-default access; validates active status and admin role on the server.

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user import User
from app.security.sessions import verify_session


def get_client_ip(request: Request) -> str:
    """Extract client IP address safely from headers or connection."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the leftmost untrusted client IP
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Validate session cookie and return the authenticated user; raises 401 if unauthenticated."""
    raw_token = request.cookies.get(settings.COOKIE_NAME)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = verify_session(db, raw_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalid or expired",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return user


def require_active_user(user: User = Depends(get_current_user)) -> User:
    """Ensure the user is active (already validated in get_current_user)."""
    return user


def require_normal_authenticated_user(
    user: User = Depends(require_active_user),
) -> User:
    """Ensure user is active and has completed any forced password changes."""
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must change password before continuing",
        )
    return user


def require_admin(
    user: User = Depends(require_active_user),
) -> User:
    """Strictly enforce that the authenticated user possesses the 'admin' role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
