# Purpose: Test suite for receipt CRUD operations, monetary validations, and filtering.
# Security: Validates positive monetary constraints, boundary checks, and proper sanitization.



def test_receipt_crud_and_sen_validation(auth_client_a):
    # 1. Validation error: my_share_sen <= 0
    err1 = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "Test", "receipt_date": "2026-10-01", "my_share_sen": 0},
    )
    assert err1.status_code == 422

    # 2. Validation error: total < my_share
    err2 = auth_client_a.post(
        "/api/receipts",
        json={
            "merchant": "Test",
            "receipt_date": "2026-10-01",
            "my_share_sen": 5000,
            "receipt_total_sen": 2000,
        },
    )
    assert err2.status_code == 422

    # 3. Create valid receipt
    resp = auth_client_a.post(
        "/api/receipts",
        json={
            "merchant": "Village Park Nasi Lemak",
            "receipt_date": "2026-10-05",
            "my_share_sen": 1500,
            "receipt_total_sen": 4500,
            "shared_with": "Ali & John",
            "notes": "Crispy fried chicken",
        },
    )
    assert resp.status_code == 201
    created = resp.json()
    r_id = created["id"]
    assert created["my_share_sen"] == 1500
    assert created["receipt_total_sen"] == 4500
    assert created["merchant"] == "Village Park Nasi Lemak"

    # 4. Read receipt
    get_resp = auth_client_a.get(f"/api/receipts/{r_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == r_id

    # 5. Update receipt
    update_resp = auth_client_a.put(
        f"/api/receipts/{r_id}",
        json={"merchant": "Village Park Restaurant", "my_share_sen": 1600},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["merchant"] == "Village Park Restaurant"
    assert update_resp.json()["my_share_sen"] == 1600


def test_receipt_search_filter_pagination(auth_client_a):
    # Create several receipts for searching and filtering
    auth_client_a.post(
        "/api/receipts",
        json={
            "merchant": "Starbucks Reserve",
            "receipt_date": "2026-10-01",
            "my_share_sen": 2200,
            "notes": "Nitro cold brew coffee",
        },
    )
    auth_client_a.post(
        "/api/receipts",
        json={
            "merchant": "Uniqlo Clothing",
            "receipt_date": "2026-10-03",
            "my_share_sen": 8900,
            "notes": "Jeans",
        },
    )

    # Search by merchant keyword
    res_search = auth_client_a.get("/api/receipts?search=Starbucks")
    assert res_search.status_code == 200
    items = res_search.json()["items"]
    assert len(items) >= 1
    assert any("Starbucks" in r["merchant"] for r in items)

    # Search by notes keyword
    res_notes = auth_client_a.get("/api/receipts?search=Nitro")
    assert res_notes.status_code == 200
    assert len(res_notes.json()["items"]) >= 1

    # Filter by date range
    res_date = auth_client_a.get("/api/receipts?start_date=2026-10-02&end_date=2026-10-04")
    assert res_date.status_code == 200
    date_items = res_date.json()["items"]
    for item in date_items:
        assert "2026-10-02" <= item["receipt_date"] <= "2026-10-04"

    # Pagination
    res_page = auth_client_a.get("/api/receipts?page=1&page_size=1")
    assert res_page.status_code == 200
    assert len(res_page.json()["items"]) == 1
    assert res_page.json()["page_size"] == 1
