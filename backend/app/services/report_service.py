# Purpose: Monthly report aggregation and category breakdown calculation service.
# Security: Scopes financial metrics strictly to the requesting user; ignores soft-deleted items.

from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.schemas.report import CategoryBreakdownItem, MonthlyReportResponse


def get_month_boundaries(year: int, month: int) -> tuple[date, date]:
    """Return start date of the given month and start date of the subsequent month."""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    return start_date, end_date


def get_previous_month(year: int, month: int) -> tuple[int, int, str]:
    """Calculate the previous year, month, and formatted 'YYYY-MM' string."""
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1
    return prev_year, prev_month, f"{prev_year:04d}-{prev_month:02d}"


def get_monthly_report(db: Session, user_id: int, month_str: str) -> MonthlyReportResponse:
    """Generate detailed monthly expense statistics and category breakdowns for the user."""
    try:
        parts = month_str.split("-")
        if len(parts) != 2:
            raise ValueError
        year, month = int(parts[0]), int(parts[1])
        if not (1 <= month <= 12 and 1900 <= year <= 2100):
            raise ValueError
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month format. Expected 'YYYY-MM' (e.g. 2026-10)",
        )

    start_date, end_date = get_month_boundaries(year, month)
    prev_year, prev_month, prev_month_str = get_previous_month(year, month)
    prev_start_date, prev_end_date = get_month_boundaries(prev_year, prev_month)

    # 1. Fetch current month active receipts
    current_receipts = (
        db.query(Receipt)
        .filter(
            Receipt.user_id == user_id,
            Receipt.deleted_at.is_(None),
            Receipt.receipt_date >= start_date,
            Receipt.receipt_date < end_date,
        )
        .all()
    )

    total_sen = sum(r.my_share_sen for r in current_receipts)
    receipt_count = len(current_receipts)

    # Category breakdown
    cat_map: dict[Optional[int], dict] = {}
    for r in current_receipts:
        cid = r.category_id
        if cid not in cat_map:
            cname = r.category.name if r.category else "Uncategorized"
            cat_map[cid] = {
                "category_id": cid,
                "category_name": cname,
                "total_sen": 0,
                "count": 0,
            }
        cat_map[cid]["total_sen"] += r.my_share_sen
        cat_map[cid]["count"] += 1

    categories: list[CategoryBreakdownItem] = []
    for _cid, data in cat_map.items():
        pct = round((data["total_sen"] / total_sen * 100), 2) if total_sen > 0 else 0.0
        categories.append(
            CategoryBreakdownItem(
                category_id=data["category_id"],
                category_name=data["category_name"],
                total_sen=data["total_sen"],
                percentage=pct,
                count=data["count"],
            )
        )

    # Sort categories by total_sen descending
    categories.sort(key=lambda c: c.total_sen, reverse=True)

    # 2. Fetch previous month total
    prev_receipts = (
        db.query(Receipt)
        .filter(
            Receipt.user_id == user_id,
            Receipt.deleted_at.is_(None),
            Receipt.receipt_date >= prev_start_date,
            Receipt.receipt_date < prev_end_date,
        )
        .all()
    )
    previous_month_total_sen = sum(r.my_share_sen for r in prev_receipts)

    diff_sen = total_sen - previous_month_total_sen
    diff_percentage = None
    if previous_month_total_sen > 0:
        diff_percentage = round((diff_sen / previous_month_total_sen) * 100, 2)

    return MonthlyReportResponse(
        month=month_str,
        total_sen=total_sen,
        receipt_count=receipt_count,
        categories=categories,
        previous_month=prev_month_str,
        previous_month_total_sen=previous_month_total_sen,
        diff_sen=diff_sen,
        diff_percentage=diff_percentage,
    )
