"""Service layer handling business logic and CSV storage operations."""

import csv
import io
import math
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

from app.config import EXPENSE_DATA_FILE, VALID_SORT_FIELDS
from app.models import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    PaginatedExpenseResponse,
)
from app.utils import CSV_FIELDNAMES, ensure_csv_initialized, round_currency, safe_atomic_write


class ExpenseService:
    """Service for managing expenses persisted in a CSV file."""

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or EXPENSE_DATA_FILE

    def _read_all(self) -> List[Dict[str, Any]]:
        """
        Reads all expense rows from the CSV file.
        Safely initializes the file if it does not exist or is empty.
        """
        try:
            ensure_csv_initialized(self.file_path)
            rows: List[Dict[str, Any]] = []

            with open(self.file_path, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row or not row.get("id"):
                        continue
                    try:
                        parsed_row = {
                            "id": int(row["id"]),
                            "title": row["title"],
                            "amount": round_currency(float(row["amount"])),
                            "category": row["category"],
                            "date": date.fromisoformat(row["date"]),
                            "description": row.get("description") if row.get("description") else None,
                        }
                        rows.append(parsed_row)
                    except (ValueError, KeyError):
                        # Skip corrupt lines gracefully
                        continue
            return rows
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage error reading expenses: {str(exc)}",
            )

    def _write_all(self, rows: List[Dict[str, Any]]) -> None:
        """Atomically saves all expense rows to the CSV file."""
        try:
            safe_atomic_write(self.file_path, rows)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage error saving expenses: {str(exc)}",
            )

    def get_all(
        self,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: str = "date",
        order: str = "desc",
        page: int = 1,
        limit: int = 10,
    ) -> PaginatedExpenseResponse:
        """
        Retrieves expenses with category/date filtering, sorting, and pagination.
        """
        rows = self._read_all()

        # Filtering by Category
        if category:
            cat_lower = category.strip().lower()
            rows = [r for r in rows if r["category"].lower() == cat_lower]

        # Filtering by Date range
        if start_date:
            rows = [r for r in rows if r["date"] >= start_date]
        if end_date:
            rows = [r for r in rows if r["date"] <= end_date]

        # Sorting
        sort_field = sort_by if sort_by in VALID_SORT_FIELDS else "date"
        reverse_sort = order.lower() == "desc"

        def sort_key(item: Dict[str, Any]) -> Any:
            val = item.get(sort_field)
            if val is None:
                return ""
            if isinstance(val, str):
                return val.lower()
            return val

        rows.sort(key=sort_key, reverse=reverse_sort)

        # Pagination
        total = len(rows)
        total_pages = math.ceil(total / limit) if total > 0 else 1
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = [ExpenseResponse(**r) for r in rows[start_idx:end_idx]]

        return PaginatedExpenseResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=paginated_items,
        )

    def get_by_id(self, expense_id: int) -> ExpenseResponse:
        """Retrieves a single expense by its unique identifier."""
        rows = self._read_all()
        for r in rows:
            if r["id"] == expense_id:
                return ExpenseResponse(**r)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} not found.",
        )

    def create(self, expense_in: ExpenseCreate) -> ExpenseResponse:
        """Creates and appends a new expense with an auto-incremented ID."""
        rows = self._read_all()
        next_id = max([r["id"] for r in rows], default=0) + 1

        new_record = {
            "id": next_id,
            "title": expense_in.title,
            "amount": round_currency(expense_in.amount),
            "category": expense_in.category,
            "date": expense_in.date,
            "description": expense_in.description,
        }
        rows.append(new_record)
        self._write_all(rows)
        return ExpenseResponse(**new_record)

    def update(self, expense_id: int, expense_update: ExpenseUpdate) -> ExpenseResponse:
        """Updates an existing expense record."""
        rows = self._read_all()
        found_idx = None

        for idx, r in enumerate(rows):
            if r["id"] == expense_id:
                found_idx = idx
                break

        if found_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense with ID {expense_id} not found.",
            )

        update_data = expense_update.model_dump(exclude_unset=True)
        current = rows[found_idx]

        for key, value in update_data.items():
            if value is not None:
                if key == "amount":
                    current[key] = round_currency(value)
                else:
                    current[key] = value

        rows[found_idx] = current
        self._write_all(rows)
        return ExpenseResponse(**current)

    def delete(self, expense_id: int) -> bool:
        """Deletes an expense record by ID."""
        rows = self._read_all()
        initial_count = len(rows)
        rows = [r for r in rows if r["id"] != expense_id]

        if len(rows) == initial_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense with ID {expense_id} not found.",
            )

        self._write_all(rows)
        return True

    def export_csv(self) -> str:
        """Generates a CSV formatted string of all current expenses."""
        ensure_csv_initialized(self.file_path)
        with open(self.file_path, mode="r", newline="", encoding="utf-8") as f:
            return f.read()

