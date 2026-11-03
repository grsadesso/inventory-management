# API Tests

Comprehensive test suite for the Factory Inventory Management System backend APIs.

## Test Structure

```
tests/
├── pytest.ini          # Pytest configuration
├── backend/            # Backend API tests
│   ├── conftest.py     # Test fixtures and configuration (incl. in-memory state reset)
│   ├── test_inventory.py        # Inventory endpoint tests (10 tests)
│   ├── test_dashboard.py        # Dashboard endpoint tests (13 tests)
│   ├── test_misc_endpoints.py   # Demand, backlog, spending, root tests (17 tests)
│   ├── test_tasks.py            # Task endpoint tests (14 tests)
│   └── test_purchase_orders.py  # Purchase order endpoint tests (19 tests)
└── README.md           # This file
```

## Running Tests

### Run all tests
```bash
cd tests
uv run pytest -v
```

### Run specific test file
```bash
cd tests
uv run pytest backend/test_inventory.py -v
```

### Run specific test class
```bash
cd tests
uv run pytest backend/test_inventory.py::TestInventoryEndpoints -v
```

### Run specific test
```bash
cd tests
uv run pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory -v
```

### Run with coverage (requires pytest-cov)
```bash
cd tests
uv run pytest --cov=../server --cov-report=html
```

## Test Coverage

**Total: 73 tests** covering the inventory, dashboard, demand, backlog, spending, root, task and purchase order endpoints.

Not covered yet: `/api/orders` and `/api/orders/{id}` (only exercised indirectly by the dashboard tests) and `/api/reports/*`.

### Inventory Endpoints (10 tests)
- ✓ Get all inventory items
- ✓ Filter by warehouse
- ✓ Filter by category (including Power Supplies)
- ✓ Filter by multiple criteria
- ✓ Get specific item by ID
- ✓ Handle non-existent items (404)
- ✓ Validate field structure
- ✓ Validate data types

### Dashboard Endpoints (13 tests)
- ✓ Get dashboard summary
- ✓ Validate data types and non-negative values
- ✓ Filter by warehouse, category, status, month
- ✓ Multiple filter combinations
- ✓ Validate calculation accuracy:
  - Pending orders calculation
  - Low stock items calculation
  - Total inventory value calculation

### Miscellaneous Endpoints (17 tests)
- **Demand Forecasts (5 tests)**
  - ✓ Get demand forecasts
  - ✓ Validate trend values
  - ✓ Validate non-negative values
  - ✓ Stable items change less than 2%
  - ✓ Expected stable items are present

- **Backlog Items (4 tests)**
  - ✓ Get backlog items
  - ✓ Validate priority values
  - ✓ Validate quantity logic
  - ✓ Validate days delayed

- **Spending Data (6 tests)**
  - ✓ Get spending summary
  - ✓ Get monthly spending
  - ✓ All cost categories present
  - ✓ Monthly spending varies
  - ✓ Get category spending
  - ✓ Get recent transactions

- **Root Endpoint (2 tests)**
  - ✓ API info endpoint
  - ✓ Validate response structure

### Task Endpoints (14 tests)
- ✓ List tasks (empty at start, newest first)
- ✓ Create a task (201, default priority)
- ✓ Validation errors (422)
- ✓ Toggle pending/completed
- ✓ Delete a task
- ✓ Unknown id returns 404, non-integer id returns 422
- ✓ In-memory state does not leak between tests

### Purchase Order Endpoints (19 tests)
- ✓ Create a purchase order (201, `PO-NNNN` ids, notes optional)
- ✓ Get a purchase order by backlog item id
- ✓ Unknown backlog item returns 404, missing purchase order returns 404
- ✓ Duplicate purchase order for a backlog item returns 409
- ✓ Validation errors (422): quantity, unit cost, supplier, missing fields
- ✓ `/api/backlog` reports `has_purchase_order: true` after creating one
- ✓ In-memory state does not leak between tests

## Test Features

- **FastAPI TestClient**: Uses FastAPI's built-in test client for fast, isolated testing
- **Fixtures**: Reusable test fixtures in `conftest.py`, including an autouse fixture that restores the in-memory tasks and purchase orders after each test
- **Comprehensive Validation**: Tests data structure, types, calculations, and business logic
- **Filter Testing**: Validates all filter combinations and edge cases
- **Error Handling**: Tests 404 responses and edge cases
- **New Features**: Includes tests for Power Supplies category

## Dependencies

Tests require the following packages (automatically installed with `uv sync`):
- pytest >= 8.0.0
- pytest-asyncio >= 0.23.0
- httpx >= 0.27.0
- pytest-cov >= 4.1.0 (optional, for coverage reports)

## Adding New Tests

1. Create test file in `tests/backend/` following naming convention `test_*.py`
2. Import `client` fixture from conftest.py
3. Create test class (optional but recommended for organization)
4. Write test functions starting with `test_`
5. Run tests to verify

Example:
```python
class TestNewEndpoint:
    def test_new_feature(self, client):
        response = client.get("/api/new-endpoint")
        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
```

## CI/CD Integration

To integrate with CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run API Tests
  run: |
    cd tests
    uv run pytest -v --tb=short
```

## Notes

- All tests use in-memory mock data (no database required)
- Tests are independent and can run in any order
- FastAPI TestClient handles app lifecycle automatically
- Tests run in ~0.13 seconds
