# CHANGELOG.md - Release Notes for Resit Saya

All notable changes to the Resit Saya application will be documented in this file.

## [1.2.1] - 2026-10-24

### Security
- Production security header hardening addressing Pentest-Tools and RedSentinel vulnerability audits:
  - Enabled HTTP Strict-Transport-Security (`HSTS`) with 1-year duration and `includeSubDomains`.
  - Implemented comprehensive `Content-Security-Policy` (`CSP`) across Nginx and FastAPI responses.
  - Enforced `X-Frame-Options: DENY` (clickjacking defense) and `X-Content-Type-Options: nosniff` (MIME sniffing defense).
  - Enforced `Referrer-Policy: strict-origin-when-cross-origin` in headers and HTML meta tags.
  - Added `Permissions-Policy` disabling unused camera, microphone, geolocation, and payment APIs.
  - Added `Cross-Origin-Opener-Policy: same-origin` to isolate browsing context against XS-Leaks.
  - Suppressed Nginx and backend server version headers (`server_tokens off;`, `proxy_hide_header Server;`).
  - Added `robots.txt` disallowing crawler indexing on administrative/API routes and RFC 9116 `.well-known/security.txt`.

## [1.2.0] - 2026-10-24

### Added
- Dark mode theme switcher with light mode as the default:
  - Custom `useTheme` hook with `localStorage` persistence and cross-tab/cross-component synchronization.
  - Quick toggle button in the top navigation bar (`Navbar`) and login screen.
  - Dedicated theme customization card in Account Settings (`SettingsPage`).
  - Comprehensive dark token overrides in `tokens.css` and `base.css` covering surfaces, text contrast, borders, and input controls.
  - Zero-flicker theme hydration on application startup in `main.jsx`.

## [1.1.0] - 2026-10-24

### Added
- Production Docker containerization suite:
  - Backend `Dockerfile` and automated migration `entrypoint.sh`.
  - Multi-stage frontend `Dockerfile` with optimized Nginx reverse proxy.
  - Production `docker-compose.yml` with persistent named volumes for database and uploaded receipts.
  - Root `.env.example` and `.dockerignore`.

## [1.0.2] - 2026-10-24

### Added
- Created `VERSIONLOG.md` documenting the v1.0.0 prototype milestone, architectural overview, and comprehensive feature inventory.

## [1.0.1] - 2026-10-17

### Added
- Standard `--help`, `-h`, and `help` flag support for `python -m app.cli` entrypoint with exit code 0.
- End-to-end verification of all backend test suites (25/25 passing) and clean Vite production frontend build.
- Seeding and verification of sample demo receipts and administrative accounts in local SQLite database.

## [1.0.0] - 2026-10-06

### Added
- **Initial release of Resit Saya**:
  - Full multi-user expense tracker with focus on manual personal shares for split receipts.
  - Backend built with FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, and Argon2-cffi.
  - Secure server-side sessions stored as SHA-256 hashes with HttpOnly SameSite=Lax cookies.
  - Strict user data isolation across receipts, categories, and file attachments.
  - Receipt lifecycle: create, read, update, soft delete, trash management, restore, and permanent deletion.
  - Automated 30-day retention purge job using APScheduler and manual CLI purge command.
  - File attachment system supporting JPEG, PNG, WebP, and PDF with deep content inspection (Pillow and PDF magic bytes).
  - Monthly expense reports with category breakdowns, percentages, and previous month comparison.
  - Admin aggregate dashboard with system metrics, active user tracking, storage metrics, and 30-day receipt trends.
  - Admin user management (creation with temporary passwords, enable/disable, role modification, password reset).
  - CLI management tool (`python -m app.cli` with `create-admin`, `seed-demo`, and `purge-deleted`).
  - Frontend SPA built with React and Vite using zero external UI libraries and 100% separated CSS.
  - CSS design tokens (`tokens.css`) and responsive layouts across phone (<600px), tablet (600-1023px), and desktop (1024px+).
  - Live server clock synchronized with `APP_TIMEZONE` (default `Asia/Kuala_Lumpur`).
  - Comprehensive Pytest test suite covering authentication, multi-user isolation, admin security, calculations, uploads, and purge lifecycle.
