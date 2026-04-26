"""Common response schemas for API."""
from typing import Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response from items."""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: List[str] = []
    correlation_id: str = ""


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str
    data: dict = {}
