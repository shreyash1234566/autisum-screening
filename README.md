# AutiScreen — India-Focused Autism Screening App

> [!WARNING]
> **AutiScreen is a clinical screening support system, NOT a diagnostic instrument.**  
> All diagnostic determinations and clinical decisions must be made by a registered, licensed healthcare clinician.

---

## 1. Project Overview
AutiScreen is an India-focused clinical screening support system designed to detect early indicators of Autism Spectrum Disorder (ASD) in children. The platform bridges the gap between digital behavioral analysis and clinical oversight by combining on-device gaze-tracking, server-side visual behavior analytics (smile and stereotypical movement detection), and validated questionnaires.

---

## 2. Tech Stack
* **Mobile (On-Device Client)**: Flutter (Android 5.0+, API 21+), MediaPipe Face Mesh (478 landmarks, 468-477 iris markers for gaze tracking).
* **Backend (Analysis API)**: Python 3.11, FastAPI, SQLAlchemy ORM, Alembic.
* **Database (Storage)**: PostgreSQL (production), SQLite StaticPool (development/in-memory testing).
* **Behavioral Engines**: OpenFace 3.0 (Action Units AU6/AU12 smile detection), ASDMotion (repetitive movement detection).
* **Machine Learning**: Scikit-Learn (Random Forest model trained on UCI ASD Screening datasets).
* **Dashboard (Clinician Portal)**: React, TailwindCSS.
* **Containerization & CI/CD**: Docker, Docker Compose, GitHub Actions.

---

## 3. Architecture Diagram

```text
┌─────────────────────────────────────┐
│  Flutter Mobile App (Android 5.0+)  │
│  • MediaPipe Face Mesh (478 pts)    │
│  • Gaze tracking (iris lm 468-477)  │
│  • M-CHAT-R / AIIMS INDT-ASD Q'aire │
│  • 4 structured tasks               │
│  • Google TTS (name calling)        │
└──────────────┬──────────────────────┘
               │ Encrypted upload
               ▼
┌─────────────────────────────────────┐
│  FastAPI Backend (Python 3.11)      │
│  • OpenFace 3.0 — AU6/AU12 smile   │
│  • ASDMotion — repetitive movement  │
│  • Combined risk scoring            │
│  • Random Forest (UCI dataset)      │
│  • PostgreSQL storage               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  React Doctor Dashboard             │
│  • Flagged case review              │
│  • Radar charts (behavioral scores) │
│  • Clinical judgment input          │
│  • Training label collection        │
└─────────────────────────────────────┘
```

---

## 4. Directory Structure

```text
autisum-screening/
├── .github/workflows/    CI/CD configurations
├── backend/              FastAPI + Python ML Service
│   ├── routers/          REST API endpoints
│   ├── services/         OpenFace, ASDMotion, video & scoring
│   ├── ml/               Model definitions and thresholds
│   └── database.py       DB initialization and schemas
├── dashboard/            React clinician dashboard
├── database/             PostgreSQL schema definitions
├── docs/                 Detailed architecture and onboarding docs
├── ml/                   Model training and UCI downloader scripts
└── tests/                Full unit, integration, and e2e test suite
```

---

## 5. Local Setup
1. **Prerequisites**: Python 3.11, Flutter SDK, Node.js (v18+).
2. **Train Standalone ML Model**:
   ```bash
   cd ml
   pip install -r requirements.txt
   python download_data.py
   python ../backend/ml/train_model.py
   ```
3. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   uvicorn main:app --reload
   ```
4. **Dashboard Setup**:
   ```bash
   cd dashboard
   npm install
   npm start
   ```

---

## 6. Docker Setup
Build and run the entire suite (PostgreSQL, Backend API, and React Dashboard) with one command:
```bash
cp .env.example .env
docker compose up --build
```
* **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Dashboard**: [http://localhost:3000](http://localhost:3000)

---

## 7. Testing Flow
To run the automated Python test suite inside the isolated container context:
```bash
docker compose -f tests/docker-compose.test.yml up --build --exit-code-from test-runner
```
To run and inspect test coverage details:
```bash
docker compose -f tests/docker-compose.test.yml run test-runner sh -c "pip install pytest-cov && pytest --cov=/app --cov-report=term-missing /tests/"
```

---

## 8. API Overview
* **`POST /children`**: Registers a child profile. Validates age limits and languages.
* **`POST /sessions/upload`**: Uploads behavioral JSON telemetry and session video for background analysis.
* **`GET /sessions/{session_id}`**: Retrieves session status, behavioral scores, and risk flags.
* **`GET /doctor/flagged`**: Lists all sessions flagged for manual clinician review.
* **`POST /doctor/{session_id}/judgment`**: Records manual clinical determinations.

---

## 9. Development Workflow & Branch Strategy
To maintain codebase quality, developers must adhere to the following rules:
* **No Direct Commits to `main`**: All features and fixes must go through pull requests.
* **Rebase or Squash-and-Merge**: Squash branch histories to keep the main git history readable. No force pushes on shared branches.
* **Branch Isolation Policies**:
  - `docs/repository-hardening`: Isolated branch for architectural documents and README updates.
  - `test/coverage-and-quality`: Isolated branch for QA coverage reports, negative testing, and security configurations.

---

## 10. Known Limitations & Roadmap
* **ML Demographics**: Standalone UCI questionnaire RF model is trained on Western populations. Validation on Indian cohorts is pending.
* **Offline Processing**: Real video analysis requires heavy binaries (OpenFace/ASDMotion). Mobile clients fall back to on-device MediaPipe outputs, and server queues processing asynchronously.
* **Roadmap**: Enforce auth guards on all clinician endpoints, expand clinical validation on Indian cohorts (AIIMS INDT-ASD), and compile native C++ builds of OpenFace directly inside backend Docker.
