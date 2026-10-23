# Purpose: Test suite for authentication, session lifecycles, and rate limiting.
# Security: Validates brute force rate limiting, session invalidation, and password policies.

from fastapi.testclient import TestClient

from app.config import settings
from app.models.audit_log import AuditLog


def test_login_success(client, user_a, db):
    response = client.post(
        "/api/auth/login",
        json={"username": "user_a", "password": "UserAPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert data["user"]["username"] == "user_a"

    # Verify session cookie was set
    cookie = response.cookies.get(settings.COOKIE_NAME)
    assert cookie is not None

    # Verify audit log
    log = (
        db.query(AuditLog)
        .filter(AuditLog.event == "login_success", AuditLog.user_id == user_a.id)
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert log is not None


def test_login_failure_wrong_password(client, user_a, db):
    response = client.post(
        "/api/auth/login",
        json={"username": "user_a", "password": "WrongPassword999!"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid username or password"

    # Verify audit log
    log = (
        db.query(AuditLog)
        .filter(AuditLog.event == "login_failed")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert log is not None


def test_login_failure_nonexistent_user(client, db):
    response = client.post(
        "/api/auth/login",
        json={"username": "nonexistent_ghost", "password": "SomePassword123!"},
    )
    assert response.status_code == 400
    # Generic error message to prevent username enumeration
    assert response.json()["detail"] == "Invalid username or password"


def test_login_rate_limiting(client):
    # Attempt 5 consecutive failed logins
    for _ in range(5):
        resp = client.post(
            "/api/auth/login",
            json={"username": "attack_target", "password": "WrongPassword1!"},
        )
        assert resp.status_code == 400

    # 6th attempt should be blocked with 429
    resp6 = client.post(
        "/api/auth/login",
        json={"username": "attack_target", "password": "WrongPassword1!"},
    )
    assert resp6.status_code == 429
    assert "Too many failed login attempts" in resp6.json()["detail"]


def test_logout(auth_client_a, db, user_a):
    # Authenticated request works
    me_resp = auth_client_a.get("/api/auth/me")
    assert me_resp.status_code == 200

    # Logout
    logout_resp = auth_client_a.post("/api/auth/logout")
    assert logout_resp.status_code == 200

    # Cookie cleared, next request fails with 401
    me_resp_after = auth_client_a.get("/api/auth/me")
    assert me_resp_after.status_code == 401


def test_forced_password_change_flow(auth_forced_user, forced_user, db):
    # User with must_change_password=True should be rejected on protected resources with 403
    receipts_resp = auth_forced_user.get("/api/receipts")
    assert receipts_resp.status_code == 403
    assert "Must change password" in receipts_resp.json()["detail"]

    # Perform password change
    change_resp = auth_forced_user.post(
        "/api/auth/change-password",
        json={
            "current_password": "TempPassword123!",
            "new_password": "BrandNewSecurePassword123!",
        },
    )
    assert change_resp.status_code == 200

    # User flag must_change_password should now be False
    db.refresh(forced_user)
    assert forced_user.must_change_password is False

    # Now protected resources are accessible
    receipts_resp2 = auth_forced_user.get("/api/receipts")
    assert receipts_resp2.status_code == 200


def test_change_password_invalidates_other_sessions(client, user_a, db):
    from app.security.sessions import create_session

    # Create 2 sessions for user_a
    token1, _ = create_session(db, user_a.id)
    token2, _ = create_session(db, user_a.id)

    client1 = TestClient(client.app, base_url="http://testserver")
    client1.cookies.set(settings.COOKIE_NAME, token1)

    client2 = TestClient(client.app, base_url="http://testserver")
    client2.cookies.set(settings.COOKIE_NAME, token2)

    assert client1.get("/api/auth/me").status_code == 200
    assert client2.get("/api/auth/me").status_code == 200

    # Client 1 changes password
    res = client1.post(
        "/api/auth/change-password",
        json={
            "current_password": "UserAPassword123!",
            "new_password": "ReplacementPassword999!",
        },
    )
    assert res.status_code == 200

    # Client 1 remains authenticated
    assert client1.get("/api/auth/me").status_code == 200

    # Client 2 session is invalidated
    assert client2.get("/api/auth/me").status_code == 401
