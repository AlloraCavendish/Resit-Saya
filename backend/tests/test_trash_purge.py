# Purpose: Test suite for soft-delete, trash lifecycle, restoration, and automated purge retention.
# Security: Asserts expired data and files are permanently unlinked and audit events are generated.

from datetime import datetime, timedelta, timezone

from app.config import settings
from app.models.audit_log import AuditLog
from app.models.receipt import Receipt
from app.services.purge import purge_expired_deleted_receipts


def test_soft_delete_restore_and_permanent(auth_client_a, db, user_a, sample_image_bytes):
    # 1. Create receipt
    res = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "Trash Test Shop", "receipt_date": "2026-10-01", "my_share_sen": 3000},
    )
    r_id = res.json()["id"]

    # Attach file
    auth_client_a.post(
        f"/api/receipts/{r_id}/file",
        files={"file": ("trash.jpg", sample_image_bytes, "image/jpeg")},
    )

    # 2. Soft delete receipt
    del_res = auth_client_a.delete(f"/api/receipts/{r_id}")
    assert del_res.status_code == 200

    # 3. Receipt disappears from standard list
    list_res = auth_client_a.get("/api/receipts")
    assert not any(r["id"] == r_id for r in list_res.json()["items"])

    # 4. Appears in trash list with days_remaining
    trash_res = auth_client_a.get("/api/receipts/trash")
    assert trash_res.status_code == 200
    trash_items = trash_res.json()["items"]
    assert any(r["id"] == r_id for r in trash_items)
    target_trash = next(r for r in trash_items if r["id"] == r_id)
    assert target_trash["days_remaining"] == settings.RETENTION_DAYS

    # 5. Restore receipt
    restore_res = auth_client_a.post(f"/api/receipts/{r_id}/restore")
    assert restore_res.status_code == 200
    assert restore_res.json()["deleted_at"] is None

    # Re-appears in active list
    list_res2 = auth_client_a.get("/api/receipts")
    assert any(r["id"] == r_id for r in list_res2.json()["items"])

    # 6. Delete again and permanent delete
    auth_client_a.delete(f"/api/receipts/{r_id}")
    perm_res = auth_client_a.delete(f"/api/receipts/{r_id}/permanent")
    assert perm_res.status_code == 200

    # Verify completely gone from DB
    r_db = db.query(Receipt).filter(Receipt.id == r_id).first()
    assert r_db is None


def test_retention_purge_removes_expired_rows_and_files(auth_client_a, db, user_a, sample_image_bytes):
    # Create two receipts: one expired (> RETENTION_DAYS), one recent (< RETENTION_DAYS)
    r1 = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "Old Expired Receipt", "receipt_date": "2026-08-01", "my_share_sen": 1000},
    ).json()
    r2 = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "Recent Deleted Receipt", "receipt_date": "2026-10-01", "my_share_sen": 2000},
    ).json()

    # Upload files to both
    auth_client_a.post(f"/api/receipts/{r1['id']}/file", files={"file": ("f1.jpg", sample_image_bytes, "image/jpeg")})
    auth_client_a.post(f"/api/receipts/{r2['id']}/file", files={"file": ("f2.jpg", sample_image_bytes, "image/jpeg")})

    # Soft delete both
    auth_client_a.delete(f"/api/receipts/{r1['id']}")
    auth_client_a.delete(f"/api/receipts/{r2['id']}")

    # Backdate deleted_at of r1 to 35 days ago (past 30 day retention)
    r1_db = db.query(Receipt).filter(Receipt.id == r1["id"]).first()
    r1_db.deleted_at = datetime.now(timezone.utc) - timedelta(days=35)
    r1_file_path = settings.upload_path / r1_db.file_path

    # Backdate deleted_at of r2 to 10 days ago (within 30 day retention)
    r2_db = db.query(Receipt).filter(Receipt.id == r2["id"]).first()
    r2_db.deleted_at = datetime.now(timezone.utc) - timedelta(days=10)
    r2_file_path = settings.upload_path / r2_db.file_path

    db.commit()

    assert r1_file_path.exists()
    assert r2_file_path.exists()

    # Run purge service
    purged_count = purge_expired_deleted_receipts(db)
    assert purged_count >= 1

    # Verify r1 is gone from DB and disk
    assert db.query(Receipt).filter(Receipt.id == r1["id"]).first() is None
    assert not r1_file_path.exists()

    # Verify r2 remains in DB and disk
    assert db.query(Receipt).filter(Receipt.id == r2["id"]).first() is not None
    assert r2_file_path.exists()

    # Verify audit log was recorded
    audit = (
        db.query(AuditLog)
        .filter(AuditLog.event == "purge_job_run")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert audit is not None
    assert "permanently removed" in audit.detail or "Retention purge" in audit.detail
