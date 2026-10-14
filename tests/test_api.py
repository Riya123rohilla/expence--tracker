"""Automated test suite covering CRUD, validation, analytics, and error cases."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app, get_service
from app.services import ExpenseService


@pytest.fixture
def test_csv_file(tmp_path: Path):
    """
    Creates an isolated temporary CSV file for testing.
    Ensures tests NEVER touch or modify real production data in data/expenses.csv.
    """
    csv_file = tmp_path / "test_expenses.csv"
    return csv_file


@pytest.fixture
def client(test_csv_file: Path):
    """
    Provides a TestClient configured with an isolated test ExpenseService.
    """
    test_service = ExpenseService(file_path=test_csv_file)
    app.dependency_overrides[get_service] = lambda: test_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==========================================
# TEST ROOT & HEALTH
# ==========================================


def test_root_endpoint(client: TestClient):
    """Test root welcoming endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Expense Tracker REST API" in data["message"]
    assert "/docs" in data["documentation"]


# ==========================================
# TEST CRUD OPERATIONS
# ==========================================


def test_create_expense_success(client: TestClient):
    """Test creating a valid expense."""
    payload = {
        "title": "Grocery Shopping",
        "amount": 75.50,
        "category": "Food",
        "date": "2026-10-10",
        "description": "Weekly essentials",
    }
    response = client.post("/expenses", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Grocery Shopping"
    assert data["amount"] == 75.50
    assert data["category"] == "Food"
    assert data["date"] == "2026-10-10"
    assert data["description"] == "Weekly essentials"


def test_get_expense_by_id_success(client: TestClient):
    """Test retrieving an existing expense by ID."""
    payload = {
        "title": "Subway Ticket",
        "amount": 3.50,
        "category": "Transportation",
        "date": "2026-10-11",
    }
    create_res = client.post("/expenses", json=payload)
    expense_id = create_res.json()["id"]

    res = client.get(f"/expenses/{expense_id}")
    assert res.status_code == 200
    assert res.json()["title"] == "Subway Ticket"
    assert res.json()["amount"] == 3.50


def test_get_expense_by_id_not_found(client: TestClient):
    """Test retrieving a non-existent expense returns 404."""
    res = client.get("/expenses/9999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_update_expense_success(client: TestClient):
    """Test updating fields on an existing expense."""
    create_res = client.post(
        "/expenses",
        json={"title": "Coffee", "amount": 4.00, "category": "Food", "date": "2026-10-12"},
    )
    expense_id = create_res.json()["id"]

    # Partial update: title and amount
    update_res = client.put(
        f"/expenses/{expense_id}",
        json={"title": "Premium Coffee", "amount": 6.50},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["title"] == "Premium Coffee"
    assert updated_data["amount"] == 6.50
    assert updated_data["category"] == "Food"  # preserved


def test_update_expense_not_found(client: TestClient):
    """Test updating a non-existent expense returns 404."""
    res = client.put(
        "/expenses/9999",
        json={"title": "Non-existent"},
    )
    assert res.status_code == 404


def test_delete_expense_success(client: TestClient):
    """Test deleting an existing expense."""
    create_res = client.post(
        "/expenses",
        json={"title": "Books", "amount": 25.00, "category": "Education", "date": "2026-10-12"},
    )
    expense_id = create_res.json()["id"]

    del_res = client.delete(f"/expenses/{expense_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted_id"] == expense_id

    # Confirm deleted
    get_res = client.get(f"/expenses/{expense_id}")
    assert get_res.status_code == 404


def test_delete_expense_not_found(client: TestClient):
    """Test deleting a non-existent expense returns 404."""
    del_res = client.delete("/expenses/9999")
    assert del_res.status_code == 404


# ==========================================
# TEST VALIDATION ERRORS (HTTP 422)
# ==========================================


def test_validation_negative_or_zero_amount(client: TestClient):
    """Test validation rejection for non-positive amounts."""
    # Zero amount
    res1 = client.post(
        "/expenses",
        json={"title": "Test Zero", "amount": 0.0, "category": "Food", "date": "2026-10-10"},
    )
    assert res1.status_code == 422

    # Negative amount
    res2 = client.post(
        "/expenses",
        json={"title": "Test Negative", "amount": -15.0, "category": "Food", "date": "2026-10-10"},
    )
    assert res2.status_code == 422


def test_validation_empty_or_whitespace_title(client: TestClient):
    """Test validation rejection for empty or whitespace-only title."""
    res = client.post(
        "/expenses",
        json={"title": "   ", "amount": 20.0, "category": "Food", "date": "2026-10-10"},
    )
    assert res.status_code == 422


def test_validation_invalid_date_format(client: TestClient):
    """Test validation rejection for invalid date format."""
    res = client.post(
        "/expenses",
        json={"title": "Gym", "amount": 50.0, "category": "Health", "date": "not-a-date"},
    )
    assert res.status_code == 422


def test_validation_date_range_inverted(client: TestClient):
    """Test 422 returned when start_date is later than end_date."""
    res = client.get("/expenses?start_date=2026-10-20&end_date=2026-10-10")
    assert res.status_code == 422
    assert "start_date must be less than or equal to end_date" in res.json()["detail"]


# ==========================================
# TEST FILTERING, SORTING, PAGINATION
# ==========================================


def test_filtering_and_pagination(client: TestClient):
    """Test category filtering, date filtering, pagination, and sorting."""
    # Seed data
    client.post("/expenses", json={"title": "Apple", "amount": 2.0, "category": "Food", "date": "2026-10-01"})
    client.post("/expenses", json={"title": "Bus", "amount": 5.0, "category": "Transportation", "date": "2026-10-02"})
    client.post("/expenses", json={"title": "Burger", "amount": 12.0, "category": "Food", "date": "2026-10-05"})
    client.post("/expenses", json={"title": "Train", "amount": 30.0, "category": "Transportation", "date": "2026-10-15"})
    client.post("/expenses", json={"title": "Pizza", "amount": 20.0, "category": "Food", "date": "2026-10-20"})

    # Filter by category Food
    food_res = client.get("/expenses?category=Food")
    assert food_res.status_code == 200
    food_data = food_res.json()
    assert food_data["total"] == 3
    assert all(item["category"] == "Food" for item in food_data["items"])

    # Filter by Date Range
    date_res = client.get("/expenses?start_date=2026-10-02&end_date=2026-10-10")
    assert date_res.status_code == 200
    date_data = date_res.json()
    assert date_data["total"] == 2
    titles = [i["title"] for i in date_data["items"]]
    assert "Bus" in titles and "Burger" in titles

    # Sorting by amount descending
    sort_res = client.get("/expenses?sort_by=amount&order=desc")
    assert sort_res.status_code == 200
    amounts = [i["amount"] for i in sort_res.json()["items"]]
    assert amounts == sorted(amounts, reverse=True)

    # Pagination: page 1 with limit 2
    p1 = client.get("/expenses?page=1&limit=2")
    assert p1.status_code == 200
    assert len(p1.json()["items"]) == 2
    assert p1.json()["total"] == 5
    assert p1.json()["total_pages"] == 3

    # Pagination: page 3 with limit 2 (should have 1 item)
    p3 = client.get("/expenses?page=3&limit=2")
    assert p3.status_code == 200
    assert len(p3.json()["items"]) == 1


# ==========================================
# TEST ANALYTICS & REPORTS
# ==========================================


def test_empty_reports(client: TestClient):
    """Test analytics endpoints when no expenses exist."""
    res_stats = client.get("/reports/statistics")
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total_spending"] == 0.0
    assert stats["expense_count"] == 0
    assert stats["highest_expense"] is None

    res_monthly = client.get("/reports/monthly")
    assert res_monthly.status_code == 200
    assert res_monthly.json()["total_spending"] == 0.0
    assert len(res_monthly.json()["items"]) == 0

    res_cat = client.get("/reports/category")
    assert res_cat.status_code == 200
    assert res_cat.json()["total_spending"] == 0.0
    assert len(res_cat.json()["items"]) == 0


def test_populated_reports(client: TestClient):
    """Test analytics calculations with sample data."""
    # Add expenses across 2 months and 2 categories
    client.post("/expenses", json={"title": "Groceries", "amount": 100.0, "category": "Food", "date": "2026-09-15"})
    client.post("/expenses", json={"title": "Dinner", "amount": 50.0, "category": "Food", "date": "2026-09-20"})
    client.post("/expenses", json={"title": "Flight", "amount": 250.0, "category": "Transportation", "date": "2026-10-05"})

    # Statistics check
    stats_res = client.get("/reports/statistics")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_spending"] == 400.0
    assert stats["expense_count"] == 3
    assert stats["average_expense"] == round(400.0 / 3, 2)
    assert stats["highest_expense"] == 250.0
    assert stats["lowest_expense"] == 50.0
    assert stats["category_breakdown"]["Food"] == 150.0
    assert stats["category_breakdown"]["Transportation"] == 250.0

    # Monthly report check
    month_res = client.get("/reports/monthly")
    assert month_res.status_code == 200
    monthly = month_res.json()
    assert monthly["total_spending"] == 400.0
    assert len(monthly["items"]) == 2

    # Category report check
    cat_res = client.get("/reports/category")
    assert cat_res.status_code == 200
    cat_data = cat_res.json()
    assert cat_data["total_spending"] == 400.0
    assert len(cat_data["items"]) == 2
    # Verify percentage calculation
    trans_item = next(i for i in cat_data["items"] if i["category"] == "Transportation")
    assert trans_item["percentage"] == 62.5  # 250 / 400 * 100


# ==========================================
# TEST CSV EXPORT
# ==========================================


def test_export_csv(client: TestClient):
    """Test CSV export returns text/csv media type and contains headers and data."""
    client.post("/expenses", json={"title": "Movie", "amount": 15.0, "category": "Entertainment", "date": "2026-10-14"})

    res = client.get("/reports/export")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment; filename=expenses_report.csv" in res.headers["content-disposition"]
    content = res.text
    assert "id,title,amount,category,date,description" in content
    assert "Movie" in content
    assert "15.0" in content

