# Implementation Plan: Resit Saya

## Project Overview
"Resit Saya" is a privacy-first, multi-user receipt and personal expense tracking web application designed for tracking personal shares of expenses (including split bills) with optional receipt image/PDF attachments, monthly reporting, category management, soft delete retention, and administrative aggregate monitoring.

## System Architecture

### Backend (FastAPI + SQLAlchemy 2.0 + SQLite/PostgreSQL)
- **Config & Settings (`app/config.py`)**: Centralized Pydantic v2 settings loading from `.env` with validation for `SECRET_KEY`, `DATABASE_URL`, `UPLOAD_DIR`, `MAX_UPLOAD_MB`, `APP_TIMEZONE`, `RETENTION_DAYS`, `COOKIE_SECURE`, `SESSION_DAYS`, and `DEV_MODE`.
- **Database Layer (`app/db.py`, `app/models/`)**: Portable SQLAlchemy 2.0 ORM models:
  - `User`: id, username, email, password_hash, role ('admin'/'user'), is_active, must_change_password, last_login_at, created_at.
  - `Session`: id, user_id, token_hash, created_at, expires_at, last_seen_at.
  - `Category`: id, user_id, name (unique constraint per user).
  - `Receipt`: id, user_id, category_id, merchant, receipt_date, my_share_sen, receipt_total_sen, currency, shared_with, notes, file_path, original_filename, created_at, updated_at, deleted_at. Indexes on `(user_id, receipt_date)` and `(user_id, deleted_at)`.
  - `AuditLog`: id, user_id, event, ip, detail, created_at.
- **Alembic Migrations**: Initial migration generating all tables and indexes cleanly.
- **Security & Auth (`app/security/`)**:
  - Argon2id password hashing via `argon2-cffi`.
  - Server-side sessions with crypto-secure random tokens stored as SHA-256 hashes; delivered via HttpOnly, SameSite=Lax cookie (`resitsaya_session`).
  - In-memory rate limiting: 5 failed attempts per 15 minutes per username+IP.
  - Deny-by-default dependencies: `get_current_user`, `require_admin`, `require_active_user`.
  - Strict user-scoping for all receipts, categories, and file downloads.
  - Security headers middleware: Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy.
- **File Storage & Validation (`app/services/file_storage.py`)**:
  - Binary inspection: Pillow for JPEG/PNG/WebP, `%PDF` magic bytes for PDF. Ignore client headers.
  - Storage under `uploads/<user_id>/<uuid>.<ext>` with path traversal guards.
  - File serving with `X-Content-Type-Options: nosniff` and safe `Content-Disposition`.
- **Services & Jobs**:
  - `receipt_service.py`: CRUD, search, filtering, soft-delete, restore, permanent delete.
  - `report_service.py`: Monthly report aggregation, per-category breakdown and percentage, previous month comparison.
  - `admin_service.py`: Aggregate statistics, audit log queries, user management (prevent self-demote/self-disable).
  - `purge.py` & APScheduler job: Daily retention purge for deleted items older than `RETENTION_DAYS`, physical file removal, audit logging.
- **CLI Commands (`app/cli.py`)**:
  - `create-admin`: CLI prompt for creating the first admin account.
  - `seed-demo`: Create demo user with ~30 realistic receipts across 3 months.
  - `purge-deleted`: Manually trigger retention purge.

### Frontend (React + Vite + Plain CSS)
- **Zero UI Libraries, Zero Inline Styles**:
  - Strict separation of styling: every `.jsx` file has a matching `.css` file.
  - Global CSS tokens in `src/styles/tokens.css` (colors, typography, spacing, radius, shadows, responsive breakpoints).
  - Base styles in `src/styles/base.css` and app shell layouts in `src/styles/layout.css`.
- **Responsive System**:
  - Mobile (<600px): single column, bottom tab bar navigation, card-based receipt views, 44px+ touch targets, >=16px form inputs.
  - Tablet (600-1023px): two-column layouts, adaptive navigation, compact tables.
  - Desktop (1024px+): persistent sidebar navigation, full multi-column dashboard, max-width centered container.
  - No horizontal scrolling across 320px to 2560px viewport widths.
- **Pages**:
  - Login & Forced Password Change
  - Dashboard (month total, CSS bars for top categories, 5 recent receipts, live clock)
  - Receipt List (search, date range & category filters, pagination, responsive cards/tables)
  - Add / Edit Receipt (date default today, merchant, category, share RM, total RM, shared with, notes, mobile-friendly camera/gallery upload, preview)
  - Receipt Detail (details, file preview/download, edit, trash)
  - Monthly Report (month picker, prev/next buttons, summary, category breakdown)
  - Trash (retention days remaining, restore, permanent delete)
  - Category Management (list, add, rename, delete)
  - Settings (change own password, invalidates other sessions)
  - Admin Dashboard (aggregates only, charts/bars, user storage, audit logs, purge status)
  - Admin Users (list, create, enable/disable, reset password, role change)

### Testing Strategy
- Pytest suite using isolated temp SQLite database and temporary upload directory:
  - Auth, login rate limiting, session cookies, forced password change.
  - Strict multi-user data isolation (User A cannot access/modify/restore User B's receipts/categories/files).
  - Admin endpoint protection (401 unauthenticated, 403 non-admin, admin cannot view user receipt contents).
  - Receipt CRUD, sen money validation (`my_share_sen > 0`, `receipt_total_sen >= my_share_sen`).
  - Soft-delete, restore, permanent delete, retention purge (backdated deleted_at) with file cleanup and audit event.
  - Monthly report calculations (percentages, previous month diff).
  - Upload security (magic byte detection, oversized files, fake extensions, safe delivery).
  - Audit logs for security events.
- Frontend: Vite build validation (`npm run build`).

## Implementation Steps
1. Initialize project structure and documentation (`AGENTS.md`, `SECURITY.md`, `.gitignore`, `CHANGELOG.md`, `README.md`).
2. Build Python backend (`pyproject.toml`, `.env.example`, Alembic setup, config, models, security, services, routers, jobs, CLI).
3. Implement database migrations and CLI commands.
4. Implement comprehensive backend tests (`tests/`).
5. Set up and implement frontend (`package.json`, `vite.config.js`, styles, api, hooks, utils, components, pages).
6. Run backend test suite, linting, frontend build, and verify responsive behavior.
7. Final review against all specifications.
