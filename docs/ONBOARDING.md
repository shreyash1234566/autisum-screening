# Developer Onboarding & Workstation Setup Checklist

This guide helps you set up a local development environment for the AutiScreen platform.

---

## 1. Prerequisites

Before starting, ensure your system has the following installed:
* **Docker & Docker Desktop** (Required for database and test pipeline execution).
* **Python 3.11** (Backend API & ML modules).
* **Node.js (v18+) & npm** (Dashboard React app).
* **Flutter SDK (v3.x)** (Only if working on the native mobile capture application).
* **Git** (Version control).

---

## 2. Step-by-Step Environment Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-org/Autism-Screening.git
cd Autism-Screening
```

### Step 2: Configure Environment Variables
Copy the example configuration to create your local `.env` file:
* **On Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
* **On macOS/Linux:**
  ```bash
  cp .env.example .env
  ```

*Open `.env` and verify the values. For local running without Docker, you will need to change the database host from `db` to `localhost` (e.g., `postgresql://autism_user:autism_pass@localhost:5432/autism_db`).*

### Step 3: Spin Up Database & Infrastructure
Launch PostgreSQL using the Docker compose file:
```bash
docker compose up -d db
```
This boots a PostgreSQL database listening on port `5432` with username `autism_user` and database `autism_db`.

### Step 4: Backend Setup
1. Create a Python virtual environment and activate it:
   * **Windows:**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * **macOS/Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run the API database migration initialization:
   The database tables will be automatically initialized when starting the FastAPI server.

### Step 5: Frontend Dashboard Setup
1. Navigate to the dashboard directory:
   ```bash
   cd dashboard
   ```
2. Install npm packages:
   ```bash
   npm install
   ```

---

## 3. Running the Applications

### Launch Backend API
Ensure you are in the `backend` directory with your virtual environment active:
```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
* Interactive API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
* Schema definition will be at [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json).

### Launch Frontend Dashboard
Navigate to the `dashboard` directory:
```bash
npm run dev
```
* The dashboard will launch locally (typically at [http://localhost:5173](http://localhost:5173)).

---

## 4. Running the Test Suite

Always verify your environment setup by executing the full containerized test pipeline:
```bash
docker compose -f tests/docker-compose.test.yml up --build --exit-code-from test-runner
```
If you see `36 passed` at the end, your local workstation is fully set up and ready!

---

## 5. Machine Learning Dependencies (Optional)
By default, the backend runs in a hardened mock fallback state if the heavy computer vision and movement tracking tools are missing. If you need to perform real clinical analysis:
1. **OpenFace:** Install OpenFace 2.2.0 binaries on your host system and update `OPENFACE_BIN` in `.env` to point to the `FeatureExtraction` executable.
2. **ASDMotion:** Clone the ASDMotion codebase into the path specified by `ASDMOTION_PATH` in `.env`.
