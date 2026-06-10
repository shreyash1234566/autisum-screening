# AutiScreen Security Review

This document reports the findings and recommendations of a production security audit performed on the AutiScreen codebase.

---

## 1. Audit Summary

The code was audited against common vulnerability classes including SQL Injection, Path Traversal, Unsafe File Uploads, CORS policies, Secrets Management, and Authentication/Authorization controls.

---

## 2. Key Findings & Audits

### A. Path Traversal & Unsafe File Uploads
* **Audit Target:** `backend/routers/sessions.py` & `backend/services/video_service.py`
* **Analysis:** Uploaded video files are saved to the server filesystem.
* **Security Control:** The system does **not** trust or use the user-supplied filename to write to the filesystem. Instead:
  1. The storage path is generated using the validated `session_id`: `Path(settings.VIDEO_STORAGE_PATH) / session_id`.
  2. The file is saved under a static name: `session.mp4`.
* **Verdict:** **SAFE**. Path traversal is prevented because the filename is hardcoded and the parent directory is based on `session_id`.

### B. SQL Injection (SQLi)
* **Audit Target:** All routers (`children.py`, `sessions.py`, `doctor.py`)
* **Analysis:** Database interactions.
* **Security Control:** All queries are constructed using SQLAlchemy ORM syntax (e.g., `db.query(Child).filter(Child.id == child_id)`). This utilizes parameterized queries at the driver level, ensuring user inputs are treated as literal values rather than executable commands.
* **Verdict:** **SAFE**. Parameterization prevents SQL injection.

### C. CORS Origin Configurations
* **Audit Target:** `backend/main.py`
* **Analysis:** CORS middleware setup.
* **Finding:** Line 24 in `main.py` sets `allow_origins=["*"]`. While useful for local Flutter/React development, allowing all origins in production exposes API endpoints to Cross-Origin resource sharing attacks.
* **Recommendation:** Update `main.py` to read allowed origins from environment settings:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.CORS_ALLOWED_ORIGINS,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
* **Verdict:** **LOW RISK (HIGH PRIORITY FIX)**. Needs tightening in production.

### D. Secrets Management
* **Audit Target:** `.env` and `config.py`
* **Analysis:** Database connection strings and tokens.
* **Finding:** Default test credentials (e.g. `test_password`) are provided in `.env.example`.
* **Recommendation:** Ensure production environment configuration uses environment variables injected securely (e.g. via Docker secrets or environment configurations) rather than hardcoded configurations.
* **Verdict:** **SAFE** (provided env files are not committed to git, which is enforced by our updated `.gitignore`).

### E. Authentication & Authorization
* **Audit Target:** API access controls.
* **Finding:** Currently, clinician endpoints such as child registration (`/children`) and session uploads (`/sessions/upload`) do not require authentication headers. This is acceptable for mock testing but poses a high risk if exposed to the open internet.
* **Recommendation:** Implement OAuth2 JWT bearer token checks (utilizing the pre-installed `python-jose` and `passlib` libraries) to restrict access to authenticated clinicians/doctors only.
* **Verdict:** **MEDIUM RISK**. Clinician authentication should be introduced before open production deployments.
