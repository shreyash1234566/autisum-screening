# AutiScreen API Reference

This document provides a comprehensive reference of all endpoints exposed by the AutiScreen Backend API server (running by default at `http://127.0.0.1:8000`).

---

## 1. Authentication and Global Settings
Currently, all endpoints in this developer build are unauthenticated to simplify integration. Standard HTTP headers should include:
* `Content-Type: application/json` (except for multi-part file uploads)

---

## 2. Children Management Endpoints

### Register a Child
* **Endpoint:** `POST /children`
* **Content-Type:** `application/json`
* **Request Body Schema (`ChildCreate`):**
  | Field | Type | Required | Description / Constraints |
  | :--- | :--- | :--- | :--- |
  | `id` | string | No | Unique identifier (UUID). Auto-generated if omitted. |
  | `name` | string | Yes | The child's name. Must be non-empty and not just whitespace. |
  | `age_months` | integer | Yes | Age in months. Must be between `1` and `120` (inclusive). |
  | `gender` | string | Yes | e.g. `M` or `F`. |
  | `language` | string | No | ISO code of preferred language. Default `en`. Must be a clinically supported language code. |
  | `doctor_id` | string | No | Reference to the assigned doctor. Must be a valid UUID existing in the doctors database. |

*Supported Language Codes:* `en`, `hi`, `ta`, `te`, `kn`, `ml`, `mr`, `gu`, `pa`, `bn`, `or`, `as`.

* **Success Response (200 OK):**
  ```json
  {
    "id": "e0b2a3cd-d9e1-4b1d-8524-ccb912f27568",
    "name": "Jane Doe",
    "age_months": 24,
    "gender": "F",
    "language": "en",
    "doctor_id": "893c5d6c-6cb4-49c0-827c-3f415bf3c39c"
  }
  ```
* **Error Responses:**
  * `400 Bad Request`: Validation errors (e.g. invalid language, name empty, invalid age range, or doctor ID not found).
  ```json
  {
    "detail": "Language 'fr' is not supported"
  }
  ```

---

### Get Child by ID
* **Endpoint:** `GET /children/{id}`
* **Success Response (200 OK):**
  ```json
  {
    "id": "e0b2a3cd-d9e1-4b1d-8524-ccb912f27568",
    "name": "Jane Doe",
    "age_months": 24,
    "gender": "F",
    "language": "en",
    "doctor_id": "893c5d6c-6cb4-49c0-827c-3f415bf3c39c"
  }
  ```
* **Error Responses:**
  * `404 Not Found`: Child ID not found.
  ```json
  {
    "detail": "Child not found"
  }
  ```

---

## 3. Screening Sessions Endpoints

### Upload Session Media & Diagnostics
Processes screen task events recorded from the mobile application, saves session files, and queues background processing for video features.
* **Endpoint:** `POST /sessions/upload`
* **Content-Type:** `multipart/form-data`
* **Form Parameters:**
  | Form Key | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `session_json` | File (JSON) | Yes | UTF-8 encoded text file containing the full task logs (structured schema below). |
  | `video` | File (Binary) | No | MP4 recording of the child's screen session for computer vision gaze and motor analysis. |

* **Session JSON Internal Schema Structure:**
  ```json
  {
    "session_id": "session-unique-uuid-string",
    "child_id": "child-uuid-string",
    "started_at": "2026-06-10T14:15:00Z",
    "gaze_task_a": [
      {"timestamp": 1200, "target_x": 0.5, "target_y": 0.5, "face_detected": true, "gaze_offset": 0.2}
    ],
    "gaze_task_b": [],
    "gaze_task_c": [],
    "name_trials": [
      {"trial_index": 1, "latency_ms": 1500, "responded": true}
    ],
    "bubble_events": [],
    "questionnaire_type": "mchat_r",
    "questionnaire_score": 3,
    "questionnaire_answers": {
      "q1": 0, "q2": 1, "q3": 0
    }
  }
  ```

* **Success Response (200 OK):**
  ```json
  {
    "session_id": "session-unique-uuid-string",
    "status": "accepted"
  }
  ```
* **Error Responses:**
  * `400 Bad Request`: `child_id` is missing or does not refer to a registered child, the session ID is a duplicate, or timestamp uses an invalid ISO format.

---

### Get Session Details
Retrieves status, scores, analysis results, and clinician reviews.
* **Endpoint:** `GET /sessions/{id}`
* **Success Response (200 OK):**
  ```json
  {
    "id": "session-unique-uuid-string",
    "child_id": "child-uuid-string",
    "started_at": "2026-06-10T14:15:00",
    "video_path": "/data/videos/session-unique-uuid-string/session.mp4",
    "processing_status": "completed_fallback",
    "processing_note": "video service skipped, fallback scoring applied",
    "processing_error": null,
    "risk_level": "medium",
    "combined_risk_score": 0.38,
    "flagged": true,
    "questionnaire_type": "mchat_r",
    "questionnaire_score": 3,
    "questionnaire_risk": "medium",
    "social_gaze_ratio": 0.62,
    "name_response_rate": 0.75,
    "expression_rate": 0.5,
    "repetitive_score": 0.1,
    "doctor_judgment": null,
    "doctor_notes": null,
    "doctor_reviewed_at": null
  }
  ```
* **Processing Status Transitions:** `pending` $\rightarrow$ `processing` $\rightarrow$ `done` OR `completed_fallback` (if video processing was skipped or simulated due to missing resources) OR `failed`.

---

## 4. Clinician / Doctor Review Endpoints

### Get Flagged Sessions
* **Endpoint:** `GET /doctor/flagged`
* **Description:** Retrieves all sessions flagged for immediate review (`flagged == true`), ordered by creation date descending.
* **Success Response (200 OK):**
  ```json
  [
    {
      "id": "session-unique-uuid-string",
      "child_name": "Jane Doe",
      "child_age_months": 24,
      "started_at": "2026-06-10T14:15:00",
      "risk_level": "high",
      "combined_risk_score": 0.78,
      "flagged": true,
      "processing_status": "completed_fallback",
      "questionnaire_type": "mchat_r",
      "questionnaire_score": 8,
      "questionnaire_risk": "high",
      "social_gaze_ratio": 0.32,
      "name_response_rate": 0.25,
      "expression_rate": 0.2,
      "repetitive_score": 0.8,
      "doctor_judgment": null
    }
  ]
  ```

---

### Get All Sessions
* **Endpoint:** `GET /doctor/all`
* **Query Parameters:**
  | Parameter | Type | Default | Description |
  | :--- | :--- | :--- | :--- |
  | `limit` | integer | `50` | Maximum number of session summaries to return. |
* **Success Response (200 OK):** Same list schema of `SessionSummary` objects as `/doctor/flagged`.

---

### Submit Clinical Judgment
* **Endpoint:** `POST /doctor/{session_id}/judgment`
* **Request Body Schema (`JudgmentIn`):**
  | Field | Type | Required | Description / Constraints |
  | :--- | :--- | :--- | :--- |
  | `judgment` | string | Yes | Must be one of: `typical`, `monitoring`, `high_concern`, `refer_immediately` |
  | `notes` | string | No | Optional text containing clinician notes. |

* **Success Response (200 OK):**
  ```json
  {
    "ok": true,
    "judgment": "monitoring"
  }
  ```
* **Error Responses:**
  * `404 Not Found`: Session ID does not exist.
  * `422 Unprocessable Entity`: The judgment value is not in the set of valid options.
