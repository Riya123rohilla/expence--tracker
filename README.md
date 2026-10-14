# Expense Tracker REST API

A beginner-friendly, modular, and production-ready **Expense Tracker REST API** built with **Python 3**, **FastAPI**, **Pydantic v2**, **Pandas**, **NumPy**, and safe **CSV storage**.

---

## 📋 Features

- **Full CRUD Operations**: Create, read, update, and delete expenses.
- **Pydantic Validation**: Automatic request validation for non-empty title, strictly positive amount (`> 0`), valid category, and ISO-8601 date (`YYYY-MM-DD`). Returns HTTP `422` with clear error messages on invalid input.
- **Data Persistence in CSV**: Stores records in `data/expenses.csv`, auto-increments unique integer IDs, safely initializes headers, and uses atomic writes to prevent data corruption.
- **Search, Filter, Sort & Paginate**:
  - Filter by category (case-insensitive).
  - Filter by date range (`start_date`, `end_date`).
  - Sort by any field (`date`, `amount`, `title`, `id`) in `asc` or `desc` order.
  - Paginate with `page` and `limit`.
- **Analytics & Reports (Pandas & NumPy)**:
  - **Monthly Report**: Monthly breakdown with total spending, expense count, and average expense.
  - **Category Breakdown**: Category totals, counts, and percentage share.
  - **Statistical Summary**: Total spending, average expense, highest/lowest expense, total count, and category breakdown.
  - **CSV Export**: Direct download of all expenses in standard CSV format.
- **Automated Test Suite**: Tested with `pytest` and `httpx` using isolated temporary storage fixtures so tests never touch production data.
- **Interactive Documentation**: Auto-generated interactive Swagger UI and ReDoc.

---

## 📁 Project Structure

```text
expense_tracker_api/
├── app/
│   ├── __init__.py          # Package initializer
│   ├── main.py              # FastAPI app definition and route handlers
│   ├── models.py            # Pydantic models for validation and responses
│   ├── services.py          # Business logic, CSV persistence, and CRUD
│   ├── analytics.py         # Expense analytics powered by Pandas and NumPy
│   ├── utils.py             # Helper functions and atomic CSV writer
│   └── config.py            # Application configuration & constants
├── data/
│   └── expenses.csv         # Persistent CSV expense database
├── tests/
│   ├── __init__.py
│   └── test_api.py          # Automated tests for CRUD, validation, and analytics
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Project dependencies
├── .gitignore               # Ignored files (venv, caches, etc.)
└── README.md                # Project documentation
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Clone / Navigate to the Project
```bash
cd expense_tracker_api
```

### 3. Create and Activate a Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate on Linux / macOS:
source venv/bin/activate

# Or activate on Windows:
# venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🏃 Running the Server

Start the API server using `uvicorn`:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once started, the API will be available at:
- **Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **Alternative ReDoc UI**: `http://127.0.0.1:8000/redoc`

---

## 📖 API Documentation & Swagger UI

Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** in your browser to access the interactive Swagger documentation. You can test all endpoints, view input models, schemas, status codes, and JSON responses directly from your web browser.

---

## 🛣️ API Endpoints Summary

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API health check & overview | 200 OK |
| `POST` | `/expenses` | Create a new expense | 201 Created |
| `GET` | `/expenses` | List expenses (filter, sort, paginate) | 200 OK |
| `GET` | `/expenses/{id}` | Get single expense by ID | 200 OK / 404 |
| `PUT` | `/expenses/{id}` | Update an existing expense | 200 OK / 404 |
| `DELETE` | `/expenses/{id}` | Delete an expense by ID | 200 OK / 404 |
| `GET` | `/reports/monthly` | Monthly spending breakdown | 200 OK |
| `GET` | `/reports/category` | Category spending breakdown & % share | 200 OK |
| `GET` | `/reports/statistics` | Metrics (total, avg, max, min, count) | 200 OK |
| `GET` | `/reports/export` | Download expenses as CSV file | 200 OK |

---

## 💡 Example Requests & Responses

### 1. Create an Expense
**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/expenses" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Grocery Shopping",
    "amount": 75.50,
    "category": "Food",
    "date": "2026-10-14",
    "description": "Weekly essentials"
  }'
