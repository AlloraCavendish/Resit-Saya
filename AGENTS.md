# AGENTS.md - Developer & AI Agent Guidelines for Resit Saya

This document sets the mandatory coding rules and engineering standards for any AI agent or human developer contributing to **Resit Saya**.

---

## 1. Code Organisation & Separation of Concerns

### Styling Separation Rule
- **STYLING IS STRICTLY SEPARATE FROM LOGIC.**
- Every React page and component must have its own `.jsx` file (structure and logic only) and a matching `.css` file (all styling).
  - Example: `ReceiptList.jsx` and `ReceiptList.css`.
- **No inline styles**: Never use the `style={{ ... }}` attribute in JSX except for dynamically calculated CSS custom properties if strictly necessary.
- **No CSS-in-JS, no Tailwind**: Plain modular CSS only.
- Global styling lives in `frontend/src/styles/`:
  - `tokens.css`: Contains ALL CSS custom variables (colors, typography, spacing, border radii, shadows, breakpoints). Modifying the app's visual identity should only require editing this file.
  - `base.css`: CSS reset, standard typography, and base elements.
  - `layout.css`: App shell, navigation grids, responsive containers, and shared utility layout classes.

### Backend Structure
- All tunable configuration parameters must live in `backend/app/config.py`. Never hardcode magic numbers (e.g. timeouts, retention days, upload size limits) in application code.
- Routers must remain thin: handle request validation, dependency injection, and HTTP responses only.
- Place all business logic, data mutations, and multi-step operations in `backend/app/services/`.

---

## 2. File Header Comments & Security Invariants

Every single source file (Python, JSX, CSS, SQL, shell scripts) must start with:
1. A short header comment explaining the purpose of the file.
2. A `Security:` comment line clearly defining what security controls the file enforces, or invariants it must never violate.

Example:
```python
# Purpose: Service for receipt lifecycle management and isolation.
# Security: Enforces user_id filtering on all database queries; prevents cross-user receipt access.
```

```javascript
// Purpose: Receipt form component for creating and editing receipts.
// Security: Sanitizes user inputs, relies on server validation, handles safe file attachments.
```

---

## 3. Responsive Design Rules

- **Mobile-first approach**: Base CSS styles target mobile devices; media queries enhance the UI for larger screens.
- **Breakpoints** (documented in `tokens.css`):
  - Phone: `< 600px`
  - Tablet: `600px - 1023px`
  - Desktop: `>= 1024px`
- **Phone UI Requirements**:
  - Single-column layout.
  - Bottom tab navigation bar.
  - Receipts displayed as cards rather than wide data tables.
  - Full-width form fields.
  - Interactive touch targets at least 44px by 44px.
  - Form input font sizes at least 16px to prevent iOS auto-zoom.
- **Tablet UI Requirements**:
  - Two-column layouts where beneficial.
  - Collapsible or adaptive side navigation.
  - Compact table layouts permitted for data lists.
- **Desktop UI Requirements**:
  - Persistent sidebar navigation.
  - Full data tables with sorting/filtering controls.
  - Multi-column dashboards.
  - Content container capped at a sensible maximum width (e.g. 1280px-1440px) and horizontally centered.
- **Strict Viewport Rule**: No horizontal scrolling at any viewport width from `320px` to `2560px`. Always include `<meta name="viewport" content="width=device-width, initial-scale=1.0">`.

---

## 4. Security Rules & Threat Defenses

- **Authentication & Sessions**:
  - Argon2id password hashing with minimum length of 10 characters.
  - Server-side sessions with crypto-secure random tokens stored as SHA-256 hashes in database.
  - HttpOnly cookies (`resitsaya_session`) with `SameSite=Lax` and configurable `Secure` flag.
  - Rate limiting on login attempts (5 failures per 15 minutes per username + IP).
  - Passwords, tokens, and sensitive keys must never be logged or returned in API responses.
- **Strict Authorization & User Isolation**:
  - Deny by default. Every endpoint requires explicit authentication and authorization dependencies.
  - Data isolation: Every database query for receipts, categories, and files must filter by the authenticated `user_id`. Attempting to access another user's item must return `404 Not Found`.
  - Admin endpoints must verify the `admin` role server-side.
  - Admins must NOT be able to view or download user receipts, categories, or files; the admin dashboard displays aggregate metrics only.
- **File Upload Security**:
  - Allowed types: JPEG, PNG, WebP, PDF.
  - File validation must inspect binary content (Pillow for images, `%PDF` magic bytes for PDF). Never trust client-supplied `Content-Type` headers or file extensions.
  - Stored files must be saved outside web roots at `uploads/<user_id>/<uuid>.<ext>`.
  - Downloads must be gated by authentication, verify ownership, guard against path traversal, and serve with `X-Content-Type-Options: nosniff`.
- **Injection & XSS Prevention**:
  - Use SQLAlchemy ORM exclusively; never concatenate SQL strings.
  - In React, never use `dangerouslySetInnerHTML` or `eval()`.
  - Set security headers on all responses (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy).

---

## 5. Documentation Rule (MANDATORY)

Whenever behavior, configuration, endpoints, dependencies, or setup steps change:
1. Update `README.md` immediately with the updated instructions, configuration options, and API summary.
2. Add an entry to `CHANGELOG.md` in the same commit / change.
3. Keep the "Assumptions" section in `README.md` up-to-date whenever any implementation decision is made.
