# Testing Strategy & Execution Guide

This document describes the testing practices, environment overrides, and verification targets for AutiScreen.

---

## 1. Testing Frameworks & Layers

We structure our quality assurance into distinct testing layers:

### 1.1 Backend Unit & API Tests (`tests/backend`)
* **Framework:** `pytest` + `pytest-asyncio` + `pytest-cov`.
* **Database Override:** Automatically intercepts production database calls and swaps them with an in-memory SQLite instance (`sqlite:///:memory:`). This isolates tests, prevents side effects on production data, and allows parallel runs.
* **Coverage Requirements:** 
  * Routers: $\ge 90\%$ coverage.
  * Core Scoring: $\ge 90\%$ coverage.
  * Services: $\ge 75\%$ coverage.
  * Total Backend Coverage target: $\ge 80\%$.

### 1.2 Integration Workflow Tests (`tests/integration`)
* **Scope:** Tests the end-to-end patient workflow, verifying coordinate transformations, file generation in `video_service`, background processing execution, scoring, and data persistence.
* **Environment:** Executes against a running PostgreSQL container inside Docker Compose.

### 1.3 End-to-End (E2E) & UI Verification (`tests/e2e`)
* **Scope:** Simulates clinicians navigating the dashboard, reviewing patient records, visualising radar charts, and submitting diagnostic judgments.

---

## 2. Test Execution

### Running the Entire Containerized Suite (Recommended)
This runs unit, API, and integration workflows inside a clean Docker sandbox matching our production setup:
```bash
docker compose -f tests/docker-compose.test.yml up --build --exit-code-from test-runner
```

### Running Unit and API Tests Locally
Ensure you have activated your virtual environment, and run:
```bash
cd backend
pytest -v ../tests/backend
```

To run a specific test file:
```bash
pytest ../tests/backend/test_children.py
```

---

## 3. Test Coverage Audits

To generate a local coverage report and audit which paths are missing coverage:
```bash
cd backend
pytest --cov=. --cov-report=term-missing ../tests/backend
```

This will output:
* A summary table by file.
* Specific line numbers of code paths that were not executed during the tests.

---

## 4. Manual Verification Process

To manually verify the API endpoints and check behavior:

1. **Start the API Server:**
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```
2. **Access Swagger UI:**
   Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser. You can interactively trigger endpoints (e.g. create children, upload mock sessions) and review the JSON response structures.
3. **Inspect Database:**
   Use any PostgreSQL client (e.g., pgAdmin, DBeaver) or CLI (`psql`) to verify tables and rows are being updated correctly.
