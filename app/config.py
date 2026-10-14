"""Application configuration settings for Expense Tracker API."""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = BASE_DIR / "data"
DEFAULT_CSV_PATH = DEFAULT_DATA_DIR / "expenses.csv"

# Configurable data file path (can be overridden via environment variable for testing)
EXPENSE_DATA_FILE = Path(os.getenv("EXPENSE_DATA_FILE", str(DEFAULT_CSV_PATH)))

# Supported expense categories
VALID_CATEGORIES = [
    "Food",
    "Transportation",
    "Utilities",
    "Entertainment",
    "Health",
    "Shopping",
    "Housing",
    "Education",
    "Other",
]

# Supported sort fields
VALID_SORT_FIELDS = ["id", "title", "amount", "category", "date"]

# API Metadata
API_TITLE = "Expense Tracker REST API"
API_DESCRIPTION = (
    "A beginner-friendly, robust REST API for tracking expenses with "
    "CSV-based storage, Pydantic validation, and Pandas/NumPy analytics."
)
API_VERSION = "1.0.0"

