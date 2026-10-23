# Purpose: Service layer for receipt management, queries, file attachments, and soft deletion.
# Security: Enforces user_id filtering on all queries; returns 404 for other users' records.

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models.category import Category
from app.models.receipt import Receipt
from app.schemas.receipt import ReceiptCreate, ReceiptUpdate
from app.services.audit import log_audit_event
from app.services.file_storage import delete_stored_file, save_user_file

DEFAULT_CATEGORIES = [
    "Food & Drinks",
    "Groceries",
    "Transport",
    "Shopping",
    "Bills & Utilities",
    "Health",
    "Entertainment",
    "Education",
    "Travel",
    "Other",
]


def seed_default_categories(db: Session, user_id: int) -> None:
    """Seed initial standard categories for a new user."""
    for name in DEFAULT_CATEGORIES:
        exists = (
            db.query(Category)
            .filter(Category.user_id == user_id, Category.name == name)
            .first()
        )
        if not exists:
            db.add(Category(user_id=user_id, name=name))
    db.commit()


def get_receipt(db: Session, user_id: int, receipt_id: int, include_deleted: bool = False) -> Receipt:
    """Fetch a single receipt belonging to user_id. Raises 404 if not found or belongs to another user."""
    query = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.user_id == user_id)
    if not include_deleted:
        query = query.filter(Receipt.deleted_at.is_(None))
    receipt = query.first()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found",
        )
    return receipt


def list_receipts(
    db: Session,
    user_id: int,
    search: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Receipt], int]:
    """List non-deleted receipts for user with search, filtering, and pagination."""
    query = db.query(Receipt).filter(
        Receipt.user_id == user_id,
        Receipt.deleted_at.is_(None),
    )

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Receipt.merchant.ilike(search_term),
                Receipt.notes.ilike(search_term),
                Receipt.shared_with.ilike(search_term),
            )
        )

    if start_date:
        query = query.filter(Receipt.receipt_date >= start_date)

    if end_date:
        query = query.filter(Receipt.receipt_date <= end_date)

    if category_id is not None:
        query = query.filter(Receipt.category_id == category_id)

    total = query.count()
    items = (
        query.order_by(Receipt.receipt_date.desc(), Receipt.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return items, total


def create_receipt(db: Session, user_id: int, data: ReceiptCreate) -> Receipt:
    """Create a new receipt scoped to user_id."""
    # Verify category belongs to user if specified
    if data.category_id is not None:
        cat = (
            db.query(Category)
            .filter(Category.id == data.category_id, Category.user_id == user_id)
            .first()
        )
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected category does not exist",
            )

    receipt = Receipt(
        user_id=user_id,
        category_id=data.category_id,
        merchant=data.merchant.strip(),
        receipt_date=data.receipt_date,
        my_share_sen=data.my_share_sen,
        receipt_total_sen=data.receipt_total_sen,
        currency=data.currency or "MYR",
        shared_with=data.shared_with.strip() if data.shared_with else None,
        notes=data.notes.strip() if data.notes else None,
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


def update_receipt(db: Session, user_id: int, receipt_id: int, data: ReceiptUpdate) -> Receipt:
    """Update an existing active receipt."""
    receipt = get_receipt(db, user_id, receipt_id)

    if data.category_id is not None:
        cat = (
            db.query(Category)
            .filter(Category.id == data.category_id, Category.user_id == user_id)
            .first()
        )
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected category does not exist",
            )
        receipt.category_id = data.category_id

    # Check totals consistency
    my_share = data.my_share_sen if data.my_share_sen is not None else receipt.my_share_sen
    total = data.receipt_total_sen if data.receipt_total_sen is not None else receipt.receipt_total_sen
    if total is not None and total < my_share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="receipt_total_sen must be greater than or equal to my_share_sen",
        )

    if data.merchant is not None:
        receipt.merchant = data.merchant.strip()
    if data.receipt_date is not None:
        receipt.receipt_date = data.receipt_date
    if data.my_share_sen is not None:
        receipt.my_share_sen = data.my_share_sen
    if data.receipt_total_sen is not None:
        receipt.receipt_total_sen = data.receipt_total_sen
    if data.currency is not None:
        receipt.currency = data.currency
    if data.shared_with is not None:
        receipt.shared_with = data.shared_with.strip() if data.shared_with else None
    if data.notes is not None:
        receipt.notes = data.notes.strip() if data.notes else None

    db.commit()
    db.refresh(receipt)
    return receipt


def soft_delete_receipt(db: Session, user_id: int, receipt_id: int) -> Receipt:
    """Soft-delete a receipt by setting deleted_at timestamp."""
    receipt = get_receipt(db, user_id, receipt_id)
    receipt.deleted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(receipt)
    return receipt


def list_trash_receipts(db: Session, user_id: int) -> list[tuple[Receipt, int]]:
    """List soft-deleted receipts for user with days remaining calculated."""
    now = datetime.now(timezone.utc)
    receipts = (
        db.query(Receipt)
        .filter(Receipt.user_id == user_id, Receipt.deleted_at.is_not(None))
        .order_by(Receipt.deleted_at.desc())
        .all()
    )

    items = []
    for r in receipts:
        d_at = r.deleted_at
        if d_at.tzinfo is None:
            d_at = d_at.replace(tzinfo=timezone.utc)
        days_passed = (now - d_at).days
        days_remaining = max(0, settings.RETENTION_DAYS - days_passed)
        items.append((r, days_remaining))
    return items


def restore_receipt(db: Session, user_id: int, receipt_id: int) -> Receipt:
    """Restore a soft-deleted receipt."""
    receipt = get_receipt(db, user_id, receipt_id, include_deleted=True)
    if not receipt.deleted_at:
        return receipt  # already active
    receipt.deleted_at = None
    db.commit()
    db.refresh(receipt)
    return receipt


def permanent_delete_receipt(db: Session, user_id: int, receipt_id: int) -> None:
    """Permanently delete a receipt and its attachment file from disk."""
    receipt = get_receipt(db, user_id, receipt_id, include_deleted=True)
    if receipt.file_path:
        delete_stored_file(receipt.file_path)

    db.delete(receipt)
    db.commit()

    log_audit_event(
        db=db,
        event="receipt_purged",
        user_id=user_id,
        detail=f"User permanently deleted receipt #{receipt_id}",
    )


def attach_receipt_file(
    db: Session,
    user_id: int,
    receipt_id: int,
    file_bytes: bytes,
    original_filename: str,
) -> Receipt:
    """Save and attach a verified file to a receipt, replacing any prior file."""
    receipt = get_receipt(db, user_id, receipt_id, include_deleted=False)

    # If there is an existing file, remove it
    if receipt.file_path:
        delete_stored_file(receipt.file_path)

    relative_path, _ = save_user_file(user_id=user_id, file_bytes=file_bytes)
    receipt.file_path = relative_path
    receipt.original_filename = original_filename[:255] if original_filename else "receipt"

    db.commit()
    db.refresh(receipt)
    return receipt


def remove_receipt_file(db: Session, user_id: int, receipt_id: int) -> Receipt:
    """Remove attached file from disk and clear receipt attachment attributes."""
    receipt = get_receipt(db, user_id, receipt_id, include_deleted=False)
    if receipt.file_path:
        delete_stored_file(receipt.file_path)
        receipt.file_path = None
        receipt.original_filename = None
        db.commit()
        db.refresh(receipt)
    return receipt
