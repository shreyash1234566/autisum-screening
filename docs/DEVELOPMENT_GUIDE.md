# Production Development & Deployment Guide

This document describes the deployment pipelines, environment configuration variables, and monitoring instructions for AutiScreen.

---

## 1. System Environment Configuration

All configurations are loaded dynamically at startup via Pydantic settings from the local `.env` file (or system environment variables).

### Environment Variables Glossary

| Variable Name | Description | Default / Example Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://autism_user:autism_pass@db:5432/autism_db` |
| `SECRET_KEY` | Hexadecimal string used for security | `CHANGE_ME_use_openssl_rand_hex_32` |
| `VIDEO_STORAGE_PATH` | Absolute path to store session MP4 files | `/data/videos` |
| `OPENFACE_BIN` | Path to the OpenFace `FeatureExtraction` binary | `/usr/local/bin/FeatureExtraction` |
| `ASDMOTION_PATH` | Path to the ASDMotion repository clone | `/opt/ASDMotion` |
| `MODEL_PATH` | Path to the questionnaire Random Forest model | `/app/ml/questionnaire_model.pkl` |
| `S3_BUCKET` | AWS S3 bucket name for backup video archiving | `autism-sessions` |
| `AWS_ACCESS_KEY` | AWS programmatic access key | (Empty for local) |
| `AWS_SECRET_KEY` | AWS programmatic secret key | (Empty for local) |
| `DEBUG` | Verbose logging toggle | `false` |

---

## 2. Docker Deployment

In production, AutiScreen runs as containerized microservices managed via Docker Compose.

### Production Topology
* **`db` (PostgreSQL):** Stores relational schemas. Mounts a persistent volume (`pgdata`) to preserve database state across container restarts.
* **`backend` (FastAPI):** Hosts APIs, handles media uploads, executes scoring pipelines, and hosts the background tasks queue.
* **`dashboard` (React/Nginx):** Serves compiled static frontend code.

### Deployment Commands

1. **Deploy Stack in Detached (Background) Mode:**
   ```bash
   docker compose up -d
   ```
2. **Rebuild Container Images (After Code Modifications):**
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```
3. **Shutdown Services & Retain Persistent Volumes:**
   ```bash
   docker compose down
   ```
4. **Shutdown Services & Delete Database Volumes (Destructive Reset):**
   ```bash
   docker compose down -v
   ```

---

## 3. Operations, Logging, & Monitoring

### 3.1 Viewing Container Logs
To monitor API activity, background task logs, or database operations:
* **All Services:**
  ```bash
  docker compose logs -f
  ```
* **API Backend Logs Only:**
  ```bash
  docker compose logs -f backend
  ```
* **Database Logs Only:**
  ```bash
  docker compose logs -f db
  ```

### 3.2 Health Checking
* **Backend Health Check:** Query `http://<server-ip>:8000/docs` or check response codes on child endpoints.
* **Database Connection Status:** Verify connection pool performance in the backend logs (indicated by `pool_pre_ping=True` logs).

### 3.3 Media Storage Backups
Since raw patient screening videos are stored locally at `/data/videos` (or target path defined in `.env`), this folder **must** be mounted to a high-capacity storage drive and backed up periodically using automated cron jobs (e.g. synched to AWS S3 using the configured credentials).
