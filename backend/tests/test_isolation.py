# Purpose: Test suite enforcing strict multi-user tenant isolation and authorization barriers.
# Security: Asserts that User B and Admin cannot access, modify, or download User A's data under any condition.



def test_user_cannot_access_other_users_receipts(auth_client_a, auth_client_b, auth_admin, sample_image_bytes):
    # 1. User A creates a receipt
    create_resp = auth_client_a.post(
        "/api/receipts",
        json={
            "merchant": "User A Private Store",
            "receipt_date": "2026-10-01",
            "my_share_sen": 2500,
            "receipt_total_sen": 5000,
            "shared_with": "Secret Friend",
            "notes": "User A Private Note",
        },
    )
    assert create_resp.status_code == 201
    receipt_a_id = create_resp.json()["id"]

    # 1b. User A uploads a file
    upload_resp = auth_client_a.post(
        f"/api/receipts/{receipt_a_id}/file",
        files={"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")},
    )
    assert upload_resp.status_code == 200

    # 2. User B attempts to read User A's receipt -> 404
    resp_b_get = auth_client_b.get(f"/api/receipts/{receipt_a_id}")
    assert resp_b_get.status_code == 404

    # 3. User B attempts to update User A's receipt -> 404
    resp_b_put = auth_client_b.put(
        f"/api/receipts/{receipt_a_id}",
        json={"merchant": "Hacked Merchant"},
    )
    assert resp_b_put.status_code == 404

    # 4. User B attempts to download User A's file -> 404
    resp_b_file = auth_client_b.get(f"/api/receipts/{receipt_a_id}/file")
    assert resp_b_file.status_code == 404

    # 5. User B attempts to delete User A's receipt -> 404
    resp_b_del = auth_client_b.delete(f"/api/receipts/{receipt_a_id}")
    assert resp_b_del.status_code == 404

    # 6. User B attempts to restore User A's receipt -> 404
    resp_b_restore = auth_client_b.post(f"/api/receipts/{receipt_a_id}/restore")
    assert resp_b_restore.status_code == 404

    # 7. User B attempts to permanent delete User A's receipt -> 404
    resp_b_perm = auth_client_b.delete(f"/api/receipts/{receipt_a_id}/permanent")
    assert resp_b_perm.status_code == 404

    # 8. Admin attempts to read User A's receipt -> 404 (Admin cannot read user receipts!)
    resp_admin_get = auth_admin.get(f"/api/receipts/{receipt_a_id}")
    assert resp_admin_get.status_code == 404

    # 9. Admin attempts to download User A's file -> 404
    resp_admin_file = auth_admin.get(f"/api/receipts/{receipt_a_id}/file")
    assert resp_admin_file.status_code == 404


def test_user_cannot_access_or_modify_other_users_categories(auth_client_a, auth_client_b):
    # User A creates a category
    create_cat = auth_client_a.post("/api/categories", json={"name": "User A Private Cat"})
    assert create_cat.status_code == 201
    cat_id = create_cat.json()["id"]

    # User B cannot see it in categories list
    list_b = auth_client_b.get("/api/categories")
    cat_names = [c["name"] for c in list_b.json()]
    assert "User A Private Cat" not in cat_names

    # User B cannot update User A's category -> 404
    put_b = auth_client_b.put(f"/api/categories/{cat_id}", json={"name": "Tampered Cat"})
    assert put_b.status_code == 404

    # User B cannot delete User A's category -> 404
    del_b = auth_client_b.delete(f"/api/categories/{cat_id}")
    assert del_b.status_code == 404
