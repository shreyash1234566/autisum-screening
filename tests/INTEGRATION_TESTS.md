# Integration and E2E Testing Guide

This document describes the testing strategy, setup, and execution guidelines for validating multi-step workflows and browser automations using **Pytest** and **Playwright**.

---

## 1. Directory Structure

All integration and E2E browser tests are stored in `tests/integration/` and `tests/e2e/`.

```
tests/
├── docker-compose.test.yml # Isolated service orchestration for test pipelines
├── integration/
│   └── test_workflow.py    # Pytest workflow: Child -> Upload -> Score -> DB Verify
└── e2e/
    ├── playwright.config.js # Browser viewport and routing configurations
    └── dashboard.spec.js   # Playwright E2E browser scripts
```

---

## 2. End-to-End Workflow Integration

Integration tests verify database persistence across boundaries. Instead of testing endpoints in isolation, `tests/integration/test_workflow.py` executes:

```
[Create Child] (POST /children)
      │
      ▼
[Upload Session] (POST /sessions/upload with JSON payload & dummy video)
      │
      ▼
[Process Video] (Triggers mock OpenFace/ASDMotion wrappers)
      │
      ▼
[Verify Database Metrics] (Polls GET /sessions/{id} for calculations)
      │
      ▼
[Doctor Review] (POST /doctor/{id}/judgment clinical update)
      │
      ▼
[Final DB State Check] (Confirm review status, notes, & timestamp persistence)
```

---

## 3. Playwright E2E Setup

Playwright runs browser scripts to test UI elements, route configurations, click events, and data inputs.

### Playwright Config (`playwright.config.js`)
```javascript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: process.env.TEST_BASE_URL || "http://localhost:3000",
    browserName: "chromium",
    headless: true,
    viewport: { width: 1280, height: 720 },
  },
});
```

### E2E Test Case (`dashboard.spec.js`)
Navigates to the dashboard, selects a flagged case, verifies that scores render, inputs clinical notes, and saves the judgment.

---

## 4. Compose Testing Runner (`docker-compose.test.yml`)

We orchestrate an isolated container pipeline to run these tests automatically:

```yaml
version: "3.9"

services:
  db-test:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: autism_test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"

  backend-test:
    build: ../backend
    ports:
      - "8001:8000"
    environment:
      DATABASE_URL: postgresql://test_user:test_password@db-test:5432/autism_test_db
      VIDEO_STORAGE_PATH: /tmp/videos
      OPENFACE_BIN: /usr/local/bin/FeatureExtraction
      ASDMOTION_PATH: /opt/ASDMotion
    depends_on:
      db-test:
        condition: service_healthy

  test-runner:
    build: ../backend
    environment:
      API_BASE_URL: http://backend-test:8000
    depends_on:
      - backend-test
    command: pytest /tests/integration/ -v
```

---

## 5. Execution Commands

### Run composing tests (CI pipeline)
```bash
docker compose -f tests/docker-compose.test.yml up --build --exit-code-from test-runner
```

### Run Playwright E2E browser tests locally
Ensure the dashboard application is running on port 3000.
```bash
npx playwright test --config=tests/e2e/playwright.config.js
```
