# Purpose: Router for administrative aggregate dashboard, system audit logs, and user management.
# Security: Server-side enforcement of admin role on all endpoints; prevents self-demotion and cross-user data leakage.

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminDashboardResponse,
    AdminResetPasswordRequest,
    AdminUserCreate,
    AdminUserUpdate,
    AuditLogItem,
)
from app.schemas.auth import UserOut
from app.security.deps import get_client_ip, require_admin
from app.services.admin_service import (
    admin_create_user,
    admin_reset_password,
    admin_update_user,
    get_admin_dashboard,
    list_audit_logs,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_dashboard(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return get_admin_dashboard(db=db)


@router.get("/audit-log", response_model=list[AuditLogItem])
def get_audit_logs(
    event: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return list_audit_logs(db=db, event_filter=event, limit=limit)


@router.get("/users", response_model=list[UserOut])
def get_users_list(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserOut.model_validate(u) for u in users]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_new_user(
    payload: AdminUserCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    new_user = admin_create_user(db=db, data=payload, admin_ip=ip)
    return UserOut.model_validate(new_user)


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user_status_or_role(
    user_id: int,
    payload: AdminUserUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    updated = admin_update_user(
        db=db,
        admin_user=admin,
        target_user_id=user_id,
        is_active=payload.is_active,
        role=payload.role,
        admin_ip=ip,
    )
    return UserOut.model_validate(updated)


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: AdminResetPasswordRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    admin_reset_password(
        db=db,
        admin_user=admin,
        target_user_id=user_id,
        new_password=payload.new_password,
        admin_ip=ip,
    )
    return {"message": "User password reset successfully. User must change password upon next login."}
