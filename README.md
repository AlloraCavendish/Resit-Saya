📜 [Version Log](VERSIONLOG.md) · [Changelog](CHANGELOG.md) · [Security](SECURITY.md)
# Resit Saya — Privacy-First Personal Expense & Receipt Tracker

<!-- Purpose: Project documentation — setup, features, API reference, and security notes. -->
<!-- Security: No secrets stored here; references .env.example for environment variable patterns. -->
<!-- DOCUMENTATION RULE: Update this file and CHANGELOG.md whenever behaviour, config, endpoints or setup change. -->

**Resit Saya** (Malay for "my receipt") is a self-hosted, multi-user web application for tracking personal expenses with receipt photo attachments. It is designed for Malaysian users who split bills with friends and want to record **their own share** of each receipt.

---

## Features

- **Multi-user authentication** — admin-created accounts with Argon2id password hashing, server-side sessions, and HttpOnly session cookies.
- **Receipt management** — create, edit, soft-delete, restore, and permanently delete receipts with optional JPEG/PNG/WebP/PDF file attachments.
- **Split-bill tracking** — record your share (in sen) separately from the total bill amount, with an optional "shared with" note.
- **Monthly reports** — per-category breakdown with percentages, month-over-month comparison, and month picker navigation.
- **Dashboard** — current month total, top categories with CSS bars, 5 most recent receipts, and a live server-synced clock.
- **Categories** — default categories seeded per user; users can add, rename, and delete their own.
- **Trash & retention** — soft-deleted receipts with a configurable retention period (default 30 days) and automatic daily purge.
- **Admin dashboard** — aggregate system metrics, user management, and audit logs. Admins **cannot** view other users' financial data.
- **Responsive design** — mobile-first with bottom tab nav on phones, collapsible sidebar on tablets, persistent sidebar on desktop.

---

## Project Structure

```
resit-saya/
├── README.md, CHANGELOG.md, VERSIONLOG.md, SECURITY.md, AGENTS.md, PLAN.md, .gitignore
├── backend/
│   ├── pyproject.toml              # Python deps & tool config
│   ├── .env.example                # Environment variable template
│   ├── alembic.ini                 # Alembic migration config
│   ├── alembic/versions/           # Database migration scripts
│   └── app/
│       ├── main.py                 # FastAPI app, lifespan, scheduler, CORS, headers
│       ├── config.py               # All tunable configuration (no magic numbers)
│       ├── db.py                   # SQLAlchemy engine & session
│       ├── cli.py                  # CLI: create-admin, seed-demo, purge-deleted
│       ├── models/                 # SQLAlchemy ORM models
│       ├── schemas/                # Pydantic v2 request/response schemas
│       ├── routers/                # FastAPI route handlers (thin)
│       ├── services/               # Business logic layer
│       ├── security/               # Auth, passwords, sessions, rate limits, headers
│       └── jobs/                   # APScheduler background jobs
├── frontend/
│   ├── package.json                # React + Vite deps
│   ├── vite.config.js              # Dev proxy /api → backend
│   ├── index.html                  # SPA entry
│   └── src/
│       ├── main.jsx                # React DOM mount
│       ├── App.jsx                 # Router, auth guards, app shell
│       ├── styles/                 # tokens.css, base.css, layout.css
│       ├── api/                    # fetch wrapper + per-resource API modules
│       ├── hooks/                  # useAuth, useServerClock
│       ├── components/             # Reusable components (each .jsx + .css)
│       ├── pages/                  # Page components (each .jsx + .css)
│       └── utils/                  # money.js, date.js helpers
└── uploads/                        # Runtime file storage (gitignored)
```

---

## Setup

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm

### Backend

```bash
cd backend

# Create virtual environment and install dependencies
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -e ".[dev]"

# Copy and edit environment variables
cp .env.example .env
# Edit .env as needed (defaults work for local dev with SQLite)

# Run database migrations
alembic upgrade head

# Create the first admin account
python -m app.cli create-admin

# (Optional) Seed demo data — creates a "demo" user with ~35 sample receipts
python -m app.cli seed-demo

# Start the backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server (proxies /api to backend on port 8000)
npm run dev
```

Open **http://localhost:5173** in your browser.

### Production Deployment (Docker Compose)

The easiest way to run Resit Saya on a server or VM:

```bash
# Clone the repository
git clone https://github.com/AlloraCavendish/Resit-Saya.git
cd Resit-Saya

# Copy and configure environment variables
cp .env.example .env
# Edit .env and set a random 32+ character SECRET_KEY

# Build and start containers
docker compose up -d --build

# Create initial admin account
docker compose exec backend python -m app.cli create-admin

# (Optional) Seed demo receipts
docker compose exec backend python -m app.cli seed-demo
```

Access the application on port `80` (e.g. `http://<server-ip>`).

---

## Environment Variables

All config is in `backend/.env`. See `backend/.env.example` for the full list.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///resitsaya.db` | SQLAlchemy database URL. Switch to PostgreSQL for production. |
| `SECRET_KEY` | *(random)* | Session token signing key. |
| `APP_TIMEZONE` | `Asia/Kuala_Lumpur` | Timezone for business date logic and display. |
| `SESSION_LIFETIME_HOURS` | `72` | Session cookie lifetime in hours. |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum file upload size in megabytes. |
| `RETENTION_DAYS` | `30` | Days before soft-deleted receipts are permanently purged. |
| `PURGE_HOUR_UTC` | `2` | Hour (UTC) when the daily purge job runs. |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed CORS origins. |
| `UPLOAD_DIR` | `../uploads` | Path to the uploads directory (relative to backend/). |
| `APP_VERSION` | `1.0.0` | Version string shown in admin dashboard. |

