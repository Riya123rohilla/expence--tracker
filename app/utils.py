"""Utility and helper functions for CSV operations, file safety, and data sanitization."""

import csv
import os
from pathlib import Path
from typing import Any, Dict, List

# Standard CSV column headers in order
CSV_FIELDNAMES: List[str] = ["id", "title", "amount", "category", "date", "description"]


def round_currency(val: float) -> float:
    """Round a monetary value to two decimal places."""
    return round(float(val), 2)


def safe_atomic_write(file_path: Path, rows: List[Dict[str, Any]], fieldnames: List[str] = CSV_FIELDNAMES) -> None:
    """
    Atomically writes rows to a CSV file.
    Writes to a temporary file first, then replaces the destination file.
    This prevents file corruption during unexpected interruptions.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = file_path.with_suffix(".tmp")

    with open(temp_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Ensure row matches fieldnames
            clean_row = {
                "id": row.get("id"),
                "title": row.get("title", ""),
                "amount": round_currency(row.get("amount", 0.0)),
                "category": row.get("category", ""),
                "date": str(row.get("date", "")),
                "description": row.get("description") or "",
            }
            writer.writerow(clean_row)

    # Atomic rename/replace
    os.replace(temp_path, file_path)


def ensure_csv_initialized(file_path: Path) -> None:
    """
    Ensures that the target CSV file and its parent directory exist.
    If the file does not exist or is empty, initializes it with header row.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists() or file_path.stat().st_size == 0:
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_FIELDNAMES)

