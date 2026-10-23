# Purpose: Audit logging service for recording security and administrative events.
# Security: Immutably persists security audit events; strictly prevents recording sensitive credentials.

from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_audit_event(
    db: Session,
    event: str,
    detail: str,
    user_id: Optional[int] = None,
    ip: Optional[str] = None,
) -> AuditLog:
    """Record a security event into the audit log."""
    # Sanitize detail length to fit column
    safe_detail = detail[:500]
    log_entry = AuditLog(
        user_id=user_id,
        event=event,
        ip=ip,
        detail=safe_detail,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
