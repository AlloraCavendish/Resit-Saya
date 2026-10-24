# Purpose: HTTP middleware injecting production-grade security headers on all responses.
# Security: Enforces strict CSP, HSTS, COOP, nosniff, clickjacking prevention, and feature restrictions.

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Strict-Transport-Security: Enforce HTTPS for 1 year including subdomains
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )

        # Content-Security-Policy: Restrict resource origins and execution context
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data: blob:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self';",
        )

        # Prevent MIME type sniffing
        response.headers.setdefault("X-Content-Type-Options", "nosniff")

        # Prevent clickjacking / frame embedding
        response.headers.setdefault("X-Frame-Options", "DENY")

        # Referrer policy: send origin only on cross-origin requests
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")

        # Permissions policy: disable unused hardware APIs
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )

        # Cross-Origin-Opener-Policy: isolate browsing context
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        # Prevent cross-domain flash/pdf policy loading
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        return response
