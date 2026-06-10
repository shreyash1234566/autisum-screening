# Test Execution Evidence

This document records the exact test suite execution details, test counts, and raw terminal logs captured at timestamp: 2026-06-10T20:04:00Z.

---

## 1. Execution Summary

* **Exact Command Executed:**
  ```bash
  docker compose -f tests/docker-compose.test.yml up --build --exit-code-from test-runner
  ```
* **Execution Timestamp:** 2026-06-10T20:03:52Z
* **Total Test Count:** 37
* **Passed:** 37
* **Failed:** 0
* **Skipped:** 0

---

## 2. Raw Terminal Log Output

```text
test-runner-1   | platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/bin/python3.11
test-runner-1   | cachedir: .pytest_cache
test-runner-1   | rootdir: /tests
test-runner-1   | plugins: asyncio-1.4.0, cov-7.1.0, anyio-4.13.0
test-runner-1   | asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
test-runner-1   | collecting ... collected 37 items
test-runner-1   | 
test-runner-1   | ../tests/backend/test_children.py::test_register_child_success PASSED    [  2%]
test-runner-1   | ../tests/backend/test_children.py::test_register_child_invalid_doctor PASSED [  5%]
test-runner-1   | ../tests/backend/test_children.py::test_register_child_null_doctor PASSED [  8%]
test-runner-1   | ../tests/backend/test_children.py::test_register_child_existing_id PASSED [ 10%]
test-runner-1   | ../tests/backend/test_children.py::test_register_child_missing_fields PASSED [ 13%]
test-runner-1   | ../tests/backend/test_children.py::test_get_child_success PASSED         [ 16%]
test-runner-1   | ../tests/backend/test_children.py::test_get_child_not_found PASSED       [ 18%]
test-runner-1   | ../tests/backend/test_children.py::test_register_child_negative_age PASSED [ 21%]
test-runner-1   | ../tests/backend/test_children.py::test_register_child_huge_age PASSED   [ 24%]
test-runner-1   | ../tests/backend/test_children.py::test_register_child_invalid_language PASSED [ 27%]
test-runner-1   | ../tests/backend/test_children.py::test_register_child_empty_name PASSED [ 29%]
test-runner-1   | ../tests/backend/test_children.py::test_register_child_whitespace_name PASSED [ 32%]
test-runner-1   | ../tests/backend/test_doctor.py::test_get_flagged_sessions PASSED        [ 35%]
test-runner-1   | ../tests/backend/test_doctor.py::test_get_all_sessions PASSED            [ 37%]
test-runner-1   | ../tests/backend/test_doctor.py::test_submit_judgment_success PASSED     [ 40%]
test-runner-1   | ../tests/backend/test_doctor.py::test_submit_judgment_invalid_choice PASSED [ 43%]
test-runner-1   | ../tests/backend/test_doctor.py::test_submit_judgment_session_not_found PASSED [ 45%]
test-runner-1   | ../tests/backend/test_sessions.py::test_scoring_math PASSED              [ 48%]
test-runner-1   | ../tests/backend/test_sessions.py::test_upload_session_success PASSED    [ 51%]
test-runner-1   | ../tests/backend/test_sessions.py::test_upload_session_invalid_child PASSED [ 54%]
test-runner-1   | ../tests/backend/test_sessions.py::test_upload_session_duplicate_id PASSED [ 56%]
test-runner-1   | ../tests/backend/test_sessions.py::test_upload_session_invalid_timestamp PASSED [ 59%]
test-runner-1   | ../tests/backend/test_sessions.py::test_process_session_fallback_missing_video PASSED [ 62%]
test-runner-1   | ../tests/backend/test_sessions.py::test_openface_fallback_mock PASSED    [ 64%]
test-runner-1   | ../tests/backend/test_sessions.py::test_openface_parser_success PASSED   [ 67%]
test-runner-1   | ../tests/backend/test_sessions.py::test_get_session_details PASSED       [ 70%]
test-runner-1   | ../tests/backend/test_sessions.py::test_upload_session_missing_child_id PASSED [ 72%]
test-runner-1   | ../tests/backend/test_sessions.py::test_upload_session_empty_payload PASSED [ 75%]
test-runner-1   | ../tests/backend/test_sessions.py::test_get_session_not_found PASSED     [ 78%]
test-runner-1   | ../tests/backend/test_sessions.py::test_upload_session_indt_asd PASSED   [ 81%]
test-runner-1   | ../tests/backend/test_sessions.py::test_video_service PASSED             [ 83%]
test-runner-1   | ../tests/backend/test_sessions.py::test_scoring_service_edge_cases PASSED [ 86%]
test-runner-1   | ../tests/backend/test_sessions.py::test_scoring_service_normal PASSED    [ 89%]
test-runner-1   | ../tests/backend/test_sessions.py::test_process_session_exception_handling PASSED [ 91%]
test-runner-1   | ../tests/backend/test_sessions.py::test_asdmotion_service_errors PASSED  [ 94%]
test-runner-1   | ../tests/backend/test_sessions.py::test_upload_session_invalid_session_id_format PASSED [ 97%]
backend-test-1  | INFO:     172.21.0.4:48754 - "POST /children HTTP/1.1" 200 OK
backend-test-1  | 2026-06-10 14:33:49,508 INFO services.video_service — Video saved: /tmp/videos/session-integration-1781102029/session.mp4 (0 KB)
backend-test-1  | INFO:     172.21.0.4:48754 - "POST /sessions/upload HTTP/1.1" 200 OK
backend-test-1  | 2026-06-10 14:33:49,524 WARNING services.openface_service — OpenFace binary not found. Install: pip install openface-test && openface download
backend-test-1  | 2026-06-10 14:33:49,524 WARNING services.openface_service — Using mock OpenFace result — install OpenFace for real analysis
backend-test-1  | 2026-06-10 14:33:49,524 WARNING services.asdmotion_service — ASDMotion not found. Clone: git clone https://github.com/Dinstein-Lab/ASDMotion to /opt/ASDMotion
backend-test-1  | 2026-06-10 14:33:49,524 WARNING services.asdmotion_service — Using mock ASDMotion — clone repo for real detection
backend-test-1  | 2026-06-10 14:33:49,527 INFO services.scoring_service — Session session-integration-1781102029 scored: combined=0.780 level=high flagged=True
backend-test-1  | INFO:     172.21.0.4:48754 - "GET /sessions/session-integration-1781102029 HTTP/1.1" 200 OK
backend-test-1  | 2026-06-10 14:33:49,531 INFO routers.sessions — Session session-integration-1781102029 processed (completed_fallback): high
backend-test-1  | INFO:     172.21.0.4:48754 - "GET /sessions/session-integration-1781102029 HTTP/1.1" 200 OK
backend-test-1  | INFO:     172.21.0.4:48754 - "POST /doctor/session-integration-1781102029/judgment HTTP/1.1" 200 OK
backend-test-1  | INFO:     172.21.0.4:48754 - "GET /doctor/flagged HTTP/1.1" 200 OK
test-runner-1   | ../tests/integration/test_workflow.py::test_full_patient_workflow PASSED [100%]
test-runner-1   | 
test-runner-1   | =============================== warnings summary ===============================
test-runner-1   | ../usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:284
test-runner-1   | ../usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:284
test-runner-1   | ../usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:284
test-runner-1   |   /usr/local/lib/python3.11/site-packages/pydantic/_internal/_config.py:284: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.7/migration/
test-runner-1   |     warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)
test-runner-1   | 
test-runner-1   | -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
test-runner-1   | ======================== 37 passed, 3 warnings in 4.48s ========================
```
