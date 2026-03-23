from __future__ import annotations

from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int


class DataResponse(BaseModel, Generic[T]):
    data: T
    message: str = "success"


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta
    message: str = "success"
