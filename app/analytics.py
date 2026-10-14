"""Expense analytics and reporting powered by Pandas and NumPy."""

from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd

from app.config import EXPENSE_DATA_FILE
from app.models import (
    CategoryReportItem,
    CategoryReportResponse,
    MonthlyReportItem,
    MonthlyReportResponse,
    StatisticsResponse,
)
from app.utils import round_currency


def load_expenses_dataframe(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads expense records from the CSV file into a Pandas DataFrame.
    Returns an empty DataFrame with expected columns if the file is missing or empty.
    """
    target_path = file_path or EXPENSE_DATA_FILE
    columns = ["id", "title", "amount", "category", "date", "description"]

    if not target_path.exists() or target_path.stat().st_size == 0:
        return pd.DataFrame(columns=columns)

    try:
        df = pd.read_csv(target_path)
        if df.empty or "amount" not in df.columns:
            return pd.DataFrame(columns=columns)

        # Clean and cast columns
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df = df.dropna(subset=["amount"])
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df["category"] = df["category"].fillna("Other").astype(str)
        return df
    except Exception:
        return pd.DataFrame(columns=columns)


def get_monthly_report(file_path: Optional[Path] = None) -> MonthlyReportResponse:
    """
    Calculates monthly expense aggregations:
    Total, count, and average spending per month.
    """
    df = load_expenses_dataframe(file_path)

    if df.empty:
        return MonthlyReportResponse(total_spending=0.0, items=[])

    # Extract year-month period for aggregation
    df["month"] = df["date"].dt.strftime("%Y-%m")

    grouped = (
        df.groupby("month")
        .agg(
            total_amount=("amount", "sum"),
            count=("amount", "count"),
            average_amount=("amount", "mean"),
        )
        .reset_index()
        .sort_values(by="month", ascending=False)
    )

    items = [
        MonthlyReportItem(
            month=str(row["month"]),
            total_amount=round_currency(row["total_amount"]),
            count=int(row["count"]),
            average_amount=round_currency(row["average_amount"]),
        )
        for _, row in grouped.iterrows()
    ]

    # Overall total spending using NumPy sum
    total_spending = round_currency(np.sum(df["amount"].to_numpy()))

    return MonthlyReportResponse(
        total_spending=total_spending,
        items=items,
    )


def get_category_report(file_path: Optional[Path] = None) -> CategoryReportResponse:
    """
    Calculates category spending aggregations:
    Total amount, count, and percentage share per category.
    """
    df = load_expenses_dataframe(file_path)

    if df.empty:
        return CategoryReportResponse(total_spending=0.0, items=[])

    total_spending = float(np.sum(df["amount"].to_numpy()))

    grouped = (
        df.groupby("category")
        .agg(
            total_amount=("amount", "sum"),
            count=("amount", "count"),
        )
        .reset_index()
        .sort_values(by="total_amount", ascending=False)
    )

    items = []
    for _, row in grouped.iterrows():
        cat_total = float(row["total_amount"])
        # NumPy-backed percentage calculation with zero-division safeguard
        percentage = (cat_total / total_spending * 100.0) if total_spending > 0 else 0.0
        items.append(
            CategoryReportItem(
                category=str(row["category"]),
                total_amount=round_currency(cat_total),
                count=int(row["count"]),
                percentage=round_currency(percentage),
            )
        )

    return CategoryReportResponse(
        total_spending=round_currency(total_spending),
        items=items,
    )


def get_statistics_report(file_path: Optional[Path] = None) -> StatisticsResponse:
    """
    Computes overall statistical metrics using Pandas and NumPy:
    - Total spending
    - Average expense
    - Highest expense
    - Lowest expense
    - Expense count
    - Category breakdown
    """
    df = load_expenses_dataframe(file_path)

    if df.empty:
        return StatisticsResponse(
            total_spending=0.0,
            average_expense=0.0,
            highest_expense=None,
            lowest_expense=None,
            expense_count=0,
            category_breakdown={},
        )

    amounts = df["amount"].to_numpy()

    # NumPy calculations
    total_spending = round_currency(np.sum(amounts))
    average_expense = round_currency(np.mean(amounts))
    highest_expense = round_currency(np.max(amounts))
    lowest_expense = round_currency(np.min(amounts))
    expense_count = int(len(amounts))

    # Category breakdown dictionary
    category_totals = df.groupby("category")["amount"].sum().to_dict()
    category_breakdown = {k: round_currency(v) for k, v in category_totals.items()}

    return StatisticsResponse(
        total_spending=total_spending,
        average_expense=average_expense,
        highest_expense=highest_expense,
        lowest_expense=lowest_expense,
        expense_count=expense_count,
        category_breakdown=category_breakdown,
    )
