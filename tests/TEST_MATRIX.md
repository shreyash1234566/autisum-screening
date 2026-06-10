# AutiScreen Traceability and Testing Matrix

This matrix maps all core system features to their validation methods, tracking status, required mocks, and testing layers.

| Feature ID | Feature Name | Testing Layer | Automated | Mock Requirements | Validation Target | Status |
|------------|--------------|---------------|-----------|-------------------|-------------------|--------|
| **F-01** | **Child Registration** | API / Integration | Yes | None | Checks inputs, returns `201`, persists record, enforces age bounds. | Pending |
| **F-02** | **Child Query** | API | Yes | None | Querying child ID returns schema match; invalid ID returns `404`. | Pending |
| **F-03** | **Session Upload** | API / Integration | Yes | Multi-part form parser | Saves JSON payload, creates video folder, triggers backend queue. | Pending |
| **F-04** | **Background Worker** | Integration | Yes | Subprocess Mock (OpenFace & ASDMotion) | Validates queue status transitions (`pending` $\to$ `processing` $\to$ `done`). | Pending |
| **F-05** | **Gaze Risk Calculation** | Unit | Yes | None | Checks $0.45$ cut-point Youden interpolation. | Pending |
| **F-06** | **Name Response Risk** | Unit | Yes | None | Evaluates latency, checks $0.33$ and $0.67$ response bounds. | Pending |
| **F-07** | **Expression Risk** | Unit / API | Yes | OpenFace CSV parser mock | Verifies $AU6 > 1.0 \land AU12 > 1.5$ calculation and smile rates. | Pending |
| **F-08** | **Combined Risk Score** | Unit | Yes | None | Confirms formula weighting ($40\%$ Q, $30\%$ G, $20\%$ N, $10\%$ E) and flagging. | Pending |
| **F-09** | **Doctor Judgment** | API / Integration | Yes | None | Doctor POST requests write to database, add timestamps, and save notes. | Pending |
| **F-10** | **Flagged Sessions List** | API | Yes | None | Returns list of flagged sessions sorted by date descending. | Pending |
| **F-11** | **All Sessions List** | API | Yes | None | Returns sessions with pagination limits. | Pending |
| **F-12** | **OpenFace Fallback** | API / Integration | Yes | Binary FileNotFoundError simulator | Confirms system falls back to mock results on binary missing, avoiding crashes. | Pending |
| **F-13** | **Dashboard Interface** | Frontend | Yes | Axios Mock | Verifies app layout, view toggle, case click, and radar rendering. | Pending |
| **F-14** | **Native Gaze Pipeline** | Native Android | Manual | Camera simulator | Native platform channels receive gaze stream outputs. | Pending |
| **F-15** | **E2E Case Lifecycle** | E2E | Yes | None (runs on running DB) | Playwright script opens dashboard, clicks case, saves diagnostic judgment. | Pending |

---

## Technical Feasibility & Mock Definitions

### 1. Subprocess Mocking
* **Target:** `openface_service.run_openface` and `asdmotion_service.run_asdmotion`.
* **Approach:** Python's standard `unittest.mock.patch` intercepts `subprocess.run` calls. It returns pre-arranged return codes and creates temporary mock output CSV files to simulate successful execution of OpenFace binaries without requiring TBB or dlib libraries.

### 2. Database Mocking
* **Target:** SQLAlchemy database session.
* **Approach:** The fixture `db_session` overrides the FastAPI `get_db` dependency. It binds metadata schemas to an in-memory SQLite database, creating tables and providing transactional rollbacks after each test run to keep the environment clean.

### 3. Frontend HTTP Mocking
* **Target:** Axios calls to port 8000.
* **Approach:** Unit tests inside Vitest mock the Axios client or use `msw` (Mock Service Worker) to return sample JSON datasets representing flagged, typical, and processing cases.

### 4. Native Device Hardware Mocking
* **Target:** Camera input and MediaPipe results on Android.
* **Approach:** Automated unit tests verify Dart algorithms using mocked list coordinate fixtures. Direct camera hardware and Kotlin pipeline processing require physical device execution and manual verification.
