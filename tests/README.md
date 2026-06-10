# AutiScreen Testing Framework & Guide

This directory contains the automated testing pipeline for the AutiScreen platform. The tests cover multiple levels of validation, ensuring reliability, accuracy of scoring algorithms, API contracts, database integrity, and fallback mechanisms.

---

## 1. Testing Architecture

The AutiScreen testing framework is structured into four distinct layers:

### Layer 1: Infrastructure Smoke Tests
* **Objective:** Verify that Docker containers, environment variables, services, and database connections initialize correctly.
* **Scope:** Docker service startup, PostgreSQL initialization, backend/dashboard health endpoints.

### Layer 2: API (Contract & Negative) Tests
* **Objective:** Validate REST API endpoints, request schemas, validation rules, HTTP status codes, and database mutations.
* **Scope:** 
  * `POST /children`: Checks creation, unique ID generation, and validation for name (non-empty), age (1-120 months), and supported languages.
  * `GET /children/{id}`: Verifies retrieval and `404 Not Found` for invalid IDs.
  * `POST /sessions/upload`: Validates multipart file uploads, JSON payload parsing, and duplicate session checks.
  * `GET /sessions/{id}`: Verifies session structure and processing state.
  * `POST /doctor/{id}/judgment`: Validates clinical notes saving, timestamp injection, and database updates.
  * `GET /doctor/flagged` and `GET /doctor/all`: Verifies listing of sessions.

### Layer 3: Integration Workflow Tests
* **Objective:** Test end-to-end clinical workflows across components.
* **Scope:** 
  * Child Registration $\rightarrow$ Session Upload $\rightarrow$ Background ML Processing (OpenFace & ASDMotion) $\rightarrow$ Scoring Run $\rightarrow$ Database Persistence.
  * Falling back to mock processing when OpenFace binaries or media files are missing, ensuring `completed_fallback` status and appropriate scoring.

### Layer 4: E2E & Frontend Tests
* **Objective:** Validate user interfaces and browser-level interactions.
* **Scope:** Playwright and Vitest tests verifying dashboard rendering, Axios client requests, and diagnostic views.

---

## 2. Test Execution Commands

### Running via Docker (Recommended / CI Pipeline)
The entire backend, database, and test suite are containerized. To run the automated test suite inside the isolated Docker network:

```bash
docker compose -f tests/docker-compose.test.yml up --build --exit-code-from test-runner
```

This command will:
1. Spin up a temporary PostgreSQL instance.
2. Build the backend and the test runner container.
3. Execute the pytest test suite.
4. Tear down the environment and exit with the pytest exit code (allowing CI systems to capture pass/fail status).

### Running Locally (Without Docker)
If you have a local python environment with dependencies installed:

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Run pytest:
   ```bash
   pytest ../tests/backend
   ```
3. Run pytest with coverage:
   ```bash
   pytest --cov=. --cov-report=term-min=80 ../tests/backend
   ```

---

## 3. Negative Testing Coverage

We have expanded the test suite with robust negative tests to prevent runtime exceptions and malformed data from corrupting the PostgreSQL database:

* **Name Validation:** Rejects empty names, names containing only whitespace, or missing name fields.
* **Age Boundaries:** Rejects ages $\le 0$ or $> 120$ months (screening is certified for toddlers up to 10 years).
* **Language Support:** Rejects language codes not included in the supported clinical list (`en`, `hi`, `ta`, `te`, `kn`, `ml`, `mr`, `gu`, `pa`, `bn`, `or`, `as`).
* **Doctor Reference Integrity:** Verifies that registering a child referencing a non-existent `doctor_id` returns a clear `400 Bad Request` instead of throwing a raw database integrity error (500).
* **Session ID Duplication:** Uploading a session with an ID that already exists returns `400 Bad Request`.
* **Missing Media Graceful Degradation:** Simulates scenarios where media processing fails or video files are missing, ensuring the pipeline records a `completed_fallback` status and populates `processing_note` without crashing.

---

## 4. Test Matrix & Traceability

Refer to [TEST_MATRIX.md](file:///d:/Desktop/Autism-Screening/autisum-screening/tests/TEST_MATRIX.md) for a complete mapping of feature IDs, validation targets, and mock requirements.
