from __future__ import annotations

from datetime import datetime, date
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


def _validate_due_date(v: Optional[date]) -> Optional[date]:
    if v is not None and v < date.today():
        raise ValueError("due_date cannot be in the past")
    return v


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Literal["todo", "in_progress", "done"] = "todo"
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: Optional[date] = None

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: Optional[date]) -> Optional[date]:
        return _validate_due_date(v)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[Literal["todo", "in_progress", "done"]] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    due_date: Optional[date] = None

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: Optional[date]) -> Optional[date]:
        return _validate_due_date(v)


class TaskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
