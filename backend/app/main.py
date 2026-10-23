# Purpose: FastAPI application entrypoint, middleware configuration, and lifecycle management.
# Security: Enforces production security checks, CSP headers, restrictive CORS, and sanitizes unhandled exceptions.

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.jobs.purge_deleted import run_scheduled_purge
from app.routers import admin, auth, categories, meta, receipts, reports
from app.security.headers import SecurityHeadersMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resitsaya.main")

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    logger.info("Initializing Resit Saya backend...")
    settings.validate_production_security()

    # Ensure uploads root directory exists
    settings.upload_path.mkdir(parents=True, exist_ok=True)

    # Initialize daily retention purge job
    scheduler.add_job(
        run_scheduled_purge,
        trigger="cron",
        hour=3,
        minute=0,
        id="retention_purge",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Background retention purge scheduler started.")

    yield

    # Shutdown
    logger.info("Shutting down Resit Saya backend scheduler...")
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Resit Saya API",
    description="Privacy-first personal expense tracker backend",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# 1. Custom Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS Middleware (Dev origins permitted with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Global Exception Handler (prevents leaking internal stack traces)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# Mount API routers
app.include_router(auth.router, prefix="/api")
app.include_router(receipts.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(meta.router, prefix="/api")
