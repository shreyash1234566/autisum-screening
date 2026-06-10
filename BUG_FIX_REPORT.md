# AutiScreen Production Hardening & Bug Fix Report

This document outlines the bugs resolved, their root causes, implementation details, testing coverage, and remaining risks.

---

## 1. Child Registration Doctor Validation

### Bug Description & Root Cause
When registering a child with a non-existent `doctor_id`, the SQLite database context (used during unit testing) succeeded because SQLite does not enforce foreign key constraints by default. However, in production PostgreSQL, it raised an `IntegrityError` (ForeignKeyViolation) and crashed the request with an internal 500 error.

### Code Fix
Updated `backend/routers/children.py` to query the `Doctor` table. If `doctor_id` is supplied but the referenced record is not found, we raise a clean `HTTPException(400, "Doctor not found")` instead of letting it reach the database insert stage.

### Tests Added
- `test_register_child_invalid_doctor`: Verifies registration fails with a 400 when an invalid doctor ID is supplied.
- `test_register_child_null_doctor`: Verifies registration succeeds when doctor ID is `None` (since the column is nullable).
- Adjusted `test_register_child_success` to seed `doc_123` beforehand.

---

## 2. API-Level Validations for Session Uploads

### Bug Description & Root Cause
Uploading a session with an invalid/missing `child_id` triggered a database `IntegrityError` on PostgreSQL due to foreign key constraints. Similarly, a duplicate `session_id` triggered unique constraint violations, and invalid `started_at` format triggered parsing crashes. All of these led to unhandled 500 crashes.

### Code Fix
Updated `backend/routers/sessions.py`'s `upload_session`:
1. Checked for `child_id` presence and queried the `Child` table. If the child is not found, returns `400 Child not found`.
2. Checked for duplicate `session_id`. If duplicate, returns `400 Session already exists`.
3. Wrapped `started_at` in a `try-except` block. If parsing fails, returns `400 Invalid started_at ISO format`.

### Tests Added
- `test_upload_session_invalid_child`
- `test_upload_session_duplicate_id`
- `test_upload_session_invalid_timestamp`

---

## 3. OpenFace & ASDMotion Service Return Contracts

### Bug Description & Root Cause
When a video path is absent or unreadable, `run_openface` logged an error and returned `None` instead of the fallback mock result. Additionally, when ASDMotion encountered errors or timeouts, it returned a dictionary missing the `repetitive_score` key, which then crashed scoring logic.

### Code Fix
- **OpenFace**: Refactored `run_openface` in `backend/services/openface_service.py` so that any failure (missing file, non-zero return code, subprocess timeout, empty CSV output) consistently warns and returns `_mock_openface_result()` instead of `None`.
- **ASDMotion**: Refactored `run_asdmotion` in `backend/services/asdmotion_service.py` to return the `_mock_asdmotion()` dictionary populated with error details under the `error` key on any failure.
- **Scoring**: Refactored `_parse_openface_csv` to ensure standard float fields like `expression_rate`, `mean_au6`, and `mean_au12` default to `0.0` when no confident frames are parsed.

### Tests Added
- Covered implicitly by existing OpenFace tests and background fallback tests.

---

## 4. Graceful Session Fallback Degradation

### Bug Description & Root Cause
Sessions that failed media processing or were processed entirely using fallbacks were indistinguishable from successfully processed real media sessions.

### Code Fix
1. Added a `processing_note` column to the `Session` model.
2. Implemented database migration logic for PostgreSQL in `backend/database.py` to append `processing_note` on startup (safeguarding against persistent Docker DB volumes that skip initialization).
3. Updated background task `_process_session` to check if `video_path` is missing or unreadable, or if any analysis services fell back to mocks. If so, it sets:
   - `processing_status = "completed_fallback"`
   - `processing_note = "Fallback processing used. Reason: ..."`
4. Updated `get_session` response mapping to return both `processing_note` and `processing_error`.

### Tests Added
- `test_process_session_fallback_missing_video`: Verifies background processor sets status to `completed_fallback` and populates the reason in `processing_note` when video path is missing.
- Updated `test_full_patient_workflow` to poll and expect `completed_fallback` or `done` during test execution (since test runners lack ML binaries).

---

## 5. Validation Results
All **22 tests** (16 existing + 6 new regression/negative tests) passed successfully on SQLite and PostgreSQL.

---

## 6. Remaining Risks
- **Subprocess Resources**: Subprocess calls use a timeout limit (300s/600s). In heavily constrained environments, timeouts can still occur, but will now fall back gracefully instead of crashing the pipeline.
