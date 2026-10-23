# Purpose: Test suite for monthly expense report aggregation and percentages.
# Security: Asserts mathematical isolation and verification that soft-deleted entries do not contaminate reports.

import pytest

from app.models.category import Category
from app.models.receipt import Receipt


def test_monthly_report_calculations_and_previous_month(auth_client_a, db, user_a):
    # Clear prior receipts for user_a to guarantee calculation isolation
    db.query(Receipt).filter(Receipt.user_id == user_a.id).delete()
    db.commit()

    # Fetch or create two distinct categories
    cats = db.query(Category).filter(Category.user_id == user_a.id).all()
    cat_food = cats[0]
    cat_transport = cats[1]

    # Create previous month (2026-09) active receipts
    # Total = 10000 sen (RM 100.00)
    auth_client_a.post(
        "/api/receipts",
        json={
            "merchant": "Sep Fuel",
            "receipt_date": "2026-09-15",
            "my_share_sen": 10000,
            "category_id": cat_transport.id,
        },
    )

    # Create current month (2026-10) receipts:
    # Receipt 1: Food 6000 sen
    # Receipt 2: Food 4000 sen
    # Receipt 3: Transport 5000 sen
    # Receipt 4: Soft-deleted 2000 sen (should NOT be counted!)
    auth_client_a.post(
        "/api/receipts",
        json={
            "merchant": "Oct Lunch",
            "receipt_date": "2026-10-02",
            "my_share_sen": 6000,
            "category_id": cat_food.id,
        },
    )

    auth_client_a.post(
        "/api/receipts",
        json={
            "merchant": "Oct Dinner",
            "receipt_date": "2026-10-03",
            "my_share_sen": 4000,
            "category_id": cat_food.id,
        },
    )

    auth_client_a.post(
        "/api/receipts",
        json={
            "merchant": "Oct MRT",
            "receipt_date": "2026-10-04",
            "my_share_sen": 5000,
            "category_id": cat_transport.id,
        },
    )

    r_del = auth_client_a.post(
        "/api/receipts",
        json={
            "merchant": "Oct Deleted Item",
            "receipt_date": "2026-10-05",
            "my_share_sen": 2000,
            "category_id": cat_food.id,
        },
    ).json()
    # Soft delete r_del
    auth_client_a.delete(f"/api/receipts/{r_del['id']}")

    # Query report for 2026-10
    resp = auth_client_a.get("/api/reports/monthly?month=2026-10")
    assert resp.status_code == 200
    report = resp.json()

    # Total active for Oct = 6000 + 4000 + 5000 = 15000 sen (RM 150.00)
    assert report["total_sen"] == 15000
    assert report["receipt_count"] == 3

    # Previous month = 10000 sen
    assert report["previous_month"] == "2026-09"
    assert report["previous_month_total_sen"] == 10000

    # Difference = 15000 - 10000 = +5000 sen
    assert report["diff_sen"] == 5000
    # Diff percentage = ((15000 - 10000) / 10000) * 100 = 50.0%
    assert report["diff_percentage"] == 50.0

    # Category breakdown:
    # Food: 10000 sen out of 15000 sen = 66.67%
    # Transport: 5000 sen out of 15000 sen = 33.33%
    cats_breakdown = {c["category_name"]: c for c in report["categories"]}
    assert cat_food.name in cats_breakdown
    assert cat_transport.name in cats_breakdown

    assert cats_breakdown[cat_food.name]["total_sen"] == 10000
    assert cats_breakdown[cat_food.name]["percentage"] == pytest.approx(66.67, 0.01)
    assert cats_breakdown[cat_food.name]["count"] == 2

    assert cats_breakdown[cat_transport.name]["total_sen"] == 5000
    assert cats_breakdown[cat_transport.name]["percentage"] == pytest.approx(33.33, 0.01)
    assert cats_breakdown[cat_transport.name]["count"] == 1
