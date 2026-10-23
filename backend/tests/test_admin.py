# Purpose: Test suite for administrative privilege enforcement and security invariants.
# Security: Asserts 401/403 controls on all admin routes; verifies aggregate-only dashboard visibility.



ADMIN_ENDPOINTS = [
    ("GET", "/api/admin/dashboard"),
    ("GET", "/api/admin/audit-log"),
    ("GET", "/api/admin/users"),
    ("POST", "/api/admin/users"),
    ("PATCH", "/api/admin/users/1"),
    ("POST", "/api/admin/users/1/reset-password"),
]


def test_admin_endpoints_require_authentication(client):
    """Unauthenticated requests must return 401 on every admin route."""
    for method, path in ADMIN_ENDPOINTS:
        if method == "GET":
            resp = client.get(path)
        elif method == "POST":
            resp = client.post(path, json={})
        elif method == "PATCH":
            resp = client.patch(path, json={})
        assert resp.status_code == 401, f"Failed 401 check on {method} {path}"


def test_admin_endpoints_forbidden_for_regular_users(auth_client_a):
    """Authenticated non-admin users must return 403 on every admin route."""
    for method, path in ADMIN_ENDPOINTS:
        if method == "GET":
            resp = auth_client_a.get(path)
        elif method == "POST":
            resp = auth_client_a.post(path, json={})
        elif method == "PATCH":
            resp = auth_client_a.patch(path, json={})
        assert resp.status_code == 403, f"Failed 403 check on {method} {path}"


def test_admin_dashboard_returns_aggregates_only(auth_admin):
    resp = auth_admin.get("/api/admin/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    # Must contain high level metrics
    assert "total_users" in data
    assert "active_users" in data
    assert "disabled_users" in data
    assert "total_receipts" in data
    assert "trash_receipts" in data
    assert "total_storage_bytes" in data
    assert "receipts_per_day_30d" in data
    assert "users_summary" in data

    # Check that users_summary contains only aggregates (NO receipt descriptions or totals)
    for u in data["users_summary"]:
        assert "username" in u
        assert "receipt_count" in u
        assert "storage_bytes" in u
        # Must not contain receipt contents
        assert "receipts" not in u
        assert "expenses" not in u


def test_admin_user_lifecycle_and_self_protection(auth_admin, admin_user, db):
    # 1. Admin creates a user
    create_resp = auth_admin.post(
        "/api/admin/users",
        json={
            "username": "new_created_user",
            "email": "new_created@example.com",
            "password": "TemporaryPassword123!",
            "role": "user",
        },
    )
    assert create_resp.status_code == 201
    created_id = create_resp.json()["id"]

    # 2. Admin cannot disable themselves
    disable_self = auth_admin.patch(
        f"/api/admin/users/{admin_user.id}",
        json={"is_active": False},
    )
    assert disable_self.status_code == 400
    assert "cannot disable their own account" in disable_self.json()["detail"]

    # 3. Admin cannot demote themselves
    demote_self = auth_admin.patch(
        f"/api/admin/users/{admin_user.id}",
        json={"role": "user"},
    )
    assert demote_self.status_code == 400
    assert "cannot demote their own account" in demote_self.json()["detail"]

    # 4. Admin disables other user
    disable_other = auth_admin.patch(
        f"/api/admin/users/{created_id}",
        json={"is_active": False},
    )
    assert disable_other.status_code == 200
    assert disable_other.json()["is_active"] is False

    # 5. Admin resets password for user
    reset_resp = auth_admin.post(
        f"/api/admin/users/{created_id}/reset-password",
        json={"new_password": "NewResetPassword999!"},
    )
    assert reset_resp.status_code == 200
