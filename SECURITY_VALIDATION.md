# Security Review Validation

This document presents a formal security validation of the AutiScreen repository, highlighting verified security findings, unresolved risks, and mitigation recommendations.

---

## 1. Verified Findings & Applied Fixes

We systematically audited the backend codebase and infrastructure parameters:

* **Path Traversal Risk on File Upload (Mitigated):**
  * *Analysis:* The `POST /sessions/upload` endpoint allowed clients to pass a custom `session_id` in the JSON payload, which was then appended directly to the storage path:
    `storage_dir = Path(settings.VIDEO_STORAGE_PATH) / session_id`
    A malicious `session_id` using sequences like `../../` could lead to arbitrary directory writes or system file overrides.
  * *Action Taken:* Added regular expression verification on the input `session_id` in [sessions.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/routers/sessions.py#L29):
    ```python
    import re
    if not re.match(r"^[a-zA-Z0-9_\-]+$", session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    ```
    This restricts `session_id` to alphanumeric characters, dashes, and underscores, preventing path traversal. We verified the correction with a new negative test case.
* **SQL Injection Risks (Mitigated):**
  * *Analysis:* Checked how database queries are made using SQLAlchemy.
  * *Verification:* The API uses the SQLAlchemy ORM query engine (`db.query(...)`) or parameterized SQL binds, avoiding raw SQL queries string interpolation. This completely blocks SQL injection pathways.
* **Secrets Handling (Mitigated):**
  * *Analysis:* Checked for hardcoded passwords or API keys in code.
  * *Verification:* API secrets, database passwords, and AWS credentials are loaded dynamically using Pydantic settings in [config.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/config.py) from a local `.env` file. A template config file `.env.example` is provided, and `.env` is properly excluded via `.gitignore`.

---

## 2. Unresolved Risks (For Production Release)

The following risks are present in the developer build and must be addressed before publishing to a live production environment:

* **Permissive CORS Settings:**
  * *Location:* [main.py](file:///d:/Desktop/Autism-Screening/autisum-screening/backend/main.py#L24)
  * *Finding:* CORS middleware is configured with `allow_origins=["*"]`. This allows any third-party domain/browser site to request API metrics or trigger uploads.
  * *Risk:* Cross-origin request forgery and data scraping.
* **Lack of Authentication & Authorization:**
  * *Finding:* Currently, there are no bearer tokens, JSON Web Tokens (JWT), or session authorization headers required to call administrative, child, or doctor endpoints. Anyone with network access to the backend port can query patients or doctor reviews.
  * *Risk:* Data leakage of clinical PHI (Protected Health Information).
* **Missing Video File Encryption:**
  * *Finding:* Although `video_service.py` is labeled as *encrypted video storage*, it currently writes raw bytes to the filesystem:
    `video_path.write_bytes(video_bytes)`
  * *Risk:* Unprotected storage of patient media on host filesystems.

---

## 3. Future Recommendations

To transition AutiScreen to a production environment (such as HIPAA-compliant setups):

1. **Tighten CORS Middleware:**
   Change `allow_origins=["*"]` to explicitly match the dashboard host IP/URL.
2. **Implement OAuth2/JWT Authentication:**
   Secure endpoints with token verification. Implement doctor login routing to check requests signature.
3. **AES Media Encryption:**
   Add real AES-256 binary encryption/decryption in `video_service.py` before files are written/read from the filesystem.
4. **Rate Limiting:**
   Integrate API rate-limiting middleware (like `slowapi`) to prevent denial-of-service (DoS) attacks on media upload endpoints.
