# Purpose: Pydantic schemas for category management and display.
# Security: Enforces string sanitization and character length restrictions.

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class CategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    receipt_count: Optional[int] = 0
