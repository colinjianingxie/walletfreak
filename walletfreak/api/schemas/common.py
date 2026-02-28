from ninja import Schema
from typing import Any, Optional


class SuccessResponse(Schema):
    success: bool = True


class ErrorResponse(Schema):
    success: bool = False
    error: str


class PaginatedResponse(Schema):
    items: list[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
