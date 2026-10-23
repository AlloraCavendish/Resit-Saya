<!-- Purpose: Version log and release milestone tracker for Resit Saya. -->
<!-- Security: Contains no sensitive secrets or production credentials. -->

# VERSIONLOG.md — Resit Saya Release History

This document tracks milestones, semantic versions, release stages, and functional change logs for **Resit Saya**.

---

## [v1.0.0] — 2026-10-24 (Prototype / MVP)

> **Stage / Status**: **Prototype**  
> **Milestone**: Initial working prototype of the multi-user expense tracker designed for local testing and personal expense tracking with manual bill-split shares.

### 📌 Summary of Changes & Features

#### 1. Core Architecture & Stack
* **Backend**: FastAPI 0.115+ framework with SQLAlchemy 2.0 ORM, Pydantic v2 schemas, and Alembic database migration management.
* **Database**: Portable SQLAlchemy SQLite database (`resitsaya.db`) with forward-compatibility for PostgreSQL.
* **Frontend**: React 18 Single Page Application built with Vite 5 and vanilla CSS (no UI libraries, no CSS-in-JS, zero Tailwind dependencies).
* **Strict Separation of Concerns**: 100% decoupling of component markup (`.jsx`) from dedicated stylesheet modules (`.css`), supported by global design tokens (`tokens.css`).

#### 2. Authentication & Session Management
* **Account Provisioning**: Admin-only user creation (no open public registration) with forced temporary password reset on initial login (`must_change_password`).
* **Argon2id Hashing**: Cryptographic password hashing meeting OWASP standards (minimum 10 characters).
* **Stateful Sessions**: 256-bit entropy session tokens stored as SHA-256 hashes in the database; transmitted via `HttpOnly`, `SameSite=Lax` cookies (`resitsaya_session`).
* **Session Lifecycle**: Password changes automatically invalidate all other user sessions; logout cleanly removes session database records and expires browser cookies.
* **Brute-Force Protection**: Server-side rate limiting restricting failed login attempts (5 failures per 15 minutes per username + IP).

#### 3. Expense & Split-Bill Receipts
* **Manual Share Calculation**: Dedicated tracking of personal shares (`my_share_sen`) separate from total merchant bill amounts (`receipt_total_sen`).
* **Integer Sen Currency**: All financial figures stored and transmitted as exact integer sen (e.g. RM 12.50 = 1250 sen) to eliminate floating-point rounding errors.
* **Receipt Lifecycle**: Full CRUD workflows with search (merchant/notes), date range filtering, category filtering, and pagination.
* **Soft Deletion & Trash**: Safe deletion setting `deleted_at`; dedicated Trash interface with days-remaining countdown, receipt restoration, and manual permanent purge.
* **File Attachments**: Optional attachment of receipts (JPEG, PNG, WebP, PDF) with deep binary content inspection (Pillow and `%PDF` magic bytes).
* **Automatic Retention Purge**: Integrated APScheduler background job purging soft-deleted receipts and disk files older than 30 days (`RETENTION_DAYS`).

#### 4. Reports & Live Time Synchronization
* **Monthly Spending Reports**: `/api/reports/monthly` returning total expenses, receipt count, per-category breakdown, percentage share, and month-over-month comparisons.
* **Dashboard View**: Overview displaying current month total, top spending categories using CSS progress bars, 5 most recent receipts, and a live synchronized clock.
* **Timezone Consistency**: Centralized business date calculations using `APP_TIMEZONE` (`Asia/Kuala_Lumpur`), while database timestamps are stored in UTC.

#### 5. User & Category Management
* **Default Categories**: Automated seeding of 10 localized categories (`Food & Drinks`, `Groceries`, `Transport`, `Shopping`, `Bills & Utilities`, `Health`, `Entertainment`, `Education`, `Travel`, `Other`).
* **Custom Categories**: Users can create, rename, and delete custom categories.
* **User Isolation**: Strict database query scoping by `user_id` across all receipt, category, and file endpoints.

#### 6. Admin Panel (Isolated Aggregates)
* **Dedicated Navigation**: Restricted tab visible only to users with role `admin` (enforced independently on every backend admin endpoint).
* **Privacy-First Metrics**: Aggregated system metrics only (user counts, active vs disabled, upload storage used, 30-day receipt volume trends, recent audit logs).
* **Admin Invariants**: Admins are strictly prohibited from viewing or downloading personal receipts, categories, or attachments of other users.
* **User Governance**: Create accounts, enable/disable users, assign roles, and trigger password resets.

#### 7. Administrative CLI
* `python -m app.cli create-admin`: Interactive CLI tool to bootstrap initial administrator accounts.
* `python -m app.cli seed-demo`: Seeds a `demo` user account preloaded with ~35 realistic Malaysian split-bill receipts across 3 months.
* `python -m app.cli purge-deleted`: On-demand manual execution of the soft-deleted retention purge routine.

#### 8. Verification & Quality Assurance
* **Automated Tests**: 25/25 passing Pytest unit/integration tests covering auth, rate-limiting, user isolation, receipt math, file security, and purge mechanics.
* **Linter & Security**: 100% clean Ruff linter checks and 0 known vulnerabilities verified via `pip-audit`.
* **Responsive Layouts**: Mobile-first responsive UI supporting mobile viewports (<600px with bottom navigation), tablets (600–1023px), and desktops (>=1024px with sidebar navigation).

#### 9. Production Self-Hosting (Hyper-V & Tailscale)
* **Host Platform**: Dedicated Hyper-V virtual machine (`ResitSaya-Prod`, hostname `resitsaya-prod`) running Ubuntu Server 24.04 LTS.
* **Orchestration**: Docker Compose managing the FastAPI backend and Nginx frontend with persistent named volumes.
* **Network Mesh**: Private, encrypted Tailscale network integration enabling secure remote access from mobile and desktop without exposing public ports.
