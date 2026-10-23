# SECURITY.md - Security Model and Threat Defenses for Resit Saya

This document describes the threat model, security controls, and production deployment checklist for **Resit Saya**.

---

## 1. Threat Model

Resit Saya is designed to store private financial and personal expense data, including receipts that may reveal personal shopping habits, medical visits, dining locations, and friend names (bill splitting). The threats addressed include:

| Threat | Risk Level | Mitigation in Resit Saya |
|---|---|---|
| Unauthorized Public Registration | High | Public registration is disabled. Only authorized administrators can create new user accounts. |
| Cross-Tenant Data Access (IDOR) | Critical | Every database query for receipts, categories, and files strictly scopes by the authenticated user's ID. Requests for another user's resources return generic `404 Not Found`. |
| Credential Stuffing & Brute Force | High | Argon2id password hashing, minimum 10-character password policy, rate limiting (5 failed attempts per 15 min per username+IP), and generic authentication failure messages. |
| Session Hijacking & Token Theft | High | Crypto-random 32-byte tokens stored only as SHA-256 hashes in database. Sessions delivered exclusively via `HttpOnly`, `SameSite=Lax` cookies; no token storage in browser `localStorage`. |
| Malicious File Uploads & RCE | Critical | Strict binary verification using Pillow (images) and `%PDF` magic bytes (PDFs). Disregards client headers and extensions. Stored outside web server document roots under random UUID filenames. Served with `X-Content-Type-Options: nosniff`. |
| Cross-Site Scripting (XSS) | High | Strict Content-Security-Policy header, automatic React JSX text escaping, zero `dangerouslySetInnerHTML`, zero `eval()`. |
| SQL Injection | Critical | Portable SQLAlchemy ORM queries exclusively. Zero raw SQL string interpolation. |
| Information Disclosure via Errors | Medium | Generic user-facing error messages without stack traces, database schemas, or filesystem paths. |
| Administrative Overreach | High | Admin dashboard displays aggregate counts and storage usage only. Administrators have no access to view other users' receipts, categories, or file attachments. |

---

## 2. Implemented Security Controls

### Authentication & Passwords
- **Argon2id Hashing**: Uses the modern Argon2 password hashing standard via `argon2-cffi`.
- **Forced Password Change**: Newly created accounts have `must_change_password=True` and cannot access application features until their temporary password is changed.
- **Session Revocation**: Password changes invalidate all other active sessions for that user.

### Authorization & Scope Isolation
- **Role-Based Access Control**: Server-side verification on all endpoints (`require_admin`, `require_active_user`).
- **Self-Preservation Protection**: Administrators are blocked from demoting or disabling their own account.
- **Data Isolation**: All resource reads and writes enforce `WHERE user_id = current_user.id`.

### Audit Logging
- Security events (`login_success`, `login_failed`, `logout`, `password_changed`, `user_created`, `user_disabled`, `user_enabled`, `user_role_changed`, `password_reset`, `receipt_purged`, `purge_job_run`) are immutably logged with timestamp, user ID, IP address, and high-level details.
- Audit logs NEVER record passwords, session tokens, or sensitive receipt contents.

### File Handling
- File uploads are validated by content inspection.
- Files are saved as `uploads/<user_id>/<uuid>.<ext>` using sanitized paths.
- Paths are validated against directory traversal attacks before filesystem operations.
- Soft-deleted receipts are retained for `RETENTION_DAYS` (default 30 days) and then permanently purged along with their files from disk.

### HTTP Security Headers
All backend responses include the following headers:
- `Content-Security-Policy`: Restricts script and resource loading.
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
- `X-Frame-Options: DENY`: Prevents clickjacking.
- `Referrer-Policy: strict-origin-when-cross-origin`: Minimizes referrer leakage.
- `Permissions-Policy`: Restricts camera, microphone, and geolocation access unless explicitly needed.

---

## 3. Pre-Deployment Security Checklist

Before exposing Resit Saya on any production server, network, or VM:

- [ ] **HTTPS / TLS**: Terminate HTTPS with a valid TLS certificate (e.g. Let's Encrypt or Tailscale HTTPS) using a reverse proxy (Caddy, Nginx).
- [ ] **Cookie Security**: Set `COOKIE_SECURE=true` in the environment so session cookies are only transmitted over HTTPS.
- [ ] **Strong Secret Key**: Generate a 32+ byte cryptographically secure key:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Set `SECRET_KEY` in `.env`.
- [ ] **Production Mode**: Ensure `DEV_MODE=false`. Resit Saya will refuse to start if `SECRET_KEY` is missing or uses the default placeholder.
- [ ] **Database Hardening**: If using PostgreSQL, ensure dedicated credentials with least-privilege access and SSL mode enabled.
- [ ] **Uploads Directory Permissions**: Ensure the `UPLOAD_DIR` folder has restricted filesystem permissions (`chmod 700`).
- [ ] **Network & Firewall**: Bind FastAPI to `127.0.0.1` or the internal VPN interface (e.g. Tailscale), not `0.0.0.0`.
- [ ] **Dependency Auditing**:
  - Run backend audit: `pip-audit`
  - Run frontend audit: `npm audit`
- [ ] **Backups**: Implement automated encrypted backups for the database and upload directory.
