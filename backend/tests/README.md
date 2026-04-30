# Test Suite for SIEM M365

## Overview

This test suite provides comprehensive testing for the SIEM M365 backend application including:
- Health check endpoint validation
- Authentication flow testing
- Audit logs ingestion
- Query and dashboard functionality
- Database connectivity

## Test Structure

```
tests/
├── conftest.py          # Pytest configuration and fixtures
├── test_utils.py        # Test utilities and helpers
├── test_health.py       # Health endpoint tests
├── test_auth.py         # Authentication tests
├── test_ingest.py       # Ingestion endpoint tests
├── test_query.py        # Query endpoint tests (future)
└── test_dashboard.py    # Dashboard endpoint tests (future)
```

## Key Fixtures

### Database Fixtures
- `db_session`: SQLite test database session for each test
- `test_db_url`: Test database connection string
- `engine`: SQLAlchemy engine for test database

### User Fixtures
- `test_user`: Standard test user with basic permissions
- `test_admin`: Admin user for elevated operations

### Sample Data Fixtures
- `sample_audit_log()`: Single M365 audit log record
- `sample_audit_logs_file()`: Temporary JSON file with audit logs
- `sample_incident()`: Sample security incident

### HTTP Client
- `client`: FastAPI TestClient for API testing

## Test Utilities

### TestDataBuilder
Factory for creating consistent test data:
```python
# Create single audit log
log = TestDataBuilder.audit_log(
    operation="UserLoggedIn",
    user_id="user@example.com"
)

# Create batch
logs = TestDataBuilder.audit_logs_batch(count=5)
```

### APITestHelper
Helpers for API assertions:
```python
# Successful response
data = APITestHelper.assert_success(response, 200)

# Error response
error_data = APITestHelper.assert_error(response, 400)

# File upload
response = APITestHelper.upload_file(
    client, 
    "/api/v1/ingest/upload/audit-logs",
    {"records": []}
)
```

### DatabaseAssert
Database-level assertions:
```python
# Check if record exists
if DatabaseAssert.record_exists(db_session, M365AuditLog, id="123"):
    pass

# Count records
count = DatabaseAssert.record_count(db_session, M365AuditLog)

# Assert record created
record = DatabaseAssert.assert_record_created(
    db_session, 
    M365AuditLog, 
    id="123"
)
```

## Running Tests

### Install test dependencies
```bash
pip install pytest pytest-asyncio pytest-mock
```

### Run all tests
```bash
pytest backend/tests/ -v
```

### Run specific test file
```bash
pytest backend/tests/test_health.py -v
```

### Run specific test class
```bash
pytest backend/tests/test_health.py::TestHealth -v
```

### Run with coverage
```bash
pip install pytest-cov
pytest backend/tests/ --cov=app --cov-report=html
```

### Run with markers
```bash
pytest -m "not integration" backend/tests/
```

## Test Coverage Goals

| Component | Coverage | Status |
|-----------|----------|--------|
| Health Check | Endpoint validation | ✅ |
| Authentication | Login flow, token generation | 📝 |
| Audit Logs | Upload, parsing, storage | 📝 |
| Query API | Data retrieval, filtering | 📋 |
| Dashboard | Statistics calculation | 📋 |

## Adding New Tests

1. Create test file: `test_<feature>.py`
2. Import fixtures from `conftest.py`
3. Use utilities from `test_utils.py`
4. Follow naming convention: `test_<functionality>`

Example:
```python
def test_new_feature(client, db_session, test_user):
    """Test description"""
    response = client.post("/api/v1/endpoint", json={"data": "value"})
    assert response.status_code == 200
```

## Debugging Tests

### Verbose output
```bash
pytest backend/tests/ -vv
```

### Print debugging info
```bash
pytest backend/tests/ -s  # Capture print statements
```

### Drop into debugger
```python
import pdb; pdb.set_trace()  # In test code
```

### Run with markers for specific tests
```bash
pytest -m "slow" backend/tests/  # Only slow tests
```

## CI/CD Integration

Tests are run automatically on:
- Push to main branch
- Pull requests
- Scheduled nightly runs

See `.github/workflows/` for CI configuration.

## Known Issues

None currently.

## Future Improvements

- [ ] Integration tests with real database
- [ ] Performance benchmarks
- [ ] API load testing
- [ ] Security testing
- [ ] End-to-end workflow tests
