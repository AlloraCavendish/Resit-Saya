# Purpose: Background retention purge service for soft-deleted receipts.
# Security: Permanently cleans up expired data and files, logging audit trails without exposing file contents.

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.receipt import Receipt
from app.services.audit import log_audit_event
from app.services.file_storage import delete_stored_file


def purge_expired_deleted_receipts(db: Session) -> int:
    """Permanently delete receipts soft-deleted longer than RETENTION_DAYS and remove files from disk."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_DAYS)

    deleted_receipts = (
        db.query(Receipt)
        .filter(Receipt.deleted_at.is_not(None))
        .all()
    )

    expired_receipts = []
    for r in deleted_receipts:
        d_at = r.deleted_at
        if d_at.tzinfo is None:
            d_at = d_at.replace(tzinfo=timezone.utc)
        if d_at < cutoff:
            expired_receipts.append(r)

    count = len(expired_receipts)
    if count == 0:
        log_audit_event(
            db=db,
            event="purge_job_run",
            detail=f"Retention purge executed: 0 receipts purged (retention: {settings.RETENTION_DAYS} days)",
        )
        return 0

    for receipt in expired_receipts:
        if receipt.file_path:
            delete_stored_file(receipt.file_path)
        db.delete(receipt)

    db.commit()

    log_audit_event(
        db=db,
        event="purge_job_run",
        detail=f"Retention purge executed: permanently removed {count} receipts older than {settings.RETENTION_DAYS} days",
    )

    return count
