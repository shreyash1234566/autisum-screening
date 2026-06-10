# Project Architecture Audit: AutiScreen

This document provides a highly technical, end-to-end architectural audit of the **AutiScreen** repository. It is designed to serve as a comprehensive reference for onboarding developers, technical architects, and system administrators, enabling them to understand the system's design, code patterns, data flows, scoring formulas, dependencies, bugs, and roadmap without reading the entire codebase.

---

## 1. Repository Overview

### Project Purpose
AutiScreen is an India-focused, clinical-support screening platform for Autism Spectrum Disorder (ASD) in toddlers and children. It aims to bridge the gap between expensive, resource-intensive diagnostic procedures and accessible early-screening options. By combining standardized clinical questionnaires (M-CHAT-R for ages 16–30 months, AIIMS INDT-ASD for ages >30 months) with computer vision and machine learning (on-device eye-tracking via MediaPipe, and server-side facial expression and repetitive movement analysis via OpenFace and ASDMotion), the system flags high-risk cases for clinician review.

### Current State
* **Mobile (Flutter & Native Kotlin):** Provides the child-facing interaction screens (visual stimuli, audio cues, games) and runs native on-device face mesh tracking. However, it is in a **partially broken state** due to missing native camera-to-MediaPipe plumbing (meaning no gaze tracking frames are populated) and a critical crash on upload when video files are absent.
* **Backend (FastAPI):** Exposes a REST API to register children, accept session uploads, and query case lists. A background task runs OpenFace and ASDMotion on uploaded videos, falling back to mock outputs if the binary is missing. It is in a **partially functional state** due to dependencies on binaries that are not installed in the docker container.
* **Dashboard (React):** A single-page application for doctors to review flagged sessions, inspect radar charts of behavioral scores, and log clinical judgments. It is **functional but unauthenticated**, with minor production-build configuration issues.

### Architectural Style
AutiScreen implements a **Client-Server/Distributed Pipelines** pattern:
1. **Client Tier (Mobile App):** Orchestrates child stimuli, collects user touch events, and computes real-time eye-tracking / head-orientation coordinates on-device, writing them to a JSON session model.
2. **Database Tier (PostgreSQL):** Stores relational child details, doctor credentials, raw behavior telemetry, calculated metrics, and clinical outcomes.
3. **Application & Processing Tier (FastAPI & Subprocesses):** Acts as the central web server. It handles uploads, persists database records, and triggers synchronous CV/ML subprocess pipelines for deep video analysis.
4. **Presentation Tier (React Web):** Connects to the FastAPI endpoints to render patient lists, behavioral graphs, and capture diagnostic outcomes.

```
                  +-----------------------------------+
                  |      Flutter Mobile App           |
                  |  - MediaPipe Gaze/Blink Tracking  |
                  |  - Interactive Tasks (A, B, C, D) |
                  +-----------------+-----------------+
                                    |
                                    | Encrypted JSON Payload
                                    | & Session Video (MP4)
                                    v
                  +-----------------------------------+
                  |      FastAPI Web Server           |
                  |  - Child / Session Management     |
                  |  - Background Task Queue          |
                  +--------+-----------------+--------+
                           |                 |
            Spawns Subproc |                 | ORM (SQLAlchemy)
                           v                 v
  +--------------------------------+   +-----------------------+
  |  CV & Scoring Pipeline         |   | PostgreSQL Database   |
  |  - OpenFace (Smile Detection)  |   | - doctors, children,  |
  |  - ASDMotion (Stereotypy)      |   |   sessions tables     |
  |  - Random Forest Classifiers   |   +-----------------------+
  +--------------------------------+               ^
                                                   | Read / Update
                                                   | Judgments
                                       +-----------+-----------+
                                       | React Doctor Dashboard|
                                       | - Recharts Radar Graph|
                                       | - Diagnostic Labels   |
                                       +-----------------------+
```

### Technology Stack
* **Mobile Client:** Flutter (3.x/Dart), Native Android Kotlin (targeting SDK 36 / Android 16), MediaPipe Face Landmarker (0.10.26), Google Text-To-Speech.
* **Doctor Dashboard:** React (v18), Axios, Recharts, TailwindCSS, date-fns, served via Nginx.
* **Backend Server:** FastAPI (0.111.0), Uvicorn (0.30.1), SQLAlchemy (2.0.30), PostgreSQL (15), Pydantic Settings (2.3.1), Python-dotenv, Python-Jose (for security).
* **Machine Learning / CV:** Scikit-Learn (1.5.0), Pandas (2.2.2), NumPy (1.26.4), OpenCV (opencv-python-headless 4.9.0.80), OpenFace 3.0, ASDMotion.

---

## 2. Folder Structure Analysis

The repository is organized into five primary subdirectories, separating responsibilities cleanly between the client, backend, database, ML training, and front-end dashboard.

