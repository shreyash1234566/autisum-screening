# AutiScreen Testing Plan

This document establishes the multi-layered testing strategy and methodology for the **AutiScreen** platform. It provides developers with instructions to run, configure, and expand the test suite to verify system stability, API contracts, and user workflows.

---

## 1. Testing Strategy

The AutiScreen testing strategy consists of four distinct layers of validation. Testing aims to confirm architectural functionality and regression prevention, rather than statistical verification of clinical model accuracy (which are treated as separate research problems).

```
                      +-----------------------------+
                      |   Layer 4: Frontend / E2E   |
                      |   - Playwright (E2E flows)  |
                      |   - Vitest & RTL (React)    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Layer 3: Integration Tests |
                      |  - Multi-step API Workflows |
                      |  - DB State Tracking        |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |     Layer 2: API Tests      |
                      |  - Pytest & Httpx Client    |
                      |  - Endpoint Input/Output    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Layer 1: Infrastructure     |
                      |  - Docker Compose Health    |
                      |  - Connection Smoke Tests   |
                      +-----------------------------+
```

### Scope of Testing

#### What We Test
* **API Contracts:** Route parameters, response models, schemas, and HTTP status codes.
* **Workflows:** End-to-end user journeys (e.g., Child Creation $\to$ Session Upload $\to$ Background Run $\to$ Scoring $\to$ Diagnostic Outcomes).
* **Database State Transactions:** Verification of correct row insertion, updates, indices query paths, and foreign keys.
* **Frontend View Rendering:** Render states, loading indicators, case selections, and local form submissions.
* **Pipeline Fallbacks:** Proper mock execution if the OpenFace or ASDMotion binaries are missing.

#### What We Do NOT Test (Out of Scope for MVP Verification)
* **OpenFace Facial Landmark Accuracy:** We assume the underlying open-source OpenFace binary behaves correctly.
* **ASDMotion Deep Learning Models:** We assume the Dinstein Lab classifier scripts are correct.
* **Random Forest Prediction Accuracy:** We train and test the model using historical cross-validation, but do not test classification accuracy inside the integration loop.
* **Medical Correctness:** Diagnostics remain clinical support variables. Verification targets code processing rather than clinical judgment correctness.

---

## 2. Infrastructure Setup & Requirements

Tests can run in local isolation or within the Docker environment.

### Backend Requirements (Pytest Suite)
* **Python Runtime:** Python 3.11+
* **Dependencies:** `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`, `sqlalchemy`.
* **Database Mocking:** SQLAlchemy engine overrides to direct data transactions to an in-memory SQLite backend (`sqlite:///:memory:`), avoiding dependency on a running PostgreSQL container during unit testing.

### Frontend Requirements (Vitest & RTL)
* **NodeJS Runtime:** Node 20+
* **Dependencies:** `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`, `msw` (Mock Service Worker for API mocking).

### E2E Requirements (Playwright)
* **Engine:** Playwright browser binaries (Chromium, Firefox, WebKit).
* **Target Host:** Configurable environment variable pointing to the target deployment (default: `http://localhost:3000`).

---

## 3. Test Directory Structure

All testing scripts, configuration files, and mocks are kept isolated from production code within the `/tests` folder.

```
autiscreen-app/
├── tests/
│   ├── TEST_PLAN.md            # Testing methodology and guide
│   ├── TEST_MATRIX.md          # Traceability matrix mapping features to test types
│   ├── BACKEND_TESTS.md        # Technical guide for Pytest backend suites
│   ├── FRONTEND_TESTS.md       # Technical guide for Vitest frontend suites
│   ├── INTEGRATION_TESTS.md    # Technical guide for workflow integration tests
│   │
│   ├── docker-compose.test.yml # Docker config to execute isolated test pipelines
│   │
│   ├── backend/                # Pytest suites
│   │   ├── conftest.py         # Global pytest fixtures, DB setup overrides
│   │   ├── test_children.py    # Child profile tests
│   │   ├── test_doctor.py      # Doctor dashboard endpoint tests
│   │   └── test_sessions.py    # Session creation, upload, and scoring tests
│   │
│   ├── frontend/               # Vitest + React Testing Library suites
│   │   ├── setup.js            # RTL global configuration
│   │   ├── App.test.jsx        # Sidebar, views, and layout tests
│   │   ├── CaseList.test.jsx   # List rendering and badge color tests
│   │   └── SessionDetail.test.jsx # Charts, values, and diagnostic form tests
│   │
│   ├── integration/            # Multi-step integration tests
│   │   └── test_workflow.py    # Child -> Upload -> Processing -> Scoring -> DB -> Judgment
│   │
│   └── e2e/                    # Playwright automation tests
│       └── dashboard.spec.js   # Browser E2E smoke tests
```

---

## 4. How to Execute Tests

### Docker-Based Execution (Recommended)
You can run the entire testing pipeline inside isolated containers using the dedicated test compose configuration:

```bash
# Build and execute all tests (Backend unit + integration, Frontend unit)
docker compose -f tests/docker-compose.test.yml up --build --exit-code-from test-runner
```

### Local Manual Execution

#### 1. Backend Tests (Pytest)
Ensure you have activated your virtual environment and installed the dependencies inside `backend/requirements.txt`.

```bash
# Navigate to the backend directory
cd backend

# Execute pytest with coverage tracking
pytest ../tests/backend/ -v --cov=. --cov-report=term-missing
```

#### 2. Frontend Tests (Vitest)
Ensure you have installed node dependencies inside the `dashboard/` directory.

```bash
# Navigate to dashboard directory
cd dashboard

# Run Vitest in watch mode
npm run test

# Run Vitest and output coverage report
npm run test:coverage
```

#### 3. E2E Browser Tests (Playwright)
Install Playwright test tools and execute:

```bash
# Install Playwright browser engines
npx playwright install

# Execute browser automation tests
npx playwright test --config=tests/e2e/playwright.config.js
```
