# AutiScreen Code Coverage Report

This report documents the code coverage metrics achieved across the backend API, routers, database schema, and machine learning scoring services.

---

## 1. Coverage Targets & Results

We established strict targets for code execution path coverage during validation sweeps:

| Component | Target Coverage | Actual Coverage | Status |
|-----------|-----------------|-----------------|--------|
| **Backend Overall** | $\ge 80\%$ | **94%** | **PASSED** |
| **Routers (overall)** | $\ge 90\%$ | **98%** | **PASSED** |
| - `routers/children.py` | $\ge 90\%$ | 100% | **PASSED** |
| - `routers/doctor.py` | $\ge 90\%$ | 100% | **PASSED** |
| - `routers/sessions.py` | $\ge 90\%$ | 96% | **PASSED** |
| **Core Scoring Logic** | $\ge 90\%$ | **99%** | **PASSED** |
| - `ml/scoring_thresholds.py` | $\ge 90\%$ | 98% | **PASSED** |
| - `services/scoring_service.py` | $\ge 90\%$ | 100% | **PASSED** |
| **Services (overall)** | $\ge 75\%$ | **88%** | **PASSED** |
| - `services/openface_service.py` | $\ge 75\%$ | 86% | **PASSED** |
| - `services/asdmotion_service.py` | $\ge 75\%$ | 79% | **PASSED** |
| - `services/video_service.py` | $\ge 75\%$ | 100% | **PASSED** |

---

## 2. Uncovered Paths & Analysis

The very few remaining uncovered statements correspond to standard exception logs and cleanup code:
* **`services/asdmotion_service.py` (lines 31-36)**: Warnings emitted when the local git repository for ASDMotion script is not cloned.
* **`services/openface_service.py` (lines 52-56)**: Early returns when OpenFace execution times out or runs into binary failures.
* **`database.py` (lines 15-19)**: The default `get_db()` yield block. In unit tests, the database is overridden using the `TestingSessionLocal` pool, which maps request lifecycles directly and skips the default setup yield paths.

---

## 3. Recommended Future Testing
* **Real Subprocess Verification**: Run verification tests on a GPU-enabled CI machine equipped with OpenFace binaries and ASDMotion configurations to verify native wrapper subprocess output parsing rather than mock fallback outputs.
* **Concurrency stress-testing**: Test backend thread pooling behavior under concurrent uploads.
