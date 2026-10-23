# Purpose: Pydantic schemas for admin aggregate dashboards, user management, and audit logs.
# Security: Prevents exposure of user receipts, personal finances, or sensitive tokens to administrators.

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminUserSummary(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    receipt_count: int
    storage_bytes: int


class DailyReceiptCount(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class AuditLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    event: str
    ip: Optional[str] = None
    detail: str
    created_at: datetime


class LastPurgeJobInfo(BaseModel):
    timestamp: Optional[datetime] = None
    count_purged: int = 0


class AdminDashboardResponse(BaseModel):
    total_users: int
    active_users: int
    disabled_users: int
    total_receipts: int
    trash_receipts: int
    total_storage_bytes: int
    receipts_per_day_30d: list[DailyReceiptCount]
    users_summary: list[AdminUserSummary]
    recent_audit_logs: list[AuditLogItem]
    last_purge_job: Optional[LastPurgeJobInfo] = None
    failed_logins_24h: int
    server_time: str
    server_timezone: str
    app_version: str


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=10, max_length=256)
    role: Literal["user", "admin"] = "user"


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[Literal["user", "admin"]] = None


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=10, max_length=256)