### Root Files
* [docker-compose.yml](file:///d:/Desktop/Autism-Screening/autisum-screening/docker-compose.yml): Configures containerized services (`db`, `backend`, `dashboard`) and maps shared volumes for persistent PostgreSQL data (`pgdata`) and video storage (`videodata`).
* [.env](file:///d:/Desktop/Autism-Screening/autisum-screening/.env): Stores environmental overrides for DB URLs, path variables, secrets, and binary paths.
* [buildlog.txt](file:///d:/Desktop/Autism-Screening/autisum-screening/buildlog.txt): UTF-16LE log file recording a failed Docker build caused by missing pip packages.

---

### Folder: `backend/`
Contains the FastAPI backend server, configuration, database models, API routing, and scoring pipelines.

* **Major Files:**
  * [main.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/main.py): Entry point; instantiates the FastAPI application, sets up CORS rules, and mounts child/doctor/session routers.
  * [config.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/config.py): Core settings manager implementing `pydantic_settings.BaseSettings` to load environment variables.
  * [database.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/database.py): Initializes the SQLAlchemy database engine (`pool_pre_ping=True`), constructs the declarative base (`Base`), and defines the ORM models: `Child`, `Session`, and `Doctor`.
  * [Dockerfile](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/Dockerfile): Builds the Python 3.11-slim container. Installs basic system utilities (`cmake`, `git`, `wget`, `libgl1`) and dependencies in `requirements.txt`.
* **Dependencies:** `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `scikit-learn`, `numpy`, `pandas`, `opencv-python-headless`, `boto3` (for S3 storage), `python-jose`, `passlib` (for hashing).

#### Subfolders inside `backend/`:
* `routers/`: Exposes FastAPI route decorators mapping incoming HTTP requests to database transactions and scoring routines.
  * [children.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/children.py): Implements child profile registration (`POST /children`) and lookup (`GET /children/{id}`).
  * [doctor.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/doctor.py): Dashboard endpoints including retrieval of flagged cases (`GET /doctor/flagged`), general query (`GET /doctor/all`), and clinician diagnosis submissions (`POST /doctor/{session_id}/judgment`).
  * [sessions.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/sessions.py): Handles multipart uploads of session JSON and video file bytes (`POST /sessions/upload`), and triggers the background analysis thread `_process_session`.
* `services/`: Encapsulates CV processing wrappers, local file I/O, and the multi-signal mathematical scoring engine.
  * [video_service.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/services/video_service.py): Handles directory management and reads/writes MP4 video files inside the `/data/videos` volume.
  * [openface_service.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/services/openface_service.py): Spawns the OpenFace `FeatureExtraction` binary via `subprocess`, parses frame confidence/AU metrics, and falls back to a mock output if the executable is missing.
  * [asdmotion_service.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/services/asdmotion_service.py): Spawns the external Dinstein Lab `detect_stereotypy.py` script to look for repetitive hand-flapping or rocking, aggregating output segment scores.
  * [scoring_service.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/services/scoring_service.py): Combines inputs from questionnaire, gaze, name response, expression rate, and repetitiveness into a single weighted score.
* `ml/`: Subdirectory housing trained machine learning models, classifiers, and thresholds.
  * [scoring_thresholds.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/ml/scoring_thresholds.py): Holds clinical constants (cut-offs, weights, normalizers) extracted from published scientific papers.
  * [questionnaire_classifier.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/ml/questionnaire_classifier.py): Uses a Random Forest model on encoded feature inputs matching the UCI ASD schema.
  * [train_model.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/ml/train_model.py): Scikit-learn training script utilizing 5-fold cross-validation and saving outputs to `questionnaire_model.pkl`.

---

### Folder: `dashboard/`
Holds the React administration dashboard designed for doctor review.

* **Major Files:**
  * [Dockerfile](file:///d:/Desktop/Autism-Screening/autisum-screening/dashboard/Dockerfile): Multi-stage build compilation using `node:20-alpine` to compile assets via `npm run build`, and copies them to an `nginx:alpine` image.
  * [package.json](file:///d:/Desktop/Autism-Screening/autisum-screening/dashboard/package.json): Lists packages (`react`, `axios`, `recharts`, `react-router-dom`) and defines a dev proxy back to port 8000.
  * [src/App.jsx](file:///d:/Desktop/Autism-Screening/autisum-screening/dashboard/src/App.jsx): Main layout container; renders the sidebar list of sessions and loads detailed views.
  * [src/services/api.js](file:///d:/Desktop/Autism-Screening/autisum-screening/dashboard/src/services/api.js): Axios configuration utilizing `REACT_APP_API_URL` to point to the backend server.
* **Dependencies:** `react`, `react-dom`, `axios`, `recharts`, `date-fns`, `nginx`.

#### Subfolders inside `dashboard/src/`:
* `components/`: Component hierarchy for rendering case data:
  * [CaseList.jsx](file:///d:/Desktop/Autism-Screening/autisum-screening/dashboard/src/components/CaseList.jsx): Renders individual clinician review items with color-coded risk levels.
  * [SessionDetail.jsx](file:///d:/Desktop/Autism-Screening/autisum-screening/dashboard/src/components/SessionDetail.jsx): Structural template for the details panel containing charts, warnings, and clinical summaries.
  * [BehaviorScore.jsx](file:///d:/Desktop/Autism-Screening/autisum-screening/dashboard/src/components/BehaviorScore.jsx): Visualizes gaze, name response, expression, and repetitiveness in a Recharts `RadarChart` and matches them against standard cut-offs.
  * [QuestionnaireResult.jsx](file:///d:/Desktop/Autism-Screening/autisum-screening/dashboard/src/components/QuestionnaireResult.jsx): Shows a custom visual progress bar indicating total risk points scored on M-CHAT-R or AIIMS INDT-ASD.
  * [DoctorJudgment.jsx](file:///d:/Desktop/Autism-Screening/autisum-screening/dashboard/src/components/DoctorJudgment.jsx): Interactive form enabling doctors to input final judgments (e.g. `typical`, `monitoring`, `refer_immediately`) and submit clinical notes.

---

### Folder: `database/`
* **Major Files:**
  * [schema.sql](file:///d:/Desktop/Autism-Screening/autisum-screening/database/schema.sql): Defines standard DDL queries for `doctors`, `children`, and `sessions` tables, setting indexes and foreign key references. Used for postgres initialization.

---

### Folder: `ml/`
* **Major Files:**
  * [download_data.py](file:///d:/Desktop/Autism-Screening/autisum-screening/ml/download_data.py): Standalone dataset helper. Connects to the UCI repository, downloads ARFF data formats, and converts them to standard CSV formats inside `ml/data/`.

---

### Folder: `mobile/`
The Flutter mobile application designed for on-device patient interaction and native MediaPipe tracking.

* **Major Files:**
  * [pubspec.yaml](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/pubspec.yaml): Core Flutter configuration. Configures package permissions, application assets, and plugins.
  * [lib/main.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/main.dart): Sets orientation properties, builds the root theme, and instantiates the stateful `SessionOrchestrator` which transitions screens.
* **Dependencies:** `camera`, `google_mlkit_face_detection`, `flutter_tts`, `dio`, `shared_preferences`, `permission_handler`, `uuid`, `fl_chart`.

#### Subfolders inside `mobile/lib/`:
* `models/`: Translates client-side logic to structured Dart classes:
  * [child.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/models/child.dart): Child records and age-based screening selection algorithms.
  * [session.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/models/session.dart): Structures JSON templates for raw data logging, including `GazeDataPoint`, `NameTrialResult`, and `BubbleTouchEvent`.
  * [questionnaire.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/models/questionnaire.dart): Stores localizations and scoring rules for the clinical questions.
* `services/`: Native bridges and peripheral handlers:
  * [mediapipe_service.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/services/mediapipe_service.dart): Connects to the native Android channels to control tracking, buffers raw coordinates, and implements mathematical logic for gaze analysis.
  * [api_service.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/services/api_service.dart): A Dio wrapper executing multipart HTTP uploads to `/children` and `/sessions/upload`.
  * [tts_service.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/services/tts_service.dart): Communicates with native text-to-speech to play audio cues in English or Hindi.
* `screens/`: Application page widgets:
  * [registration_screen.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/screens/registration_screen.dart): Form capturing details about the child.
  * [consent_screen.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/screens/consent_screen.dart): Requires user to scroll to the bottom of the terms before unlocking the screening tasks.
  * [questionnaire_screen.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/screens/questionnaire_screen.dart): Renders single-select binary or Likert options.
  * [task_a_screen.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/screens/task_a_screen.dart): Gaze preference task (split social/non-social).
  * [task_b_screen.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/screens/task_b_screen.dart): Name-call tracking protocol (3 trials).
  * [task_c_screen.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/screens/task_c_screen.dart): Imitation challenge (wave and clap cues).
  * [task_d_screen.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/screens/task_d_screen.dart): Bubble popping game capturing touch interactions.
  * [session_complete_screen.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/screens/session_complete_screen.dart): Displays upload loading spinners, error dialogs, or confirmation cards.
* `constants/`: Configuration tables:
  * [app_colors.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/constants/app_colors.dart): Soft, kid-friendly color palettes and bubble paint properties.
  * [app_strings.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/constants/app_strings.dart): English and Hindi dictionary variables.
  * [task_config.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/constants/task_config.dart): Core parameters matching the backend values.
* `widgets/`:
  * [animated_character.dart](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/lib/widgets/animated_character.dart): Draws a warm, peach-skinned character using CustomPainter, executing eye blinking, bobbing, mouth gestures, and arm waving.
* `android/`: Native build files:
  * [app/src/main/kotlin/com/autism/screening/MainActivity.kt](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/android/app/src/main/kotlin/com/autism/screening/MainActivity.kt): Registers the platform MethodChannel and EventChannel. Sets window layouts to accommodate Android 16 system margins.
  * [app/src/main/kotlin/com/autism/screening/MediaPipeHandler.kt](file:///d:/Desktop/Autism-Screening/autisum-screening/mobile/android/app/src/main/kotlin/com/autism/screening/MediaPipeHandler.kt): Configures MediaPipe Face Landmarker options (confidence thresholding, async result listeners). Integrates iris coordinate extraction, head orientation geometry, and eye aspect ratio blink calculations.

---

## 3. Backend Architecture

### FastAPI Structure
The backend uses a clean routing separation with global CORS policies, centralized logger configuration, and an async database connection setup.

```
[ uvicorn ]
    │
    ▼
[ main.py (FastAPI App) ]
    │
    ├─► [ routers/children.py ] ──► [ database.py (SQLAlchemy Model) ]
    │
    ├─► [ routers/doctor.py ] ────► [ database.py (SQLAlchemy Model) ]
    │
    └─► [ routers/sessions.py ] ──► [ database.py ] ──► [ background_tasks ]
                                                              │
                                  ┌───────────────────────────┴───────────────────────────┐
                                  ▼                                                       ▼
                        [ video_service.py ]                                    [ scoring_service.py ]
                        (Save video, storage)                                   (run_full_scoring)
                                  │                                                       │
         ┌────────────────────────┴────────────────────────┐                              ├─► Gaze Ratio
         ▼                                                 ▼                              ├─► Name Rate
  [ openface_service.py ]                           [ asdmotion_service.py ]              ├─► OpenFace AU Smile
  (FeatureExtraction Subprocess)                    (detect_stereotypy.py Subproc)        ├─► ASDMotion
         │                                                 │                              └─► Questionnaire (RF)
         └────────────────────────┬────────────────────────┘
                                  v
                        [ scoring_service.py ]
```

* **Startup Flow:**
  1. The app starts via `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`.
  2. `main.py` configures Python's root logger.
  3. `database.py` evaluates the `DATABASE_URL` settings.
  4. `Base.metadata.create_all(bind=engine)` triggers automatically, compiling any tables (`doctors`, `children`, `sessions`) that do not exist in the connected database.
  5. The API routers are registered.
  6. The backend goes idle, waiting to receive REST payloads.

### API Endpoints

#### 1. Register Child
* **Route:** `POST /children`
* **Method:** `POST`
* **Request Format (JSON):**
  ```json
  {
    "id": "optional-uuid-string",
    "name": "Jane Doe",
    "age_months": 24,
    "gender": "female",
    "language": "en",
    "doctor_id": null
  }
  ```
* **Response Format (JSON):**
  ```json
  {
    "id": "generated-or-provided-uuid",
    "name": "Jane Doe",
    "age_months": 24,
    "gender": "female",
    "language": "en",
    "created_at": "2026-06-10T15:50:00.000000"
  }
  ```
* **Dependencies:** `database.get_db`, `database.Child` ORM model.

#### 2. Get Child
* **Route:** `GET /children/{child_id}`
* **Method:** `GET`
* **Response Format (JSON):** Matches the registration structure, or returns `404 Not Found` if missing.
* **Dependencies:** `database.get_db`, `database.Child` ORM model.

#### 3. Upload Session
* **Route:** `POST /sessions/upload`
* **Method:** `POST`
* **Request Format:** Multipart form data:
  * `session_json` (File containing stringified JSON, matches mobile telemetry formats).
  * `video` (Optional video file bytes, MP4 format).
* **Response Format (JSON):**
  ```json
  {
    "session_id": "uploaded-session-uuid",
    "status": "accepted"
  }
  ```
* **Dependencies:** `database.get_db`, `services.video_service.save_video`, `FastAPI.BackgroundTasks` for scheduling `_process_session`.

#### 4. Get Session details
* **Route:** `GET /sessions/{session_id}`
* **Method:** `GET`
* **Response Format (JSON):**
  ```json
  {
    "id": "session-uuid",
    "child_id": "child-uuid",
    "processing_status": "done",
    "risk_level": "high",
    "flagged": true,
    "combined_risk_score": 0.584,
    "social_gaze_ratio": 0.32,
    "name_response_rate": 0.33,
    "expression_rate": 0.12,
    "questionnaire_score": 8,
    "questionnaire_type": "mchat_r",
    "questionnaire_risk": "high"
  }
  ```
* **Dependencies:** `database.get_db`, `database.Session` ORM model.

#### 5. Get Flagged Sessions
* **Route:** `GET /doctor/flagged`
* **Method:** `GET`
* **Response Format (JSON Array):** Returns a list of `SessionSummary` JSON objects where the session `flagged` status is `true`, ordered by creation date descending.
* **Dependencies:** `database.get_db`, joins `Session` and `Child` tables.

#### 6. Get All Sessions
* **Route:** `GET /doctor/all`
* **Method:** `GET`
* **Request Parameters:** `limit` (default 50).
* **Response Format (JSON Array):** Returns recent session summaries.
* **Dependencies:** `database.get_db`.

#### 7. Submit Judgment
* **Route:** `POST /doctor/{session_id}/judgment`
* **Method:** `POST`
* **Request Format (JSON):**
  ```json
  {
    "judgment": "typical | monitoring | high_concern | refer_immediately",
    "notes": "Spoke with parents. Hand-flapping observed during tasks."
  }
  ```
* **Response Format (JSON):**
  ```json
  {
    "ok": true,
    "judgment": "monitoring"
  }
  ```
* **Dependencies:** `database.get_db`, `database.Session` ORM model.

---

## 4. Database Architecture

AutiScreen utilizes PostgreSQL to maintain patient data, raw telemetry, processed diagnostic metrics, and doctor inputs.

### Entity Relationship Diagram (ERD) Description
* **`doctors` (One-to-Many with `children`):** A doctor profile created upon system access. Can register and manage multiple child records.
* **`children` (One-to-Many with `sessions`):** Holds descriptive records for children (name, age in months, language, gender, and reference doctor). A child can undergo multiple screening sessions over time.
* **`sessions` (Many-to-One with `children`):** Stores raw gaze coordinate streams, touch positions, score results, logs, and clinician judgments.

```
       doctors
  +---------------+
  | id (PK)       | <---+
  | name          |     |
  | email (Unique)|     |
  | password      |     |
  | created_at    |     |
  +---------------+     |
                        | (doctor_id)
       children         |
  +---------------+     |
  | id (PK)       | <---+
  | name          |
  | age_months    |
  | gender        | <---+
  | language      |     |
  | doctor_id (FK)|     |
  | created_at    |     |
  +---------------+     |
                        | (child_id)
       sessions         |
  +---------------+     |
  | id (PK)       | <---+
  | child_id (FK) |
  | started_at    |
  | video_path    |
  | gaze_task_a   |
  | gaze_task_b   |
  | name_trials   |
  | gaze_task_c   |
  | bubble_events |
  | q_type        |
  | q_score       |
  | q_answers     |
  | q_risk        |
  | q_norm        |
  | gaze_ratio    |
  | name_rate     |
  | expr_rate     |
  | blink_rate    |
  | repetitive    |
  | comb_score    |
  | risk_level    |
  | flagged       |
  | proc_status   |
  | proc_error    |
  | doc_judgment  |
  | doc_notes     |
  | doc_reviewed  |
  +---------------+
```

### Table Schema and Indices

#### Table: `doctors`
* **`id` (VARCHAR, PK):** Primary Key identifier.
* **`name` (VARCHAR(100)):** Doctor name.
* **`email` (VARCHAR(200), Unique):** Unique email constraint used for credentials.
* **`password` (VARCHAR(200)):** Bcrypt hashed authentication credentials.
* **`created_at` (TIMESTAMP):** Defaults to `NOW()`.

#### Table: `children`
* **`id` (VARCHAR, PK):** Unique UUID.
* **`name` (VARCHAR(100), NOT NULL):** Child name.
* **`age_months` (INTEGER, NOT NULL):** Numeric age in months for cutoff calculation.
* **`gender` (VARCHAR(10)):** e.g., `male`, `female`, `other`.
* **`language` (VARCHAR(5)):** Defaults to `en`. Used to load correct strings and sound cues.
* **`doctor_id` (VARCHAR, FK):** Points to `doctors.id` (nullable).
* **`created_at` (TIMESTAMP):** Defaults to `NOW()`.

#### Table: `sessions`
* **`id` (VARCHAR, PK):** Unique UUID.
* **`child_id` (VARCHAR, NOT NULL, FK):** Points to `children.id`.
* **`started_at` (TIMESTAMP):** Creation time.
* **`video_path` (VARCHAR):** File path pointing to local encrypted video store (e.g. `/data/videos/...`).
* **`gaze_task_a`, `gaze_task_b`, `gaze_task_c` (JSONB, Default '[]'):** Contains lists of structured on-device coordinate records (timestamps, EAR, iris coords).
* **`name_trials` (JSONB, Default '[]'):** List of results from Name response trials (latencies, yaws, results).
* **`bubble_events` (JSONB, Default '[]'):** Touch logs from Task D.
* **`questionnaire_type` (VARCHAR(20)):** `mchat_r` or `indt_asd`.
* **`questionnaire_score` (INTEGER):** Total numeric score.
* **`questionnaire_answers` (JSONB, Default '{}'):** Stores key-value items mapping question IDs to responses.
* **`questionnaire_risk` (VARCHAR(10)):** `low`, `medium`, or `high`.
* **`questionnaire_norm` (FLOAT):** Normalised 0-1 scale.
* **`social_gaze_ratio` (FLOAT):** Gaze ratio scored server-side from Task A.
* **`name_response_rate` (FLOAT):** Ratio of name response matches.
* **`expression_rate` (FLOAT):** OpenFace calculated smile rate.
* **`blink_rate_bpm` (FLOAT):** Evaluated blinks per minute.
* **`repetitive_score` (FLOAT):** ASDMotion repetitiveness assessment.
* **`combined_risk_score` (FLOAT):** Combined weighted index.
* **`risk_level` (VARCHAR(10)):** Combined assessment (`low`, `medium`, `high`).
* **`flagged` (BOOLEAN, Default FALSE):** Checked `true` if combined score is `>= 0.45`.
* **`processing_status` (VARCHAR(20), Default 'pending'):** `pending`, `processing`, `done`, or `error`.
* **`processing_error` (TEXT):** Message recorded if subprocesses or calculations fail.
* **`doctor_judgment` (VARCHAR(20)):** Diagnostic label (`typical`, `monitoring`, `high_concern`, `refer_immediately`).
* **`doctor_notes` (TEXT):** Clinician logs.
* **`doctor_reviewed_at` (TIMESTAMP):** Creation timestamp when clinician submits judgment.

#### Database Indexes
To maintain responsive dashboard queries, four indexes are built on the `sessions` table:
1. **`idx_sessions_flagged` on `sessions(flagged)`:** Optimizes loading flagged cases for doctor review.
2. **`idx_sessions_child` on `sessions(child_id)`:** Speeds up historical lookups for specific children.
3. **`idx_sessions_started` on `sessions(started_at DESC)`:** Supports descending chronological query sorting.
4. **`idx_sessions_processing` on `sessions(processing_status)`:** Used to track items in the queue.

---

## 5. Session Processing Pipeline

An end-to-end data transaction flows through six sequential phases:

```
[1. Session Creation] (mobile/lib/screens/registration_screen.dart, consent_screen.dart)
         │
         ▼
[2. Task Stimuli & Telemetry Collection] (mobile/lib/screens/task_a/b/c/d_screen.dart, mediapipe_service.dart)
         │
         ▼
[3. Session Upload] (mobile/lib/services/api_service.dart ──► POST /sessions/upload)
         │
         ▼
[4. Background Queue Routing] (backend/routers/sessions.py: _process_session)
         │
         ├─► [ services/openface_service.py ] (Smile & Head Yaw Analysis)
         ├─► [ services/asdmotion_service.py ] (Repetitive Movement Scoring)
         └─► [ services/scoring_service.py ] (Aggregate multi-signal weights)
         │
         ▼
[5. Database Persistence] (backend/database.py: Session ORM commits updates)
         │
         ▼
[6. Dashboard Visualization] (dashboard/src/App.jsx, CaseList.jsx, SessionDetail.jsx)
```

1. **Session Creation:** The doctor registers the child on the mobile app. The orchestrator checks child age, selects the appropriate questionnaire, and presents consent terms.
2. **Task Stimuli and Collection:**
   * Gaze and blink data are computed at ~30 FPS on-device via native `MediaPipeHandler.kt`.
   * Task A tracks gaze preference (social left vs toy right).
   * Task B plays TTS name calls and evaluates yaw rotation.
   * Task C tracks imitation tasks (waves/claps).
   * Task D logs screen touch hits/misses.
3. **Session Upload:** Data completes. The client compiles `SessionData` and makes a Multipart HTTP POST call to `/sessions/upload` transmitting the JSON parameters and session video (MP4).
4. **Background Queue Routing:** The backend routes the files, saves the video to local storage, saves the initial session record with `processing_status="pending"`, and schedules `_process_session` on a background thread.
5. **Machine Learning & CV Processing:**
   * Status is updated to `"processing"`.
   * OpenFace processes the MP4 video, returning smile frame rates and head coordinates.
   * ASDMotion analyses the video to score repetitive behaviors.
   * `run_full_scoring` maps the results against clinical thresholds and updates the database, setting status to `"done"`. If a service fails, the error message is caught and stored, setting status to `"error"`.
6. **Dashboard Visualization:** The clinician opens the React Dashboard. It calls `/doctor/flagged` and pulls the latest scores, rendering details on radar charts, visual scorebars, and presenting fields to save notes and judgments.

---

## 6. ML and Scoring Pipeline

The scoring system aggregates questionnaire risk and behavioral observations into a unified assessment score.

### Scoring Thresholds and Research Citations

#### 1. Social Preference Gaze Ratio (Task A)
* **Citation:** Perochon et al. (2023) *"A tablet-based game for screening of autism..."* NEJM Evidence.
* **Clinical Basis:** Typical children spend a significantly higher percentage of time viewing social stimuli (human character face) compared to non-social, moving targets (spinning toys).
  * Typical gaze ratio: $\text{mean} = 0.61 \pm 0.12$
  * ASD gaze ratio: $\text{mean} = 0.38 \pm 0.14$
  * Optimal Youden J index cut-point: $0.45$
* **Algorithm (`score_gaze`):**
  * $\text{Ratio} \ge 0.55 \implies \text{Score} = 0.0$ (Low risk)
  * $\text{Ratio} \le 0.45 \implies \text{Score} = 1.0$ (High risk)
  * Between $0.45$ and $0.55$: Linear interpolation:
    $$\text{Score} = 1.0 - \frac{\text{Ratio} - 0.45}{0.55 - 0.45}$$

#### 2. Name Response Rate (Task B)
* **Citation:** Perochon et al. (2023) supplementary protocol; Bradshaw et al. (2018) *"Feasibility of an eye-tracking system..."* Autism Research.
* **Clinical Basis:** Measures head turn response within 3 seconds of a name call.
  * Typical child responds to $\ge 2/3$ trials (Response rate $\ge 0.67$).
  * ASD concern is raised if child responds to $\le 1/3$ trials (Response rate $\le 0.33$).
* **Algorithm (`score_name_response`):**
  * $\text{Response Rate} \ge 0.67 \implies \text{Score} = 0.0$ (Low risk)
  * $\text{Response Rate} \le 0.33 \implies \text{Score} = 1.0$ (High risk)
  * Between $0.33$ and $0.67$: Linear interpolation:
    $$\text{Score} = 1.0 - \frac{\text{Response Rate} - 0.33}{0.67 - 0.33}$$

#### 3. Facial Expression Rate (OpenFace AU)
* **Citation:** Ekman's Facial Action Coding System (FACS) & OpenFace documentation.
* **Clinical Basis:** Genuine social smiles (Duchenne smile) involve the contraction of both $AU6$ (Cheek Raiser, intensity $> 1.0$) and $AU12$ (Lip Corner Puller, intensity $> 1.5$). Typical children show smile expression in at least $30\%$ of social interaction frames.
* **Algorithm (`score_expression`):**
  * Evaluates frames where confidence is $\ge 0.8$.
  * Count frames where $AU6 > 1.0 \land AU12 > 1.5$ simultaneously.
  * $\text{Expression Rate} = \frac{\text{Smile Frames}}{\text{Total Configured Frames}}$
  * Risk Score:
    $$\text{Score} = \max\left(0.0, 1.0 - \frac{\text{Expression Rate}}{0.30}\right)$$

#### 4. Eye Aspect Ratio Blink Rate
* **Citation:** Soukupová & Čech (2016) *"Real-Time Eye Blink Detection..."*
* **Clinical Basis:** Measures Eye Aspect Ratio ($EAR$) to detect eye closure duration.
  $$EAR = \frac{||p_2 - p_6|| + ||p_3 - p_5||}{2 ||p_1 - p_4||}$$
* **Thresholds:**
  * $EAR < 0.20 \implies$ Closed eye (Blink).
  * Blink rate is calculated as:
    $$\text{Blink Rate (BPM)} = \frac{\text{Blinks}}{\text{Duration in Minutes}}$$
  * Typical children rate: $15 - 20 \text{ BPM}$.

#### 5. M-CHAT-R Scoring
* **Citation:** Robins et al. (2014) *J. Autism Dev Disord*.
* **Scoring Rules:**
  * Score $0 - 2 \implies$ Low risk.
  * Score $3 - 7 \implies$ Medium risk (requires follow-up).
  * Score $8 - 20 \implies$ High risk (immediate referral).
  * Normalized Score:
    $$\text{Score} = \min\left(1.0, \frac{\text{Total Risk Points}}{20}\right)$$

#### 6. AIIMS INDT-ASD Scoring
* **Citation:** Malhotra et al. (2019) *PLOS ONE*.
* **Scoring Rules:**
  * 28 Likert items scored 0 to 4 (maximum score 112).
  * Cutoff $\ge 36 \implies$ Concern.
  * Normalized Score:
    $$\text{Score} = \min\left(1.0, \frac{\text{Total Score}}{112}\right)$$

---

### Combined Risk Formula and Decision Logic
The final classification combines the normalized scores using a weighted sum:

$$\text{Combined Score} = (0.40 \times Q_{\text{norm}}) + (0.30 \times G_{\text{risk}}) + (0.20 \times N_{\text{risk}}) + (0.10 \times E_{\text{risk}})$$

Where:
* $Q_{\text{norm}}$: Questionnaire normalized score.
* $G_{\text{risk}}$: Social gaze risk score.
* $N_{\text{risk}}$: Name response risk score.
* $E_{\text{risk}}$: Facial expression risk score.

#### Decision Logic:
* $\text{Combined Score} < 0.30 \implies$ **Low Risk**
* $0.30 \le \text{Combined Score} < 0.45 \implies$ **Medium Risk**
* $\text{Combined Score} \ge 0.45 \implies$ **High Risk** (Sets the `flagged` status to `true` for clinician review).

---

## 7. OpenFace Analysis

### Expected Workflow
The file `openface_service.py` acts as a wrapper around the OpenFace command-line tools:
1. Receives the path of the saved MP4 file.
2. Spawns a subprocess calling `FeatureExtraction` at `/usr/local/bin/FeatureExtraction`.
3. Passes parameters:
   * `-f [video_path]`: Specifies input video.
   * `-out_dir [tmpdir]`: Saves outputs to a temporary directory.
   * `-aus`: Extracts Action Units.
   * `-pose`: Estimates head yaw/pitch/roll.
   * `-gaze`: Extracts gaze vectors.
   * `-2Dfp`: Tracks 2D facial landmarks.
   * `-quiet`: Suppresses console output.
4. Reads the output CSV file in the temp directory.
5. Filters rows where tracking confidence is $< 0.8$.
6. For valid frames, evaluates $AU6$ and $AU12$ intensities.
7. Calculates the `expression_rate` (percentage of frames with active smile) and average Action Unit values.

### External Dependencies
* **OpenFace Binary:** Requires the compiled C++ `FeatureExtraction` executable.
* **System Libraries:** OpenCV, dlib models (for face landmark detection), OpenBLAS, CUDA (optional for GPU acceleration), and standard compression codecs.

### Fallback Logic and Mock Mode
If the OpenFace binary is missing or `FileNotFoundError` occurs, the service catches the exception, logs a warning, and executes `_mock_openface_result()`:
```python
def _mock_openface_result() -> dict:
    return {
        "total_frames": 0,
        "smile_frames": 0,
        "expression_rate": 0.0,
        "mean_au6": 0.0,
        "mean_au12": 0.0,
        "frames": [],
        "mock": True,
    }
```

### Production Requirement Assessment
**OpenFace is absolutely required for production.** If the OpenFace binary is missing in production:
1. `expression_rate` defaults to `0.0`.
2. The risk score function `score_expression(0.0)` evaluates to `1.0` (highest risk score).
3. This adds a constant $0.10$ penalty to the child's final risk index ($0.10 \times 1.0 = 0.10$).
4. A low-risk child could be pushed into a medium-risk classification, and a medium-risk child into a high-risk category, triggering false-positive clinician reviews.
5. In addition, the system loses verification checks for facial movement and expressions, which are key clinical metrics.

---

## 8. Frontend Dashboard Architecture

The frontend is a single-page React dashboard designed for clinicians to inspect and label screening results.

### Router and Navigation
* Router configurations in `App.jsx` are state-driven using a conditional render of a state variable `view` (`"flagged"` or `"all"`) rather than complex navigation schemes.
* Clicking sidebar options toggles the `view` state and fetches corresponding lists from the backend via Axios.
* Selection events write the `sessionId` string to the `selected` state, mounting the `<SessionDetail />` viewport.

### State Management
* App-level state is maintained using React Hooks (`useState`, `useEffect`, `useCallback`).
* Clicking refresh triggers API requests that update state arrays, forcing components to update.
* Local changes inside `<SessionDetail />` (such as saving doctor reviews) use callback handlers to update parent records in the session array.

### Charts & Visualization
* Uses the **Recharts** library to construct custom interactive components.
* Implements a `<RadarChart />` containing `<PolarGrid />`, `<PolarAngleAxis />`, `<Tooltip />`, and a `<Radar />` boundary overlay.
* Variables plotted on the radar:
  * **Social Gaze:** Social preference ratio (Task A), plotted as $1 - \text{ratio}$ (inverted to show risk).
  * **Name Response:** Ratio of successful name-call trials with responses.
  * **Expression:** Smile rate calculated from OpenFace.
  * **Non-repetitive:** Non-stereotypical score, mapped as $1 - \text{ASDMotion score}$.

### API Integrations
Axios client setup (`dashboard/src/services/api.js`) maps HTTP requests to the backend:
* `getFlagged()` $\to$ `GET /doctor/flagged`
* `getAllSessions(limit)` $\to$ `GET /doctor/all?limit=...`
* `getSession(id)` $\to$ `GET /sessions/{id}`
* `submitJudgment(id, judgment, notes)` $\to$ `POST /doctor/{id}/judgment`

### Security and Authentication
* **No Authentication:** The dashboard contains no authentication screens, tokens, or route guards.
* **No Authorization Middleware:** The API endpoint `/doctor/*` lacks JWT validation or role check policies, meaning any client on the network can query or modify patient diagnostic records.

### Broken/Critical Connections
* **Nginx Hardcoded Proxy Failures:** The dev environment uses the Webpack `"proxy": "http://backend:8000"` configuration in `package.json`. However, when built for production inside the `Nginx` container (as configured in the `Dockerfile`), this proxy does not work. Nginx must be configured to pass API routes to the backend container, or the React app must build with explicit production API endpoints.
* **Direct Docker API Bindings:** In `docker-compose.yml`, the environment variable `REACT_APP_API_URL` is set to `http://localhost:8000`. If the client browser cannot reach `localhost:8000` (e.g. running on a remote clinic machine), API requests will fail.

---

## 9. Mobile Application Architecture

The mobile client is built in Flutter, targeting Android 5.0+ devices. It guides the child through interactive visual tasks and records tracking metrics on-device.

### Screens and Flow
```
[RegistrationScreen] 
         │
         ▼
  [ConsentScreen]  (Term Scroll Validator)
         │
         ▼
[QuestionnaireScreen] ──► (M-CHAT-R or AIIMS INDT-ASD depending on age)
         │
         ▼
  [TaskAScreen]  (Social Gaze Split-View)
         │
         ▼
  [TaskBScreen]  (Name Response Cues + TTS)
         │
         ▼
  [TaskCScreen]  (Copycat Imitation Tasks)
         │
         ▼
  [TaskDScreen]  (Bubble Popping Game)
         │
         ▼
[SessionCompleteScreen] ──► (JSON + Multipart Video Upload)
```

### MediaPipe & Native Integration
* The application communicates with native code via MethodChannel `autism_screening/mediapipe` and EventChannel `autism_screening/gaze_stream`.
* Native Kotlin code in `MediaPipeHandler.kt` loads `face_landmarker.task` from assets.
* Captures facial points using the 478 landmark model:
  * **Iris tracking:** Averaging coordinates of landmarks 468–472 (left eye) and 473–477 (right eye).
  * **Head yaw estimation:** Calculated from the horizontal distance between the nose tip (landmark 1) and eye center mid-point.
  * **Blink EAR detection:** Calculated using vertical landmarks (159, 145, 386, 374) divided by horizontal landmarks (33, 133, 362, 263).
* Sends parsed telemetry frames back to Dart as maps of floats over the event channel.

### API Integrations
* Extends connection pipelines using the **Dio** HTTP client.
* Integrates `registerChild` (`/children`) to register the profile.
* Executes `uploadSession` (`/sessions/upload`) using `MultipartFile.fromString` for JSON payload logs and `MultipartFile.fromFile` for video files.

### Critical Structural Flaws (Bugs)
1. **Camera Frames Not Connected to MediaPipe:**
   * Flutter handles the UI camera view, but **no frame data is passed to the native Kotlin code**.
   * In `MediaPipeHandler.kt`, `processFrame` is never called.
   * As a result, the EventChannel `gaze_stream` never receives data.
   * Gaze data buffers are uploaded empty, causing calculations to default to neutral values.
2. **Crash on Empty Video Upload:**
   * The orchestrator in `main.dart` starts upload with `videoPath = ''` (empty string).
   * In `api_service.dart`, calling `MultipartFile.fromFile('')` throws a `FileSystemException` and crashes the application on the completion screen.

---

## 10. Environment Configuration

### Environmental Variables (`.env`)
* `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://autism_user:autism_pass@db:5432/autism_db`).
* `SECRET_KEY`: Security signature for encoding tokens.
* `VIDEO_STORAGE_PATH`: Directory path for video uploads (default: `/data/videos`).
* `OPENFACE_BIN`: Location of the OpenFace FeatureExtraction binary (default: `/usr/local/bin/FeatureExtraction`).
* `ASDMOTION_PATH`: Path to the clone of the ASDMotion repository (default: `/opt/ASDMotion`).
* `MODEL_PATH`: Saved RandomForest questionnaire classifier path (default: `/app/ml/questionnaire_model.pkl`).
* `S3_BUCKET`: AWS S3 bucket name.
* `AWS_ACCESS_KEY` / `AWS_SECRET_KEY`: Credentials for S3 storage access.
* `DEBUG`: Set to `false` in production to restrict logs.

### Docker Compose Services
Configures three containers inside `docker-compose.yml`:
1. **`db` (PostgreSQL):** Uses the `postgres:15-alpine` image. Binds local database files to the `pgdata` volume and mounts `schema.sql` to initialize database structures. Exposes port 5432.
2. **`backend` (FastAPI):** Builds from `./backend/Dockerfile`. Connects to the database and maps video files to the `videodata` volume. Depends on the database container being healthy.
3. **`dashboard` (React):** Builds from `./dashboard/Dockerfile`. Runs the production web interface behind Nginx on port 3000.

### Startup Sequence
1. Running `docker-compose up --build` starts the environment.
2. The `db` container starts, initializes PostgreSQL, and runs `schema.sql`.
3. The `db` healthcheck executes `pg_isready` to verify database status.
4. Once healthy, the `backend` container starts.
5. The backend runs uvicorn, creates any missing tables via SQLAlchemy, and exposes port 8000.
6. The `dashboard` container builds React static files and starts Nginx on port 3000.

---

## 11. Current Working Features

| Feature | Verified State | Verification Details / Source |
|---------|----------------|-------------------------------|
| **DB Migrations & Schema** | ✅ Working | Verified by SQLAlchemy database initialization and DDL queries in `schema.sql`. |
| **Standardized Questionnaires** | ✅ Working | M-CHAT-R and AIIMS INDT-ASD logic in `questionnaire.dart` are correct, including scoring and languages (EN/HI). |
| **API Endpoints** | ✅ Working | Child registration, session details retrieval, and judgment logging endpoints are fully functional. |
| **Random Forest Questionnaire** | ⚠️ Partially Working | ML training code is correct, but requires manual dataset downloads. |
| **Background Processing Task** | ⚠️ Partially Working | Backend background task framework is set up, but fails due to missing binaries in the container. |
| **Doctor Dashboard UI** | ⚠️ Partially Working | Renders components and charts correctly, but has API connection issues inside the Docker container. |
| **Native Gaze Calculations** | ⚠️ Partially Working | Iris landmark, head yaw, and blink EAR algorithms in `MediaPipeHandler.kt` are correct, but camera frames are not connected. |
| **Mobile Flow Orchestrator** | ⚠️ Partially Working | Screen transitions are correct, but the app crashes on upload due to missing video files. |
| **OpenFace & ASDMotion Pipeline** | ❌ Broken | Missing binaries in the Docker container prevent real execution, forcing the mock fallback. |

---

## 12. Known Bugs & Issues

### 1. Mobile App Crashes on Session Upload
* **Description:** In `main.dart`, `uploadSession` calls the API with `videoPath = ''`. In `api_service.dart`, `MultipartFile.fromFile('')` fails to open a file with an empty path, throwing a `FileSystemException` that crashes the app.
* **Severity:** **Critical**
* **Workaround:** Add a check to only attach a video file if `videoPath` is not empty.

### 2. Gaze Tracking Camera Source Disconnected
* **Description:** Gaze tracking calculations in `MediaPipeHandler.kt` are correct, but the mobile app does not feed camera frames to the native tracker. Gaze data remains empty.
* **Severity:** **Critical**
* **Workaround:** Implement camera frame extraction in Flutter and pass frames to `processFrame` over the MethodChannel.

### 3. OpenFace and ASDMotion Binaries Missing in Container
* **Description:** The Docker container does not install the required OpenFace or ASDMotion binaries, causing the backend to always fall back to mock results.
* **Severity:** **High**
* **Workaround:** Update the `Dockerfile` to compile and install OpenFace and its dependencies, or use a prebuilt Docker image.

### 4. React Dashboard API Connection Issues in Production
* **Description:** In Docker, Nginx serves the React app but does not proxy API requests to the backend container. The configuration relies on `REACT_APP_API_URL` pointing to `localhost:8000`, which fails if the dashboard is accessed remotely.
* **Severity:** **High**
* **Workaround:** Configure Nginx as a reverse proxy for `/api` routes, pointing to `http://backend:8000`.

### 5. Missing Database Connection Pooling and Error Handling
* **Description:** Database connections in `database.py` do not handle dropouts or connection limits under heavy loads.
* **Severity:** **Medium**
* **Workaround:** Add connection pooling options to the SQLAlchemy engine.

### 6. Obsolete Docker Compose Syntax
* **Description:** `docker-compose.yml` uses the obsolete `version` attribute, which is ignored by newer Docker engines.
* **Severity:** **Low**
* **Workaround:** Remove the `version: "3.9"` line from `docker-compose.yml`.

---

## 13. Technical Debt

* **Duplicate Gaze Configuration and Scoring Parameters:**
  * Gaze scoring thresholds, task durations, and weights are duplicated in both `backend/ml/scoring_thresholds.py` and `mobile/lib/constants/task_config.dart`. Updates to one file must be manually duplicated in the other.
* **Plaintext Video Storage:**
  * While comments mention "encrypted video storage," `video_service.py` writes standard unencrypted MP4 files to the filesystem. This is a security and privacy risk.
* **Silenced Pipeline Execution Errors:**
  * The background task logs errors but continues scoring if OpenFace or ASDMotion fails, falling back to mock results. This masks configuration issues.
* **No Database Migrations (Alembic):**
  * `alembic` is listed in `requirements.txt`, but there is no migration history or initialized folder. Schema modifications require dropping and recreating the tables manually.

---

## 14. Security Audit

* **Authentication & Authorization:**
  * The React dashboard has no login or security features.
  * The FastAPI server does not validate requests on `/doctor` endpoints, exposing patient data to the network.
* **Input Validation on File Uploads:**
  * The `/sessions/upload` endpoint accepts arbitrary uploads without validating file sizes or types, exposing the server to denial-of-service or remote code execution risks.
* **Hardcoded Credentials & Config Secrets:**
  * Database passwords and `SECRET_KEY` variables are committed in plaintext inside `docker-compose.yml` and `.env.example`.
* **Database Network Access:**
  * The database container exposes port 5432 directly to the host machine. In production, database access should be restricted to the internal Docker network.

---

## 15. Recommended Development Roadmap

### Phase 1: Immediate Bug Fixes (1-2 Weeks)
1. **Fix Mobile Upload Crash:** Add a check in `api_service.dart` to verify `videoPath` is not empty before creating the video multipart parameter.
2. **Fix Camera Gaze Tracking:** Implement camera frame capture on the client side and feed frames to the native MediaPipe tracker.
3. **Clean Up Docker Compose Configuration:** Remove the obsolete version attribute and restrict database port mapping to localhost.

### Phase 2: Security & Backend Deployment (3-4 Weeks)
1. **Implement JWT Authentication:** Add login endpoints for doctors, hash passwords, and protect `/doctor/*` and `/sessions/*` endpoints.
2. **Nginx Reverse Proxy:** Update Nginx configuration in the dashboard container to route API requests to the backend server.
3. **Database Migrations:** Initialize Alembic to manage database schema updates.

### Phase 3: Infrastructure Integration (1-2 Months)
1. **Compile CV Pipeline in Docker:** Update the `Dockerfile` to install and configure OpenFace and ASDMotion.
2. **Secure Video Storage:** Implement video encryption in `video_service.py` before writing files, and integrate secure S3 storage.
3. **Unified Configuration:** Reference a single configuration file or sync thresholds between backend and mobile.

### Phase 4: Long-Term Enhancements
1. **Train Indian-Specific ML Models:** Collect clinical data to train models on Indian children cohorts.
2. **Medical Device Clearance:** Perform clinical validation trials to align with CDSCO guidelines for software-based medical screening tools.

---

## 16. NeuroLens Migration Assessment

If migrating this repository to build **NeuroLens** (a cognitive visual attention assessment tool), we can leverage a significant portion of the existing codebase.

### Reusable Components
* **Standard Mobile Flow:** The registration, consent, and complete screens in the Flutter app can be reused with minor text changes.
* **MediaPipe Landmark Tracker:** The native Android Kotlin face tracking code can be reused to capture raw gaze and blink telemetry.
* **FastAPI Backend & Database:** The database structure and router endpoints can be reused for user management and session logging.
* **Doctor Dashboard Layout:** The layout, sidebar navigation, and radar charts can be reused to display cognitive metrics.

### Components Requiring Modifications
* **Standard Screening Tasks:** Tasks A-D must be replaced with visual cognitive tasks specific to NeuroLens.
* **Scoring Rules & Thresholds:** The scoring formulas in `scoring_thresholds.py` must be updated to match visual attention clinical references.
* **Random Forest ML Classifiers:** The UCI-trained questionnaire model is specific to autism and must be replaced with cognitive assessment models.
* **OpenFace & ASDMotion Pipeline:** If NeuroLens does not require smile or repetitive movement analysis, these resource-heavy external dependencies can be removed, simplifying backend deployment.
