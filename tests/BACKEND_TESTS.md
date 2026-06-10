# Backend Testing Guide

This document describes the structure, execution, and design of the automated test suite for the FastAPI backend, utilizing `pytest`, `pytest-asyncio`, and `httpx`.

---

## 1. Directory Structure

All backend tests are stored in `tests/backend/`.

```
tests/backend/
├── conftest.py          # Setup hooks, in-memory SQLite DB, client fixtures
├── test_children.py     # Child endpoints: POST /children, GET /children/{id}
├── test_doctor.py       # Doctor endpoints: GET /doctor/flagged, POST /doctor/{id}/judgment
└── test_sessions.py     # Upload, retrieval, pipeline fallbacks, scoring logic
```

---

## 2. Test Fixtures (`conftest.py`)

To ensure database isolation, the test suite overrides the production database connection. It creates an in-memory SQLite engine and runs all table schema builds before executing tests.

### DB Connection Override
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

# Create in-memory SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Build schema
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    # Override FastAPI dependency
    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

---

## 3. Test Coverage

The test suite validates:
* **Input Validation Constraints:** Submitting letters in age months returns `422 Unprocessable Entity`; invalid formats are caught before database writes.
* **OpenFace and ASDMotion Fallbacks:** Simulates missing binaries (captures `FileNotFoundError`) and checks that the system returns default mock structures (`mock: true`, `expression_rate: 0.0`) without throwing internal 500 errors.
* **Scoring Rules:** Directly tests scoring functions in `scoring_thresholds.py` using values representing high, medium, and low-risk behavior limits, checking linear interpolation calculations.

---

## 4. Run Execution Commands

Execute tests inside the backend directory:
```bash
# Run tests synchronously
pytest ../tests/backend/ -v

# Run tests with HTML coverage report output
pytest ../tests/backend/ --cov=routers --cov=services --cov=ml --cov-report=html
```
The coverage output is generated inside the `backend/htmlcov/` directory.
