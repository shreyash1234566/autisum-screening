# AutiScreen Clinical Workflow & API Flow Diagrams

This document illustrates the sequence of clinical and technological steps during a child's screening lifecycle.

---

## 1. The Clinical Cycle

```mermaid
sequenceDiagram
    autonumber
    actor Clinician as Clinical Staff
    actor Child as Patient / Toddler
    participant Mobile as Mobile App (Flutter)
    participant Backend as FastAPI Server
    participant DB as PostgreSQL Database
    actor Doctor as Reviewing Doctor

    %% Phase 1: Intake & Registration
    Note over Clinician, Backend: Phase 1: Intake & Registration
    Clinician->>Backend: POST /children (Name, Age, Doctor ID)
    Backend->>DB: Save Patient Record
    Backend-->>Clinician: Return Child Profile & ID

    %% Phase 2: Interactive Session
    Note over Child, Mobile: Phase 2: Interactive Tasks
    Clinician->>Mobile: Input Child ID & Launch App
    Child->>Mobile: Completes Gaze Tasks A/B/C & Name Latency Test
    Clinician->>Mobile: Fills in M-CHAT-R Questionnaire on screen
    Mobile->>Mobile: Save video & task telemetry locally

    %% Phase 3: Data Upload & Processing
    Note over Mobile, DB: Phase 3: Telemetry Upload & Processing
    Mobile->>Backend: POST /sessions/upload (session_json file + video file)
    Backend->>DB: Save Session (status = 'pending')
    Backend->>Backend: Queue background processing task
    Backend-->>Mobile: 200 OK (Accepted)

    activate Backend
    Backend->>Backend: Run OpenFace, ASDMotion, and Scoring Algorithms
    Backend->>DB: Save calculated scores, set status = 'done', check flag conditions
    deactivate Backend

    %% Phase 4: Physician Auditing
    Note over Doctor, DB: Phase 4: Physician Auditing & Review
    Doctor->>Backend: GET /doctor/flagged (Query high-risk patients)
    Backend->>DB: Retrieve sessions where flagged = TRUE
    DB-->>Backend: Return flagged summaries
    Backend-->>Doctor: Return lists (Child details + risk levels)
    Doctor->>Backend: GET /sessions/{session_id} (Detailed analytics audit)
    Backend-->>Doctor: Return raw scoring components
    Doctor->>Backend: POST /doctor/{session_id}/judgment (Submit typical / concern rating)
    Backend->>DB: Update judgment, clinician notes, and reviewed_at timestamp
    Backend-->>Doctor: 200 OK (Saved)
```

---

## 2. API Endpoint Interaction Flow

Here is a summary of the routes invoked during this clinical lifecycle:

1. **`POST /children`**: Run at intake by nurse or clinic clerk to capture names, age, and assigned physician.
2. **`POST /sessions/upload`**: Run automatically by the tablet application once the toddler finishes tasks. Starts the background ML task immediately.
3. **`GET /doctor/flagged`**: Polled or loaded by clinicians on the web dashboard to see what reviews are pending.
4. **`GET /sessions/{session_id}`**: Triggered when a clinician clicks a patient row in the dashboard to review their radar chart and scoring profile.
5. **`POST /doctor/{session_id}/judgment`**: Saved when the clinician clicks "Submit Evaluation" on the patient's record.
