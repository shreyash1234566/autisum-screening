# PR-Ready Release Checklist

This document details the branch configurations, commit hashes, files modified, and the recommended sequence for creating and merging GitHub Pull Requests.

---

## 1. Branch Coordinates & Commit Hashes

| Branch Role | Target Branch Name | Head Commit Hash | Description |
| :--- | :--- | :--- | :--- |
| **QA, Tests, & Code Fixes** | `test/coverage-and-quality` | `9e66d38dfc7a72635905d45d8b74681643c5b2c7` | Integrates code validations, SQLite/PostgreSQL schemas, and the 37 pytest cases. |
| **Documentation & Auditing** | `docs/repository-hardening` | `32f17326df2b8fdebe9cb2292f7e7161e1b80c35` | Integrates all manuals, API reference schemas, sequence diagrams, and verification reports. |
| **Production Target** | `main` | `13b79730594391696dfd5be617c59c445695029a` | Standard target branch. |

---

## 2. File Change Lists

### 2.1 Branch: `test/coverage-and-quality` (Changes relative to `main`)
* **CI/CD Configuration:**
  * `.github/workflows/ci.yml`
  * `.gitignore`
* **Reports:**
  * `BUG_FIX_REPORT.md`
  * `COVERAGE_REPORT.md`
  * `DEPENDENCY_AUDIT.md`
  * `REPOSITORY_AUDIT_REPORT.md`
  * `SECURITY_REVIEW.md`
  * `STATIC_ANALYSIS_REPORT.md`
  * `TEST_EXECUTION_REPORT.md`
* **Backend Code & Configuration:**
  * `backend/database.py`
  * `backend/ml/questionnaire_classifier.py`
  * `backend/ml/train_model.py`
  * `backend/requirements.txt`
  * `backend/routers/children.py`
  * `backend/routers/doctor.py`
  * `backend/routers/sessions.py`
  * `backend/services/asdmotion_service.py`
  * `backend/services/openface_service.py`
  * `backend/services/scoring_service.py`
  * `backend/services/video_service.py`
  * `database/schema.sql`
  * `mobile/android/app/build.gradle`
  * `mobile/android/app/src/main/java/io/flutter/plugins/GeneratedPluginRegistrant.java`
  * `mobile/android/gradle.properties`
* **Test Suites:**
  * `tests/BACKEND_TESTS.md`
  * `tests/FRONTEND_TESTS.md`
  * `tests/INTEGRATION_TESTS.md`
  * `tests/TEST_MATRIX.md`
  * `tests/TEST_PLAN.md`
  * `tests/backend/conftest.py`
  * `tests/backend/test_children.py`
  * `tests/backend/test_doctor.py`
  * `tests/backend/test_sessions.py`
  * `tests/docker-compose.test.yml`
  * `tests/e2e/dashboard.spec.js`
  * `tests/e2e/playwright.config.js`
  * `tests/frontend/App.test.jsx`
  * `tests/frontend/CaseList.test.jsx`
  * `tests/frontend/SessionDetail.test.jsx`
  * `tests/frontend/setup.js`
  * `tests/integration/test_workflow.py`

### 2.2 Branch: `docs/repository-hardening` (Changes relative to `test/coverage-and-quality`)
* **Newly Created Audits & Status Checks:**
  * `VERIFICATION_GIT_STATUS.md`
  * `REPOSITORY_HYGIENE_REPORT.md`
  * `DOCUMENTATION_AUDIT.md`
  * `TEST_EXECUTION_EVIDENCE.md`
  * `COVERAGE_EVIDENCE.md`
  * `STATIC_ANALYSIS_EVIDENCE.md`
  * `SECURITY_VALIDATION.md`
  * `ARCHITECTURE_CONSISTENCY_REPORT.md`
  * `FINAL_RELEASE_GATE.md`
* **Developer References:**
  * `PROJECT_ARCHITECTURE_AUDIT.md`
  * `README.md`
  * `backend/README.md`
  * `tests/README.md`
  * `docs/API_FLOW.md`
  * `docs/API_REFERENCE.md`
  * `docs/CONTRIBUTING.md`
  * `docs/DATABASE_SCHEMA.md`
  * `docs/DEVELOPMENT_GUIDE.md`
  * `docs/ONBOARDING.md`
  * `docs/SYSTEM_ARCHITECTURE.md`
  * `docs/TESTING_GUIDE.md`

---

## 3. Recommended PR Creation & Merging Order

We recommend creating and merging PRs sequentially to separate functional code reviews from documentation additions:

### PR #1: Merge `test/coverage-and-quality` into `main`
* **Purpose:** Integrates code changes, negative input validation logic, schema startup migrations, and the full automated testing suite.
* **Why First:** Confirms that the CI pipeline compiles, executes, and checks out all 37 test vectors successfully against production parameters.

### PR #2: Merge `docs/repository-hardening` into `main`
* **Purpose:** Integrates the Project Audit, API reference tables, ER database schema mappings, flow sequence graphs, and local setup scripts.
* **Why Second:** Once the code is stable and approved, the complete documentation is integrated to align developer onboarding instructions with the latest revision.
