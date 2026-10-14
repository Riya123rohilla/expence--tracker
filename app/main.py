"""FastAPI Application entrypoint with API routes for Expense Tracker."""

from datetime import date
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Response, status
from fastapi.responses import PlainTextResponse

from app.analytics import (
    get_category_report,
    get_monthly_report,
    get_statistics_report,
)
from app.config import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    VALID_SORT_FIELDS,
)
from app.models import (
    CategoryReportResponse,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    MessageResponse,
    MonthlyReportResponse,
    PaginatedExpenseResponse,
    StatisticsResponse,
)
from app.services import ExpenseService

# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


def get_service() -> ExpenseService:
    """Dependency provider for ExpenseService."""
    return ExpenseService()


@app.get("/", tags=["General"])
def root_info():
    """API health check and welcoming endpoint with documentation link."""
    return {
        "message": "Welcome to the Expense Tracker REST API",
        "documentation": "/docs",
        "version": API_VERSION,
        "endpoints": {
            "expenses": "/expenses",
            "monthly_report": "/reports/monthly",
            "category_report": "/reports/category",
            "statistics": "/reports/statistics",
            "export_csv": "/reports/export",
        },
    }


# ==========================================
# EXPENSE CRUD ROUTERS
# ==========================================


@app.post(
    "/expenses",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense",
    tags=["Expenses"],
)
def create_expense(
    expense_in: ExpenseCreate,
    service: ExpenseService = Depends(get_service),
):
    """
    Records a new expense item with required title, positive amount, category, and date.
    """
    return service.create(expense_in)


@app.get(
    "/expenses",
    response_model=PaginatedExpenseResponse,
    summary="List expenses with filtering, sorting, and pagination",
    tags=["Expenses"],
)
def list_expenses(
    category: Optional[str] = Query(None, description="Filter by category (case-insensitive)."),
    start_date: Optional[date] = Query(None, description="Filter from this date (YYYY-MM-DD)."),
    end_date: Optional[date] = Query(None, description="Filter up to this date (YYYY-MM-DD)."),
    sort_by: str = Query("date", description=f"Field to sort by: {', '.join(VALID_SORT_FIELDS)}."),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order: 'asc' or 'desc'."),
    page: int = Query(1, ge=1, description="Page number (1-indexed)."),
    limit: int = Query(10, ge=1, le=100, description="Items per page (max 100)."),
    service: ExpenseService = Depends(get_service),
):
    """
    Retrieve expenses with optional category/date filtering, sorting, and pagination.
    """
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be less than or equal to end_date.",
        )
    return service.get_all(
        category=category,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
        page=page,
        limit=limit,
    )


@app.get(
    "/expenses/{id}",
    response_model=ExpenseResponse,
    summary="Get single expense by ID",
    tags=["Expenses"],
)
def get_expense(
    id: int = Path(..., ge=1, description="Unique identifier of the expense."),
    service: ExpenseService = Depends(get_service),
):
    """
    Retrieve a specific expense by its integer ID.
    """
    return service.get_by_id(id)


@app.put(
    "/expenses/{id}",
    response_model=ExpenseResponse,
    summary="Update an existing expense",
    tags=["Expenses"],
)
def update_expense(
    expense_update: ExpenseUpdate,
    id: int = Path(..., ge=1, description="Unique identifier of the expense to update."),
    service: ExpenseService = Depends(get_service),
):
    """
    Update one or more attributes of an existing expense.
    """
    return service.update(id, expense_update)


@app.delete(
    "/expenses/{id}",
    response_model=MessageResponse,
    summary="Delete an expense",
    tags=["Expenses"],
)
def delete_expense(
    id: int = Path(..., ge=1, description="Unique identifier of the expense to delete."),
    service: ExpenseService = Depends(get_service),
):
    """
    Permanently delete an expense record by its ID.
    """
    service.delete(id)
    return MessageResponse(
        message=f"Expense with ID {id} successfully deleted.",
        deleted_id=id,
    )


# ==========================================
# ANALYTICS & REPORTING ROUTERS
# ==========================================


@app.get(
    "/reports/monthly",
    response_model=MonthlyReportResponse,
    summary="Monthly expense aggregation report",
    tags=["Reports & Analytics"],
)
def monthly_report(
    service: ExpenseService = Depends(get_service),
):
    """
    Returns monthly breakdown including total spent, count, and average expense.
    """
    return get_monthly_report(service.file_path)


@app.get(
    "/reports/category",
    response_model=CategoryReportResponse,
    summary="Category spending breakdown report",
    tags=["Reports & Analytics"],
)
def category_report(
    service: ExpenseService = Depends(get_service),
):
    """
    Returns category breakdown including total spent, count, and percentage share.
    """
    return get_category_report(service.file_path)


@app.get(
    "/reports/statistics",
    response_model=StatisticsResponse,
    summary="Statistical summary of expenses",
    tags=["Reports & Analytics"],
)
def statistics_report(
    service: ExpenseService = Depends(get_service),
):
    """
    Returns statistical metrics: total spending, average, highest, lowest, count, and category breakdown.
    """
    return get_statistics_report(service.file_path)


@app.get(
    "/reports/export",
    summary="Export all expenses as CSV file",
    tags=["Reports & Analytics"],
)
def export_csv_report(
    service: ExpenseService = Depends(get_service),
):
    """
    Downloads all current expense records as a CSV file.
    """
    csv_content = service.export_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=expenses_report.csv",
        },
    )


# Alias export endpoint for convenience
@app.get(
    "/expenses/export",
    include_in_schema=False,
)
def export_expenses_alias(service: ExpenseService = Depends(get_service)):
    return export_csv_report(service)
