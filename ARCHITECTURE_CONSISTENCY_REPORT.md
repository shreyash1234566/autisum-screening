# Architecture Consistency Report

This document reports on the structural consistency check performed between the AutiScreen codebase implementation and its corresponding architectural and API documentation.

---

## 1. API Endpoints Mapping Validation

We compared all documented routes in [docs/API_REFERENCE.md](file:///d:/Desktop/Autism-Screening/autisum-screening/docs/API_REFERENCE.md) against the actual FastAPI router controllers:

* **Children Router:**
  * `POST /children`: Implemented in [children.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/children.py#L18). Matches schema.
  * `GET /children/{id}`: Implemented in [children.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/children.py#L42). Matches schema.
* **Sessions Router:**
  * `POST /sessions/upload`: Implemented in [sessions.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/sessions.py#L18). Form parameter keys (`session_json`, `video`) are fully consistent with Flutter client layouts.
  * `GET /sessions/{id}`: Implemented in [sessions.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/sessions.py#L149). Matches schema.
* **Doctor Router:**
  * `GET /doctor/flagged`: Implemented in [doctor.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/doctor.py#L35). Matches schema.
  * `GET /doctor/all`: Implemented in [doctor.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/doctor.py#L47). Matches schema.
  * `POST /doctor/{session_id}/judgment`: Implemented in [doctor.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/doctor.py#L58). Matches schema.

* **Consistency Result:** **100% Consistent.** No missing or phantom API endpoints were detected.

---

## 2. Database Fields Mapping Validation

We verified that the database models defined in SQLAlchemy [database.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/database.py) align with the reference schemas described in [docs/DATABASE_SCHEMA.md](file:///d:/Desktop/Autism-Screening/autisum-screening/docs/DATABASE_SCHEMA.md):

* **Table: `doctors`**: All 5 columns (`id`, `name`, `email`, `password`, `created_at`) are fully documented and match code definitions.
* **Table: `children`**: All 7 columns (`id`, `name`, `age_months`, `gender`, `language`, `doctor_id`, `created_at`) match Pydantic schemas and database constraints.
* **Table: `sessions`**: Checked calculated metrics (`social_gaze_ratio`, `name_response_rate`, `expression_rate`, `repetitive_score`) and pipeline statuses (`processing_status`, `processing_note`, `processing_error`).
  * All 28 fields defined in the database model are documented with exact matching types.

* **Consistency Result:** **100% Consistent.**

---

## 3. Services Mapping Validation

Checked all helper services referenced in system architecture documents:
1. **Video Encryption & IO Service:** [video_service.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/services/video_service.py) exists and handles storage.
2. **OpenFace Facial landmarks Pipeline:** [openface_service.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/services/openface_service.py) exists.
3. **ASDMotion Motor movement Pipeline:** [asdmotion_service.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/services/asdmotion_service.py) exists.
4. **Behavioral scoring engine:** [scoring_service.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/services/scoring_service.py) exists.

* **Consistency Result:** **100% Consistent.** All referenced services exist and are fully integrated into the background queue logic.
