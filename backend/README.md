# AutiScreen Backend API Service

This directory contains the FastAPI-based REST API and background analytics worker for AutiScreen.

---

## 1. Directory Structure

```text
backend/
├── routers/
│   ├── children.py     Child registration and verification
│   ├── doctor.py       Clinician review, flagging, and judgments
│   └── sessions.py     Session multipart upload, queueing, and status retrieval
├── services/
│   ├── openface_service.py   Subprocess wrapper for smile intensity detection
│   ├── asdmotion_service.py  Subprocess wrapper for repetitive movement detection
│   ├── scoring_service.py    Scoring pipeline combining behavioral telemetry and questionnaires
│   └── video_service.py      Encrypted session video storage
├── ml/
│   ├── train_model.py              UCI Random Forest model training script
│   ├── questionnaire_classifier.py  Interface to load RF pickles and run inference
│   └── scoring_thresholds.py       Scoring equations, weight coefficients, and clinical cutoffs
├── config.py           Settings loading via pydantic-settings
├── database.py         PostgreSQL models and connection setup
└── main.py             ASGI app entrypoint
```

---

## 2. Behavioral Scoring Pipeline

```text
Upload JSON + Video
       │
       ▼
1. Validate inputs (child exists, started_at format, unique session ID)
       │
       ▼
2. Write initial session record as "pending"
       │
       ▼
3. Run background task (_process_session):
   ├── A. Run OpenFace AU6 & AU12 smile extraction on video
   ├── B. Run ASDMotion OpenPose-based repetitive movement extraction
   ├── C. Compute social gaze ratios, blink rates, and name response rates
   ├── D. Execute scoring equations (combined weights: Q=40%, Gaze=30%, Name=20%, Smile=10%)
       │
       ▼
4. Save scores and update status to "done" or "completed_fallback"
```

---

## 3. Graceful Fallbacks on Missing Media
To ensure pipeline stability, the backend service separates real and fallback processing paths.
If a video file is absent, unreadable, or if openface/asdmotion binary tools are missing, the services fall back to mock returns containing zeroed behavioral metrics and flag `mock: true`. The backend worker updates `processing_status` to `completed_fallback` and records granular details in the `processing_note` field. This alerts clinicians and future machine learning operations that fallback metrics were used.

---

## 4. Run Backend Locally
Make sure Python 3.11 is configured, then run:
```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
API docs will be hosted at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
