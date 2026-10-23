# Purpose: HTTP middleware injecting production-grade security headers on all responses.
# Security: Enforces strict CSP, prevents MIME-sniffing, clickjacking, and referrer leakage.

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Content-Security-Policy: restrict source origins for scripts, styles, frames, images
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data: blob:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'self' blob:; "
            "base-uri 'self';",
        )
        # Prevent MIME type sniffing
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Prevent clickjacking
        response.headers.setdefault("X-Frame-Options", "DENY")
        # Referrer policy
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # Permissions policy
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )

        return response
