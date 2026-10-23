# Purpose: SQLAlchemy model definition for system security and administrative audit logging.
# Security: Immutably tracks security-sensitive events; never records passwords, tokens, or personal receipts.

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event = Column(String(64), nullable=False, index=True)
    ip = Column(String(64), nullable=True)
    detail = Column(String(512), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
