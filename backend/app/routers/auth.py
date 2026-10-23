# Purpose: Router handling user authentication, session creation, logout, and password updates.
# Security: Enforces login rate limiting, generic failure messages, HttpOnly cookies, and session invalidation.

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserOut
from app.security.deps import get_client_ip, get_current_user, require_active_user
from app.security.passwords import hash_password, verify_password
from app.security.rate_limit import (
    clear_failed_attempts,
    is_rate_limited,
    record_failed_attempt,
)
from app.security.sessions import (
    clear_session_cookie,
    create_session,
    invalidate_session,
    invalidate_user_sessions,
    set_session_cookie,
)
from app.services.audit import log_audit_event

router = APIRouter(prefix="/auth", tags=["auth"])


class ChangePasswordPayload(BaseModel):
    current_password: Optional[str] = None
    new_password: str = Field(..., min_length=10, max_length=256)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    username_clean = payload.username.strip().lower()

    # 1. Rate limiting check
    if is_rate_limited(username_clean, ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again in 15 minutes.",
        )

    # 2. Look up user
    user = db.query(User).filter(User.username == username_clean).first()
    if not user or not verify_password(payload.password, user.password_hash):
        record_failed_attempt(username_clean, ip)
        log_audit_event(
            db=db,
            event="login_failed",
            detail=f"Failed login attempt for username '{username_clean}'",
            ip=ip,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password",
        )

    # 3. Verify user active status
    if not user.is_active:
        record_failed_attempt(username_clean, ip)
        log_audit_event(
            db=db,
            event="login_failed",
            user_id=user.id,
            detail=f"Disabled user '{username_clean}' attempted login",
            ip=ip,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password",
        )

    # Clear rate limit failure counters upon successful authentication
    clear_failed_attempts(username_clean, ip)

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Create server session and attach HttpOnly cookie
    raw_token, _ = create_session(db, user.id)
    set_session_cookie(response, raw_token)

    log_audit_event(
        db=db,
        event="login_success",
        user_id=user.id,
        detail=f"User '{user.username}' logged in successfully",
        ip=ip,
    )

    return LoginResponse(
        message="Login successful",
        user=UserOut.model_validate(user),
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    raw_token = request.cookies.get(settings.COOKIE_NAME)
    ip = get_client_ip(request)

    if raw_token:
        # Check user before invalidating
        from app.security.sessions import verify_session
        user = verify_session(db, raw_token)
        if user:
            log_audit_event(
                db=db,
                event="logout",
                user_id=user.id,
                detail=f"User '{user.username}' logged out",
                ip=ip,
            )
        invalidate_session(db, raw_token)

    clear_session_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordPayload,
    request: Request,
    user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    raw_token = request.cookies.get(settings.COOKIE_NAME)

    # If user is not under forced password change, current password is required
    if not user.must_change_password:
        if not payload.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required",
            )
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
    else:
        # If user is under forced password change and current_password was submitted, verify it
        if payload.current_password and not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current temporary password is incorrect",
            )

    # Check that new password isn't identical
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password",
        )

    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    db.commit()

    # Invalidate all other sessions for this user, keeping the current session active
    invalidate_user_sessions(db, user.id, current_raw_token=raw_token)

    log_audit_event(
        db=db,
        event="password_changed",
        user_id=user.id,
        detail=f"User '{user.username}' changed their password",
        ip=ip,
    )

    return {"message": "Password changed successfully"}
