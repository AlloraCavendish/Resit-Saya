# Purpose: Server-side session management and secure HttpOnly cookie handling.
# Security: Generates 256-bit entropy tokens, stores only SHA-256 hashes in database, uses HttpOnly SameSite cookies.

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.models.session import SessionModel
from app.models.user import User


def hash_token(raw_token: str) -> str:
    """Compute SHA-256 hash of a session token for safe storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_session(db: Session, user_id: int) -> tuple[str, SessionModel]:
    """Generate a crypto-secure session token, save its hash to the database, and return the token."""
    raw_token = secrets.token_urlsafe(32)
    token_h = hash_token(raw_token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.SESSION_DAYS)

    session_record = SessionModel(
        user_id=user_id,
        token_hash=token_h,
        created_at=now,
        expires_at=expires_at,
        last_seen_at=now,
    )
    db.add(session_record)
    db.commit()
    db.refresh(session_record)
    return raw_token, session_record


def verify_session(db: Session, raw_token: str) -> Optional[User]:
    """Verify session token against the database and return the associated active user."""
    if not raw_token:
        return None

    token_h = hash_token(raw_token)
    session_record = (
        db.query(SessionModel)
        .filter(SessionModel.token_hash == token_h)
        .first()
    )

    if not session_record:
        return None

    now = datetime.now(timezone.utc)
    # Check expiration (handle naive datetimes from SQLite)
    expires = session_record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if expires < now:
        db.delete(session_record)
        db.commit()
        return None

    # Update last_seen_at timestamp
    session_record.last_seen_at = now
    db.commit()

    return session_record.user


def invalidate_session(db: Session, raw_token: str) -> None:
    """Delete a specific session record from the database."""
    if not raw_token:
        return
    token_h = hash_token(raw_token)
    db.query(SessionModel).filter(SessionModel.token_hash == token_h).delete()
    db.commit()


def invalidate_user_sessions(db: Session, user_id: int, current_raw_token: Optional[str] = None) -> None:
    """Invalidate all sessions for a user, optionally preserving the current active session."""
    query = db.query(SessionModel).filter(SessionModel.user_id == user_id)
    if current_raw_token:
        current_hash = hash_token(current_raw_token)
        query = query.filter(SessionModel.token_hash != current_hash)
    query.delete(synchronize_session=False)
    db.commit()


def set_session_cookie(response: Response, raw_token: str) -> None:
    """Set HttpOnly SameSite=Lax session cookie on the response."""
    max_age_seconds = settings.SESSION_DAYS * 86400
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=max_age_seconds,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Delete the session cookie from the client."""
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
    )
