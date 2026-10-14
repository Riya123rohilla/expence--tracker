"""Pydantic data models and schemas for request validation and response formatting."""

from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from app.config import VALID_CATEGORIES


class ExpenseBase(BaseModel):
    """Base schema containing common expense attributes."""
    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Short title or name of the expense (e.g., Grocery Shopping).",
        examples=["Grocery Shopping"],
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Expense amount in currency units. Must be strictly positive (> 0).",
        examples=[45.50],
    )
    category: str = Field(
        ...,
        description=f"Expense category. Suggested: {', '.join(VALID_CATEGORIES)}.",
        examples=["Food"],
    )
    date: date = Field(
        ...,
        description="Date when the expense occurred in YYYY-MM-DD format.",
        examples=["2026-10-14"],
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional additional details or notes.",
        examples=["Weekly supermarket run"],
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or only whitespace.")
        return stripped

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Category cannot be empty or only whitespace.")
        # Normalize category to Title Case if matching known categories
        for valid in VALID_CATEGORIES:
            if stripped.lower() == valid.lower():
                return valid
        return stripped.title()


class ExpenseCreate(ExpenseBase):
    """Schema for creating a new expense record."""
    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating an existing expense record. All fields are optional."""
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated title of the expense.",
        examples=["Supermarket Groceries"],
    )
    amount: Optional[float] = Field(
        None,
        gt=0,
        description="Updated amount. Must be strictly positive (> 0).",
        examples=[52.00],
    )
    category: Optional[str] = Field(
        None,
        description="Updated category.",
        examples=["Food"],
    )
    date: Optional[date] = Field(
        None,
        description="Updated expense date in YYYY-MM-DD format.",
        examples=["2026-10-15"],
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Updated notes or details.",
        examples=["Included household cleaning supplies"],
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Title cannot be empty or only whitespace.")
            return stripped
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Category cannot be empty or only whitespace.")
            for valid in VALID_CATEGORIES:
                if stripped.lower() == valid.lower():
                    return valid
            return stripped.title()
        return v


class ExpenseResponse(ExpenseBase):
    """Schema for expense responses returned to the client."""
    id: int = Field(..., description="Unique integer identifier of the expense.", examples=[1])

    class Config:
        from_attributes = True


class PaginatedExpenseResponse(BaseModel):
    """Schema for paginated expense list responses."""
    total: int = Field(..., description="Total number of matching expenses.", examples=[25])
    page: int = Field(..., description="Current page number (1-indexed).", examples=[1])
    limit: int = Field(..., description="Number of items per page.", examples=[10])
    total_pages: int = Field(..., description="Total number of available pages.", examples=[3])
    items: List[ExpenseResponse] = Field(..., description="List of expenses for the current page.")


# --- Analytics & Reporting Models ---

class MonthlyReportItem(BaseModel):
    """Monthly summary report item."""
    month: str = Field(..., description="Year and month in YYYY-MM format.", examples=["2026-10"])
    total_amount: float = Field(..., description="Total spent in this month.", examples=[1250.75])
    count: int = Field(..., description="Number of expenses in this month.", examples=[14])
    average_amount: float = Field(..., description="Average expense amount in this month.", examples=[89.34])


class MonthlyReportResponse(BaseModel):
    """Response schema for monthly expense report."""
    total_spending: float = Field(..., description="Overall total spending across all months.", examples=[5430.50])
    items: List[MonthlyReportItem] = Field(..., description="Monthly breakdown list.")


class CategoryReportItem(BaseModel):
    """Category breakdown report item."""
    category: str = Field(..., description="Expense category name.", examples=["Food"])
    total_amount: float = Field(..., description="Total amount spent in this category.", examples=[450.00])
    count: int = Field(..., description="Number of expenses in this category.", examples=[5])
    percentage: float = Field(..., description="Percentage of total spending.", examples=[36.0])


class CategoryReportResponse(BaseModel):
    """Response schema for category expense report."""
    total_spending: float = Field(..., description="Overall total spending across all categories.", examples=[1250.00])
    items: List[CategoryReportItem] = Field(..., description="Category breakdown list.")


class StatisticsResponse(BaseModel):
    """Response schema for comprehensive expense statistics."""
    total_spending: float = Field(..., description="Total spending across all recorded expenses.", examples=[3500.00])
    average_expense: float = Field(..., description="Average amount per expense.", examples=[70.00])
    highest_expense: Optional[float] = Field(None, description="Maximum single expense recorded.", examples=[300.00])
    lowest_expense: Optional[float] = Field(None, description="Minimum single expense recorded.", examples=[12.50])
    expense_count: int = Field(..., description="Total count of expenses recorded.", examples=[50])
    category_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Total amount spent per category.",
        examples=[{"Food": 1500.0, "Transportation": 800.0}],
    )


class MessageResponse(BaseModel):
    """Generic status/message response."""
    message: str = Field(..., description="Status message description.", examples=["Expense deleted successfully."])
    deleted_id: Optional[int] = Field(None, description="ID of deleted item, if applicable.", examples=[1])
