# Purpose: Test suite for file attachment security, MIME-type verification, and size limits.
# Security: Asserts content inspection detects real types, blocks malicious payloads and oversized files.

from app.config import settings


def test_upload_valid_jpeg_and_download(auth_client_a, sample_image_bytes):
    # Create receipt
    r = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "Upload Shop", "receipt_date": "2026-10-01", "my_share_sen": 1200},
    ).json()

    # Upload JPEG
    resp = auth_client_a.post(
        f"/api/receipts/{r['id']}/file",
        files={"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["has_file"] is True

    # Download file
    down = auth_client_a.get(f"/api/receipts/{r['id']}/file")
    assert down.status_code == 200
    assert down.headers["content-type"] == "image/jpeg"
    assert down.headers["x-content-type-options"] == "nosniff"
    assert "inline;" in down.headers["content-disposition"]


def test_upload_valid_png(auth_client_a, sample_png_bytes):
    r = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "PNG Shop", "receipt_date": "2026-10-01", "my_share_sen": 1500},
    ).json()

    resp = auth_client_a.post(
        f"/api/receipts/{r['id']}/file",
        files={"file": ("bill.png", sample_png_bytes, "image/png")},
    )
    assert resp.status_code == 200
    assert resp.json()["has_file"] is True


def test_upload_valid_pdf(auth_client_a, sample_pdf_bytes):
    r = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "PDF Invoice", "receipt_date": "2026-10-01", "my_share_sen": 5000},
    ).json()

    resp = auth_client_a.post(
        f"/api/receipts/{r['id']}/file",
        files={"file": ("invoice.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 200
    assert resp.json()["has_file"] is True

    down = auth_client_a.get(f"/api/receipts/{r['id']}/file")
    assert down.status_code == 200
    assert down.headers["content-type"] == "application/pdf"


def test_upload_wrong_type_rejected(auth_client_a):
    r = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "Bad File", "receipt_date": "2026-10-01", "my_share_sen": 1000},
    ).json()

    # Plain text file disguised as text/plain
    resp = auth_client_a.post(
        f"/api/receipts/{r['id']}/file",
        files={"file": ("notes.txt", b"Hello plain text", "text/plain")},
    )
    assert resp.status_code == 400
    assert "Allowed file formats" in resp.json()["detail"]


def test_upload_fake_extension_rejected(auth_client_a):
    r = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "Malicious Fake Ext", "receipt_date": "2026-10-01", "my_share_sen": 1000},
    ).json()

    # An executable or html script masquerading as .jpg
    fake_payload = b"<html><script>alert(1)</script></html>"
    resp = auth_client_a.post(
        f"/api/receipts/{r['id']}/file",
        files={"file": ("malicious.jpg", fake_payload, "image/jpeg")},
    )
    assert resp.status_code == 400
    assert "Allowed file formats" in resp.json()["detail"]


def test_upload_oversized_file_rejected(auth_client_a):
    r = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "Oversized Test", "receipt_date": "2026-10-01", "my_share_sen": 1000},
    ).json()

    # Generate oversized dummy bytes exceeding MAX_UPLOAD_MB
    oversized_bytes = b"%PDF" + (b"0" * (settings.MAX_UPLOAD_MB * 1024 * 1024 + 1024))
    resp = auth_client_a.post(
        f"/api/receipts/{r['id']}/file",
        files={"file": ("huge.pdf", oversized_bytes, "application/pdf")},
    )
    assert resp.status_code == 413
    assert "exceeds maximum size limit" in resp.json()["detail"]


def test_delete_file_attachment(auth_client_a, sample_image_bytes):
    r = auth_client_a.post(
        "/api/receipts",
        json={"merchant": "Delete Attachment Test", "receipt_date": "2026-10-01", "my_share_sen": 1000},
    ).json()

    # Upload
    auth_client_a.post(
        f"/api/receipts/{r['id']}/file",
        files={"file": ("receipt.jpg", sample_image_bytes, "image/jpeg")},
    )

    # Delete attachment
    del_resp = auth_client_a.delete(f"/api/receipts/{r['id']}/file")
    assert del_resp.status_code == 200
    assert del_resp.json()["has_file"] is False

    # Download now returns 404
    down = auth_client_a.get(f"/api/receipts/{r['id']}/file")
    assert down.status_code == 404
