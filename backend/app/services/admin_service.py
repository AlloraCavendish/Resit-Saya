# Purpose: Admin management service for system metrics, user administration, and security audit logs.
# Security: Prevents admin privilege escalation/self-demotion; guarantees aggregate-only visibility without receipt data.

from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.audit_log import AuditLog
from app.models.receipt import Receipt
from app.models.user import User
from app.schemas.admin import (
    AdminDashboardResponse,
    AdminUserCreate,
    AdminUserSummary,
    AuditLogItem,
    DailyReceiptCount,
    LastPurgeJobInfo,
)
from app.security.passwords import hash_password
from app.security.sessions import invalidate_user_sessions
from app.services.audit import log_audit_event
from app.services.receipt_service import seed_default_categories


def _get_user_storage_bytes(user_id: int) -> int:
    """Calculate disk storage usage for a given user's uploads."""
    user_dir = settings.upload_path / str(user_id)
    if not user_dir.is_dir():
        return 0
    total = 0
    try:
        for entry in user_dir.glob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception:
        pass
    return total


def get_admin_dashboard(db: Session) -> AdminDashboardResponse:
    """Compile system aggregates and performance data without exposing user receipts or finances."""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()  # noqa: E712
    disabled_users = db.query(User).filter(User.is_active == False).count()  # noqa: E712

    total_receipts = db.query(Receipt).filter(Receipt.deleted_at.is_(None)).count()
    trash_receipts = db.query(Receipt).filter(Receipt.deleted_at.is_not(None)).count()

    # User rows (aggregate metrics per user)
    users = db.query(User).order_by(User.id.asc()).all()
    users_summary: list[AdminUserSummary] = []
    total_storage_bytes = 0

    for u in users:
        r_count = (
            db.query(Receipt)
            .filter(Receipt.user_id == u.id, Receipt.deleted_at.is_(None))
            .count()
        )
        u_storage = _get_user_storage_bytes(u.id)
        total_storage_bytes += u_storage
        users_summary.append(
            AdminUserSummary(
                id=u.id,
                username=u.username,
                email=u.email,
                role=u.role,
                is_active=u.is_active,
                last_login_at=u.last_login_at,
                receipt_count=r_count,
                storage_bytes=u_storage,
            )
        )

    # 30-day receipts created trend
    tz = ZoneInfo(settings.APP_TIMEZONE)
    now_local = datetime.now(tz)
    receipts_per_day: list[DailyReceiptCount] = []

    # Calculate receipts created per day for the last 30 calendar days
    for i in range(29, -1, -1):
        day_date = (now_local - timedelta(days=i)).date()
        day_str = day_date.isoformat()
        # Count receipts with receipt_date == day_date or created_at matching date
        day_count = (
            db.query(Receipt)
            .filter(
                func.date(Receipt.created_at) == day_date,
            )
            .count()
        )
        receipts_per_day.append(DailyReceiptCount(date=day_str, count=day_count))

    # Recent audit logs (last 50)
    audit_rows = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(50)
        .all()
    )
    # Map user IDs to usernames for audit log display
    user_id_map = {u.id: u.username for u in users}
    recent_logs: list[AuditLogItem] = []
    for log in audit_rows:
        uname = user_id_map.get(log.user_id) if log.user_id else None
        recent_logs.append(
            AuditLogItem(
                id=log.id,
                user_id=log.user_id,
                username=uname,
                event=log.event,
                ip=log.ip,
                detail=log.detail,
                created_at=log.created_at,
            )
        )

    # Last purge job info
    last_purge = (
        db.query(AuditLog)
        .filter(AuditLog.event == "purge_job_run")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    last_purge_info = None
    if last_purge:
        # Extract count if possible from detail
        count = 0
        try:
            parts = last_purge.detail.split(" ")
            for p in parts:
                if p.isdigit():
                    count = int(p)
                    break
        except Exception:
            pass
        last_purge_info = LastPurgeJobInfo(
            timestamp=last_purge.created_at,
            count_purged=count,
        )

    # Failed logins in the last 24 hours
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    failed_logins_24h = (
        db.query(AuditLog)
        .filter(AuditLog.event == "login_failed", AuditLog.created_at >= cutoff_24h)
        .count()
    )

    return AdminDashboardResponse(
        total_users=total_users,
        active_users=active_users,
        disabled_users=disabled_users,
        total_receipts=total_receipts,
        trash_receipts=trash_receipts,
        total_storage_bytes=total_storage_bytes,
        receipts_per_day_30d=receipts_per_day,
        users_summary=users_summary,
        recent_audit_logs=recent_logs,
        last_purge_job=last_purge_info,
        failed_logins_24h=failed_logins_24h,
        server_time=datetime.now(tz).isoformat(),
        server_timezone=settings.APP_TIMEZONE,
        app_version=settings.APP_VERSION,
    )


def list_audit_logs(
    db: Session,
    event_filter: Optional[str] = None,
    limit: int = 50,
) -> list[AuditLogItem]:
    """Retrieve audit log records with optional event filtering."""
    query = db.query(AuditLog)
    if event_filter:
        query = query.filter(AuditLog.event == event_filter.strip())
    rows = query.order_by(AuditLog.created_at.desc()).limit(min(limit, 100)).all()

    # Pre-fetch users for name mapping
    users = db.query(User.id, User.username).all()
    user_id_map = {uid: uname for uid, uname in users}

    result = []
    for r in rows:
        result.append(
            AuditLogItem(
                id=r.id,
                user_id=r.user_id,
                username=user_id_map.get(r.user_id) if r.user_id else None,
                event=r.event,
                ip=r.ip,
                detail=r.detail,
                created_at=r.created_at,
            )
        )
    return result


def admin_create_user(db: Session, data: AdminUserCreate, admin_ip: Optional[str] = None) -> User:
    """Create a new user with must_change_password=True and seed default categories."""
    username = data.username.strip().lower()
    email = data.email.strip().lower()

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Seed initial categories
    seed_default_categories(db, user.id)

    log_audit_event(
        db=db,
        event="user_created",
        user_id=user.id,
        ip=admin_ip,
        detail=f"Created user {username} with role {data.role}",
    )
    return user


def admin_update_user(
    db: Session,
    admin_user: User,
    target_user_id: int,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
    admin_ip: Optional[str] = None,
) -> User:
    """Modify user status or role; prevents self-demotion or self-disablement."""
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from disabling or demoting themselves
    if target_user.id == admin_user.id:
        if is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot disable their own account",
            )
        if role is not None and role != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot demote their own account",
            )

    if is_active is not None and is_active != target_user.is_active:
        target_user.is_active = is_active
        event_name = "user_enabled" if is_active else "user_disabled"
        log_audit_event(
            db=db,
            event=event_name,
            user_id=target_user.id,
            ip=admin_ip,
            detail=f"Admin {admin_user.username} set active={is_active} for {target_user.username}",
        )
        if not is_active:
            # Terminate active sessions for disabled user
            invalidate_user_sessions(db, target_user.id)

    if role is not None and role != target_user.role:
        old_role = target_user.role
        target_user.role = role
        log_audit_event(
            db=db,
            event="user_role_changed",
            user_id=target_user.id,
            ip=admin_ip,
            detail=f"Admin {admin_user.username} changed role from {old_role} to {role} for {target_user.username}",
        )

    db.commit()
    db.refresh(target_user)
    return target_user


def admin_reset_password(
    db: Session,
    admin_user: User,
    target_user_id: int,
    new_password: str,
    admin_ip: Optional[str] = None,
) -> None:
    """Reset target user password to a new temporary password and force change on next login."""
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    target_user.password_hash = hash_password(new_password)
    target_user.must_change_password = True
    db.commit()

    # Invalidate target user's existing sessions
    invalidate_user_sessions(db, target_user.id)

    log_audit_event(
        db=db,
        event="password_reset",
        user_id=target_user.id,
        ip=admin_ip,
        detail=f"Admin {admin_user.username} reset password for user {target_user.username}",
    )
