# AutiScreen Dependency Audit

This document inventories the Python dependencies used by the AutiScreen backend and provides a security/reliability risk analysis.

---

## 1. Dependency Inventory

The following packages are currently pinned in `backend/requirements.txt`:

| Package | Version | Role | Risk Profile |
|---------|---------|------|--------------|
| `fastapi` | `0.111.0` | API Framework | **Low** (Highly active, secure) |
| `uvicorn[standard]` | `0.30.1` | ASGI Web Server | **Low** (Standard runner) |
| `python-multipart` | `0.0.9` | Multipart Form Parsing | **Low** (Active) |
| `sqlalchemy` | `2.0.30` | Object Relational Mapper | **Low** (Stable ORM) |
| `alembic` | `1.13.1` | Schema Migrations | **Low** (Stable) |
| `psycopg2-binary` | `2.9.9` | Postgres Driver | **Medium** (Quick wrapper, see below) |
| `pydantic` | `2.7.3` | Data Validation | **Low** (Industry standard) |
| `pydantic-settings` | `2.3.1` | Configuration management | **Low** (Standard) |
| `python-jose[cryptography]` | `3.3.0` | JWT Auth Tokens | **Medium** (Unmaintained, see below) |
| `passlib[bcrypt]` | `1.7.4` | Password Hashing | **Medium** (Unmaintained, see below) |
| `scikit-learn` | `1.5.0` | Machine Learning | **Low** (Active, stable) |
| `numpy` | `1.26.4` | Numerical Analysis | **Low** (Stable) |
| `pandas` | `2.2.2` | Data Analysis | **Low** (Stable) |
| `joblib` | `1.4.2` | Serialization | **Low** (Stable) |
| `opencv-python-headless` | `4.9.0.80` | Video Frame Analysis | **Low** (Active) |
| `boto3` | `1.34.131` | S3 Storage Client | **Low** (Active) |
| `httpx` | `0.27.0` | HTTP Client | **Low** (Active) |
| `python-dotenv` | `1.0.1` | Env Config | **Low** (Standard) |
| `aiofiles` | `23.2.1` | Asynchronous file IO | **Low** (Standard) |

---

## 2. Dependency Risk Analysis

### A. High Risk: `openface-test`
* **Status:** Deprecated / Unmaintained.
* **Risk:** Installs outdated wrappers, causing compile issues in newer Python container builds.
* **Mitigation:** Commented out and disabled from the base requirements. Analysis pipelines are decoupled from direct native package imports, falling back gracefully to mock evaluations when CLI binaries are missing.

### B. Medium Risk: `psycopg2-binary`
* **Status:** Active.
* **Risk:** The psycopg2 documentation states `psycopg2-binary` is intended only for development and testing, and can crash due to library linkages in production.
* **Mitigation:** In production docker builds, replace with `psycopg2` compiled from source (requires `libpq-dev` system headers).

### C. Medium Risk: `passlib`
* **Status:** Unmaintained since 2020.
* **Risk:** Triggers deprecation warnings under Python 3.12+ (since it imports the deprecated `crypt` module).
* **Mitigation:** Replace with the modern `argon2-cffi` or direct `bcrypt` package calls.

### D. Medium Risk: `python-jose`
* **Status:** Unmaintained.
* **Risk:** Lack of active security updates.
* **Mitigation:** Plan migration to `PyJWT`.
