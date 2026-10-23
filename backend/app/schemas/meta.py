# Purpose: Pydantic schemas for server time synchronization and health checks.
# Security: Exposes only non-sensitive runtime metadata and synchronization timestamps.

from pydantic import BaseModel


class TimeResponse(BaseModel):
    current_time: str
    timezone: str
    unix_timestamp: int


class HealthResponse(BaseModel):
    status: str
    version: str
