# Purpose: Router for receipt CRUD, soft-deletion, restoration, and secure attachment management.
# Security: Enforces strict user isolation; verifies file content before storage; guards file streaming.

from datetime import date
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.receipt import Receipt
from app.models.user import User
from app.schemas.receipt import (
    ReceiptCreate,
    ReceiptListResponse,
    ReceiptOut,
    ReceiptUpdate,
    TrashListResponse,
    TrashReceiptOut,
)
from app.security.deps import require_normal_authenticated_user
from app.services.file_storage import (
    detect_file_type_and_extension,
    resolve_user_file_path,
)
from app.services.receipt_service import (
    attach_receipt_file,
    create_receipt,
    get_receipt,
    list_receipts,
    list_trash_receipts,
    permanent_delete_receipt,
    remove_receipt_file,
    restore_receipt,
    soft_delete_receipt,
    update_receipt,
)

router = APIRouter(prefix="/receipts", tags=["receipts"])


def to_receipt_out(r: Receipt) -> ReceiptOut:
    """Helper to convert Receipt ORM model to ReceiptOut schema."""
    return ReceiptOut(
        id=r.id,
        user_id=r.user_id,
        category_id=r.category_id,
        category_name=r.category.name if r.category else None,
        merchant=r.merchant,
        receipt_date=r.receipt_date,
        my_share_sen=r.my_share_sen,
        receipt_total_sen=r.receipt_total_sen,
        currency=r.currency,
        shared_with=r.shared_with,
        notes=r.notes,
        file_path=r.file_path,
        original_filename=r.original_filename,
        has_file=bool(r.file_path),
        created_at=r.created_at,
        updated_at=r.updated_at,
        deleted_at=r.deleted_at,
    )


@router.get("", response_model=ReceiptListResponse)
def list_user_receipts(
    search: Optional[str] = Query(None, max_length=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    items, total = list_receipts(
        db=db,
        user_id=user.id,
        search=search,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return ReceiptListResponse(
        items=[to_receipt_out(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=ReceiptOut, status_code=status.HTTP_201_CREATED)
def create_new_receipt(
    payload: ReceiptCreate,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    receipt = create_receipt(db=db, user_id=user.id, data=payload)
    return to_receipt_out(receipt)


@router.get("/trash", response_model=TrashListResponse)
def get_trash(
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    items = list_trash_receipts(db=db, user_id=user.id)
    trash_items = []
    for r, days_remaining in items:
        ro = to_receipt_out(r)
        trash_items.append(
            TrashReceiptOut(
                **ro.model_dump(),
                days_remaining=days_remaining,
            )
        )
    return TrashListResponse(
        items=trash_items,
        total=len(trash_items),
    )


@router.get("/{receipt_id}", response_model=ReceiptOut)
def get_single_receipt(
    receipt_id: int,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    receipt = get_receipt(db=db, user_id=user.id, receipt_id=receipt_id)
    return to_receipt_out(receipt)


@router.put("/{receipt_id}", response_model=ReceiptOut)
def update_existing_receipt(
    receipt_id: int,
    payload: ReceiptUpdate,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    receipt = update_receipt(db=db, user_id=user.id, receipt_id=receipt_id, data=payload)
    return to_receipt_out(receipt)


@router.delete("/{receipt_id}")
def delete_receipt(
    receipt_id: int,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    soft_delete_receipt(db=db, user_id=user.id, receipt_id=receipt_id)
    return {"message": "Receipt moved to trash"}


@router.post("/{receipt_id}/restore", response_model=ReceiptOut)
def restore_deleted_receipt(
    receipt_id: int,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    receipt = restore_receipt(db=db, user_id=user.id, receipt_id=receipt_id)
    return to_receipt_out(receipt)


@router.delete("/{receipt_id}/permanent")
def permanently_delete_user_receipt(
    receipt_id: int,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    permanent_delete_receipt(db=db, user_id=user.id, receipt_id=receipt_id)
    return {"message": "Receipt permanently deleted"}


@router.post("/{receipt_id}/file", response_model=ReceiptOut)
async def upload_receipt_file(
    receipt_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    receipt = attach_receipt_file(
        db=db,
        user_id=user.id,
        receipt_id=receipt_id,
        file_bytes=contents,
        original_filename=file.filename or "receipt",
    )
    return to_receipt_out(receipt)


@router.get("/{receipt_id}/file")
def download_receipt_file(
    receipt_id: int,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    receipt = get_receipt(db=db, user_id=user.id, receipt_id=receipt_id, include_deleted=True)
    if not receipt.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt has no attached file",
        )

    target_disk_path = resolve_user_file_path(user.id, receipt.file_path)

    # Determine mime type from actual disk file
    with open(target_disk_path, "rb") as f:
        head_bytes = f.read(1024)
    try:
        mime_type, _ = detect_file_type_and_extension(head_bytes)
    except Exception:
        mime_type = "application/octet-stream"

    filename = receipt.original_filename or target_disk_path.name
    # Clean filename of unsafe quotes/headers
    safe_filename = filename.replace('"', "").replace("\r", "").replace("\n", "")

    return FileResponse(
        path=target_disk_path,
        media_type=mime_type,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f'inline; filename="{safe_filename}"',
        },
    )


@router.delete("/{receipt_id}/file", response_model=ReceiptOut)
def delete_receipt_file(
    receipt_id: int,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    receipt = remove_receipt_file(db=db, user_id=user.id, receipt_id=receipt_id)
    return to_receipt_out(receipt)
