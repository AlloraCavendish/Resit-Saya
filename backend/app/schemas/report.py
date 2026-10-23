# Purpose: Pydantic schemas for monthly expense aggregation and reports.
# Security: Exposes statistical aggregate data only; ensures mathematically bounded percentage values.

from typing import Optional

from pydantic import BaseModel


class CategoryBreakdownItem(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    total_sen: int
    percentage: float
    count: int


class MonthlyReportResponse(BaseModel):
    month: str  # YYYY-MM
    total_sen: int
    receipt_count: int
    categories: list[CategoryBreakdownItem]
    previous_month: str
    previous_month_total_sen: int
    diff_sen: int
    diff_percentage: Optional[float] = None
