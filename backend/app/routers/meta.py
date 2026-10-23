# Purpose: Router for public health probes and server timezone synchronization.
# Security: Exposes non-sensitive timing and health diagnostics; no authentication required.

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter

from app.config import settings
from app.schemas.meta import HealthResponse, TimeResponse

router = APIRouter(tags=["meta"])


@router.get("/time", response_model=TimeResponse)
def get_server_time():
    """Return the current server time formatted in the application business timezone."""
    tz = ZoneInfo(settings.APP_TIMEZONE)
    local_now = datetime.now(tz)
    return TimeResponse(
        current_time=local_now.isoformat(),
        timezone=settings.APP_TIMEZONE,
        unix_timestamp=int(time.time()),
    )


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Return service health status and current release version."""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
    )
