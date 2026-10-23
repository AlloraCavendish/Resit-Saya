# Purpose: Pydantic schemas for receipt operations and financial validation.
# Security: Validates positive monetary bounds (sen) and strict schema bounds on all inputs.

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReceiptCreate(BaseModel):
    merchant: str = Field(..., min_length=1, max_length=255)
    receipt_date: date
    my_share_sen: int = Field(..., gt=0, description="User share in sen (e.g. 1250 for RM 12.50)")
    receipt_total_sen: Optional[int] = Field(None, gt=0, description="Total bill in sen")
    category_id: Optional[int] = None
    currency: str = Field("MYR", min_length=3, max_length=3)
    shared_with: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode="after")
    def validate_totals(self) -> "ReceiptCreate":
        if self.receipt_total_sen is not None and self.receipt_total_sen < self.my_share_sen:
            raise ValueError("receipt_total_sen must be greater than or equal to my_share_sen")
        return self


class ReceiptUpdate(BaseModel):
    merchant: Optional[str] = Field(None, min_length=1, max_length=255)
    receipt_date: Optional[date] = None
    my_share_sen: Optional[int] = Field(None, gt=0)
    receipt_total_sen: Optional[int] = Field(None, gt=0)
    category_id: Optional[int] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    shared_with: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode="after")
    def validate_update_totals(self) -> "ReceiptUpdate":
        if self.my_share_sen is not None and self.receipt_total_sen is not None:
            if self.receipt_total_sen < self.my_share_sen:
                raise ValueError("receipt_total_sen must be greater than or equal to my_share_sen")
        return self


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    merchant: str
    receipt_date: date
    my_share_sen: int
    receipt_total_sen: Optional[int] = None
    currency: str
    shared_with: Optional[str] = None
    notes: Optional[str] = None
    file_path: Optional[str] = None
    original_filename: Optional[str] = None
    has_file: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class ReceiptListResponse(BaseModel):
    items: list[ReceiptOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class TrashReceiptOut(ReceiptOut):
    days_remaining: int


class TrashListResponse(BaseModel):
    items: list[TrashReceiptOut]
    total: int
