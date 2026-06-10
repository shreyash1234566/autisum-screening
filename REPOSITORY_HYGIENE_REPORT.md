# Repository Hygiene Report

This document records the results of our repository hygiene audit. It catalogs ignored files, checks for improperly tracked build or cache artifacts, and documents any cleanup actions.

---

## 1. Audit of Ignored & Tracked Artifacts

We verified the local directory contents against the active `.gitignore` configurations.

### Ignored Files Physically Present:
The following files/directories are present but correctly ignored by Git:
* **Python Cache & Artifacts:**
  * `backend/.coverage`
  * `backend/.pytest_cache/`
  * `backend/.ruff_cache/`
  * `backend/__pycache__/`
  * `backend/ml/__pycache__/`
  * `backend/routers/__pycache__/`
  * `backend/services/__pycache__/`
  * `tests/.pytest_cache/`
  * `tests/backend/__pycache__/`
  * `tests/integration/__pycache__/`
* **Local Configuration & Logs:**
  * `.env`
  * `buildlog.txt`
* **Flutter & Mobile Build Caches:**
  * `mobile/.dart_tool/`
  * `mobile/.flutter-plugins-dependencies`
  * `mobile/android/.gradle/`
  * `mobile/android/gradle/wrapper/gradle-wrapper.jar`
  * `mobile/android/gradlew`
  * `mobile/android/gradlew.bat`
  * `mobile/android/local.properties`
  * `mobile/build/`
  * `mobile/pubspec.lock`

### Checking for Tracked Garbage:
We scanned the Git index (`git ls-files`) for any files that match ignore patterns but are still tracked.
* **Command:**
  ```bash
  git ls-files | findstr /i "pycache pytest_cache node_modules build dist env .log .db"
  ```
* **Tracked Matches Found:**
  * `.env.example` (Tracked — Correct, serves as configuration template)
  * `mobile/android/app/build.gradle` (Tracked — Correct, mobile app gradle configuration)
  * `mobile/android/build.gradle` (Tracked — Correct, mobile gradle configuration)
* **Status:** No tracked garbage exists. No cleanup actions were required.

---

## 2. Action Log

* **Cleanup Action:** None required. All cache, temporary, and build folders are successfully ignored and untracked.
* **Verification Status:** **PASS**
