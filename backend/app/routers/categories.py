# Purpose: Router for category creation, retrieval, updates, and deletion.
# Security: Enforces strict user isolation; prevents duplicate category names per user.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.category import Category
from app.models.receipt import Receipt
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.security.deps import require_normal_authenticated_user

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    categories = (
        db.query(Category)
        .filter(Category.user_id == user.id)
        .order_by(Category.name.asc())
        .all()
    )

    out = []
    for c in categories:
        count = (
            db.query(Receipt)
            .filter(
                Receipt.user_id == user.id,
                Receipt.category_id == c.id,
                Receipt.deleted_at.is_(None),
            )
            .count()
        )
        out.append(
            CategoryOut(
                id=c.id,
                user_id=c.user_id,
                name=c.name,
                receipt_count=count,
            )
        )
    return out


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    name_clean = payload.name.strip()
    if not name_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name cannot be empty",
        )

    exists = (
        db.query(Category)
        .filter(Category.user_id == user.id, Category.name == name_clean)
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )

    cat = Category(user_id=user.id, name=name_clean)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return CategoryOut(id=cat.id, user_id=cat.user_id, name=cat.name, receipt_count=0)


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    cat = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user.id)
        .first()
    )
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    name_clean = payload.name.strip()
    if not name_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name cannot be empty",
        )

    duplicate = (
        db.query(Category)
        .filter(
            Category.user_id == user.id,
            Category.name == name_clean,
            Category.id != category_id,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Another category with this name already exists",
        )

    cat.name = name_clean
    db.commit()
    db.refresh(cat)

    count = (
        db.query(Receipt)
        .filter(
            Receipt.user_id == user.id,
            Receipt.category_id == cat.id,
            Receipt.deleted_at.is_(None),
        )
        .count()
    )
    return CategoryOut(id=cat.id, user_id=cat.user_id, name=cat.name, receipt_count=count)


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    cat = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user.id)
        .first()
    )
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # When deleting category, set category_id=None on any receipts
    db.query(Receipt).filter(
        Receipt.user_id == user.id,
        Receipt.category_id == category_id,
    ).update({Receipt.category_id: None})

    db.delete(cat)
    db.commit()
    return {"message": "Category deleted successfully"}
