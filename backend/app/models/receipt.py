# Purpose: SQLAlchemy model definition for receipts and expense entries.
# Security: Enforces user scoping, soft-deletion tracking, and indexing for fast query isolation.

from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    merchant = Column(String(255), nullable=False)
    receipt_date = Column(Date, nullable=False)
    my_share_sen = Column(Integer, nullable=False)
    receipt_total_sen = Column(Integer, nullable=True)
    currency = Column(String(3), default="MYR", nullable=False)
    shared_with = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=True)
    original_filename = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    __table_args__ = (
        Index("ix_receipts_user_date", "user_id", "receipt_date"),
        Index("ix_receipts_user_deleted", "user_id", "deleted_at"),
    )

    user = relationship("User", back_populates="receipts")
    category = relationship("Category", back_populates="receipts")