---

## How to Run

1. **Start the backend** in one terminal:
   ```bash
   cd backend && .\.venv\Scripts\activate && uvicorn app.main:app --reload
   ```

2. **Start the frontend** in another terminal:
   ```bash
   cd frontend && npm run dev
   ```

3. Open **http://localhost:5173**

### Running Tests

```bash
cd backend
.\.venv\Scripts\activate
pytest -v
```

### Linting

```bash
cd backend
.\.venv\Scripts\activate
ruff check .
```

### Security Audit

```bash
cd backend
.\.venv\Scripts\activate
pip-audit
```

---

## API Summary

All endpoints are under `/api` and return JSON (except file downloads).

### Authentication
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Log in (username + password) |
| `POST` | `/api/auth/logout` | Log out (invalidate session) |
| `GET` | `/api/auth/me` | Get current user info |
| `POST` | `/api/auth/change-password` | Change own password |

### Receipts
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/receipts` | List receipts (search, filter, paginate) |
| `POST` | `/api/receipts` | Create receipt |
| `GET` | `/api/receipts/{id}` | Get receipt detail |
| `PUT` | `/api/receipts/{id}` | Update receipt |
| `DELETE` | `/api/receipts/{id}` | Soft-delete receipt |
| `GET` | `/api/receipts/trash` | List trashed receipts |
| `POST` | `/api/receipts/{id}/restore` | Restore from trash |
| `DELETE` | `/api/receipts/{id}/permanent` | Permanently delete |
| `POST` | `/api/receipts/{id}/file` | Upload/replace file attachment |
| `GET` | `/api/receipts/{id}/file` | Download file attachment |
| `DELETE` | `/api/receipts/{id}/file` | Remove file attachment |

### Categories
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/categories` | List user's categories |
| `POST` | `/api/categories` | Create category |
| `PUT` | `/api/categories/{id}` | Rename category |
| `DELETE` | `/api/categories/{id}` | Delete category |

### Reports
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/reports/monthly?month=YYYY-MM` | Monthly report with breakdown |

### Admin (role=admin only)
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/admin/dashboard` | Aggregate system metrics |
| `GET` | `/api/admin/audit-log` | Recent audit events |
| `GET` | `/api/admin/users` | List all users |
| `POST` | `/api/admin/users` | Create user |
| `PATCH` | `/api/admin/users/{id}` | Update user (active, role) |
| `POST` | `/api/admin/users/{id}/reset-password` | Reset user password |

### System
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/time` | Server time and timezone |
| `GET` | `/api/health` | Health check |

---

## Money Format

- All monetary values are stored and transmitted as **integer sen** (1 RM = 100 sen).
- The API sends and receives `my_share_sen` and `receipt_total_sen` as integers.
- The frontend converts to/from RM with 2 decimal places for display (e.g., `1250` → `RM 12.50`).
- Validation: `my_share_sen > 0`; if `receipt_total_sen` is provided, it must be `≥ my_share_sen`.

---

## Security Notes

See [SECURITY.md](SECURITY.md) for the full security model. Key points:

- **Argon2id** password hashing with minimum 10-character passwords.
- **Server-side sessions** stored as SHA-256 hashes; HttpOnly cookies with SameSite=Lax.
- **Rate limiting** on login: 5 failures per 15 minutes per username+IP.
- **File validation** inspects binary content (Pillow for images, magic bytes for PDF). Never trusts Content-Type headers.
- **User isolation**: every database query filters by authenticated `user_id`. Admins see only aggregates.
- **SQL injection prevention**: SQLAlchemy ORM only, no raw string concatenation.
- **Security headers**: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy on all responses.
- **Audit logging**: login success/failure, logout, password changes, user management, and purge events.

---

## Assumptions

1. **SQLite for development** — the app uses portable SQLAlchemy features so switching `DATABASE_URL` to PostgreSQL requires no code changes.
2. **No public registration** — only admins create user accounts.
3. **Single currency** — defaults to MYR. Multi-currency is out of scope.
4. **File types** — only JPEG, PNG, WebP, and PDF are accepted as receipt attachments.
5. **Timezone** — business logic (e.g., "this month") uses `APP_TIMEZONE` (default `Asia/Kuala_Lumpur`). Timestamps stored in UTC.
6. **Docker containerization** — Docker Compose orchestrates the FastAPI backend and Nginx frontend in production, with persistent volumes for data and uploads.
7. **No OCR** — receipt data is entered manually; no automatic text extraction from images.
8. **Default categories** — 10 categories are seeded per new user: Food & Drinks, Groceries, Transport, Shopping, Bills & Utilities, Health, Entertainment, Education, Travel, Other.
9. **Demo user credentials** — `demo` / `demopassword123` (created by `seed-demo` CLI command).
10. **Admin user** — created interactively via `python -m app.cli create-admin`.
11. **Retention period** — soft-deleted receipts are permanently purged after 30 days (configurable via `RETENTION_DAYS`).
12. **Session lifetime** — 72 hours by default (configurable via `SESSION_LIFETIME_HOURS`).
13. **Upload size limit** — 10 MB by default (configurable via `MAX_UPLOAD_SIZE_MB`).
14. **No charts library** — all visualizations use CSS-only bars and progress indicators.
15. **Responsive breakpoints** — phone < 600px, tablet 600–1023px, desktop ≥ 1024px.
16. **Self-hosted production environment** — runs on Hyper-V Ubuntu Server (`ResitSaya-Prod`, hostname `resitsaya-prod`) securely accessible via Tailscale mesh VPN.
