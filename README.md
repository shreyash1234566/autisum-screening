# AutiScreen — India-Focused Autism Screening App

> **Screening tool only. Not a diagnostic instrument.**  
> All clinical decisions are made by the registered doctor.

---

## Architecture

```
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

## Open Source Tools Used

| Tool | Source | Use |
|------|--------|-----|
| MediaPipe Face Mesh | google-ai-edge/mediapipe | Gaze + blink (iris lm 468-477) |
| OpenFace 3.0 | CMU-MultiComp-Lab/OpenFace-3.0 | AU6/AU12 smile detection |
| ASDMotion | Dinstein-Lab/ASDMotion | Repetitive movement |
| MMASD+ | pavanravva/enhanced-mmasd | Movement training data |
| UCI ASD Datasets | Thabtah et al. (CC BY 4.0) | Questionnaire RF model |

---

## Scoring Thresholds (from research papers)

| Metric | Threshold | Source |
|--------|-----------|--------|
| Social gaze ratio | < 0.45 = risk | Perochon et al. 2023, NEJM Evidence |
| Name response rate | < 0.33 = risk | Perochon et al. 2023 |
| Head orientation | > 15° change | Bradshaw et al. 2018, Autism Research |
| AU6 (smile) | > 1.0 intensity | OpenFace/FACS |
| AU12 (smile) | > 1.5 intensity | OpenFace/FACS |
| Blink EAR | < 0.20 = closed | Soukupová & Čech 2016 |
| M-CHAT-R high risk | score ≥ 8 | Robins et al. 2014 |
| INDT-ASD cutoff | score ≥ 36/112 | Malhotra et al. 2019, PLOS ONE |
| Combined flag | ≥ 0.45 | Derived from above |

**Weights:** Questionnaire 40% · Gaze 30% · Name Response 20% · Expression 10%

---

## Quick Start

### 1. Backend + Dashboard
```bash
cp .env.example .env
docker-compose up --build
```
- API:       http://localhost:8000
- Docs:      http://localhost:8000/docs
- Dashboard: http://localhost:3000

### 2. Train Questionnaire Model
```bash
cd ml
pip install -r requirements.txt
python download_data.py      # Downloads UCI datasets
python ../backend/ml/train_model.py
# Expected: ~95% 5-fold CV accuracy (Thabtah et al. 2018)
```

### 3. Flutter App
```bash
cd mobile
flutter pub get
# Download MediaPipe model (face_landmarker.task):
wget -O android/app/src/main/assets/face_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task

flutter run   # Connect Android device (API 21+)
```

### 4. OpenFace 3.0
```bash
pip install openface-test
openface download
# Binary installed to: /usr/local/bin/FeatureExtraction
```

### 5. ASDMotion
```bash
git clone https://github.com/Dinstein-Lab/ASDMotion /opt/ASDMotion
# Requires OpenPose — see ASDMotion README
```

---

## Indian Data

| Dataset | Status | Action |
|---------|--------|--------|
| UCI ASD (Thabtah) | ✅ Auto-download | `python ml/download_data.py` |
| Toddler Kaggle | Manual | kaggle.com/fabdelja/autism-screening-for-toddlers |
| AMI (AIIMS, 225 Indian kids) | Email request | Email Trapti Shrivastava (arxiv.org/abs/2404.02181) |
| MMASD+ (movement) | ✅ GitHub | github.com/pavanravva/enhanced-mmasd |

---

## Questionnaire Tools

- **M-CHAT-R** (16-30 months): Free from mchatscreen.com · Hindi validated (Juneja 2024)
- **AIIMS INDT-ASD** (>30 months): Malhotra et al. PLOS ONE 2019 · DOI: 10.1371/journal.pone.0213242

---

## Regulatory Note

Per CDSCO Medical Devices Rules 2017 (India):  
This is a **screening support system**, not a diagnostic device.  
Clinical validation on Indian children is required before clinical deployment.

---

## Project Files

```
autism-screening-app/
├── mobile/           Flutter app (Android 5.0+, API 21+)
│   ├── lib/          Dart source
│   └── android/      Native MediaPipe (Kotlin)
├── backend/          FastAPI + Python ML
│   ├── routers/      REST endpoints
│   ├── services/     OpenFace, ASDMotion, scoring
│   └── ml/           Model training + thresholds
├── dashboard/        React doctor dashboard
├── database/         PostgreSQL schema
├── ml/               Standalone training scripts
└── docker-compose.yml
```
