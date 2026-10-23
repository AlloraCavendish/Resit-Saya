# Purpose: Router providing monthly aggregation and financial category reporting.
# Security: Enforces user isolation; prevents calculation contamination from soft-deleted entries.

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user import User
from app.schemas.report import MonthlyReportResponse
from app.security.deps import require_normal_authenticated_user
from app.services.report_service import get_monthly_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/monthly", response_model=MonthlyReportResponse)
def get_user_monthly_report(
    month: Optional[str] = Query(None, description="Month in 'YYYY-MM' format"),
    user: User = Depends(require_normal_authenticated_user),
    db: Session = Depends(get_db),
):
    if not month:
        # Default to current month in application timezone
        tz = ZoneInfo(settings.APP_TIMEZONE)
        month = datetime.now(tz).strftime("%Y-%m")

    return get_monthly_report(db=db, user_id=user.id, month_str=month)