```
**Response (`201 Created`):**
```json
{
  "id": 1,
  "title": "Grocery Shopping",
  "amount": 75.5,
  "category": "Food",
  "date": "2026-10-14",
  "description": "Weekly essentials"
}
```

---

### 2. List Expenses (with Filtering, Sorting & Pagination)
**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/expenses?category=Food&sort_by=amount&order=desc&page=1&limit=5"
```
**Response (`200 OK`):**
```json
{
  "total": 1,
  "page": 1,
  "limit": 5,
  "total_pages": 1,
  "items": [
    {
      "id": 1,
      "title": "Grocery Shopping",
      "amount": 75.5,
      "category": "Food",
      "date": "2026-10-14",
      "description": "Weekly essentials"
    }
  ]
}
```

---

### 3. Get Expense by ID
**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/expenses/1"
```
**Response (`200 OK`):**
```json
{
  "id": 1,
  "title": "Grocery Shopping",
  "amount": 75.5,
  "category": "Food",
  "date": "2026-10-14",
  "description": "Weekly essentials"
}
```

---

### 4. Update an Expense
**Request:**
```bash
curl -X PUT "http://127.0.0.1:8000/expenses/1" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 82.00,
    "description": "Weekly essentials plus household supplies"
  }'
```
**Response (`200 OK`):**
```json
{
  "id": 1,
  "title": "Grocery Shopping",
  "amount": 82.0,
  "category": "Food",
  "date": "2026-10-14",
  "description": "Weekly essentials plus household supplies"
}
```

---

### 5. Delete an Expense
**Request:**
```bash
curl -X DELETE "http://127.0.0.1:8000/expenses/1"
```
**Response (`200 OK`):**
```json
{
  "message": "Expense with ID 1 successfully deleted.",
  "deleted_id": 1
}
```

---

### 6. Get Analytics & Reports

#### Overall Statistics:
```bash
curl -X GET "http://127.0.0.1:8000/reports/statistics"
```
**Response (`200 OK`):**
```json
{
  "total_spending": 82.0,
  "average_expense": 82.0,
  "highest_expense": 82.0,
  "lowest_expense": 82.0,
  "expense_count": 1,
  "category_breakdown": {
    "Food": 82.0
  }
}
```

#### Category Report:
```bash
curl -X GET "http://127.0.0.1:8000/reports/category"
```
**Response (`200 OK`):**
```json
{
  "total_spending": 82.0,
  "items": [
    {
      "category": "Food",
      "total_amount": 82.0,
      "count": 1,
      "percentage": 100.0
    }
  ]
}
```

#### Monthly Report:
```bash
curl -X GET "http://127.0.0.1:8000/reports/monthly"
```
**Response (`200 OK`):**
```json
{
  "total_spending": 82.0,
  "items": [
    {
      "month": "2026-10",
      "total_amount": 82.0,
      "count": 1,
      "average_amount": 82.0
    }
  ]
}
```

#### Export CSV:
```bash
curl -X GET "http://127.0.0.1:8000/reports/export" -o my_expenses.csv
```

---

## 🧪 Running Automated Tests

Run the full automated test suite using `pytest`:

```bash
pytest -v
```

All 16 tests run against an isolated temporary CSV file, verifying:
- ✅ **CRUD Operations**: Create, Read, Update, Delete with proper status codes.
- ✅ **Validation (422)**: Negative/zero amount rejection, empty title rejection, invalid date formats, reversed date ranges.
- ✅ **Not Found Handling (404)**: Accessing or modifying non-existent IDs.
- ✅ **Filtering, Sorting & Pagination**: Query parameters, sort direction, page offset and limits.
- ✅ **Pandas & NumPy Analytics**: Edge cases with 0 records, mathematical correctness of aggregations, averages, percentages, and max/min values.
- ✅ **CSV Export**: Attachment headers and content format.

---

## 🛡️ Data Persistence & Safety

- **Atomic Writes**: Uses `os.replace` on temporary files to prevent data corruption during unexpected write interruptions.
- **Graceful File Initialization**: Automatically checks and writes CSV headers if the storage file is missing or empty.
- **Test Isolation**: Automated tests execute using `tmp_path` fixtures, guaranteeing production data is never touched or polluted.

