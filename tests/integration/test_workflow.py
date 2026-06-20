import os
import io
import sys
import time
import pytest
import httpx
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))
if os.path.exists("/app"):
    sys.path.insert(0, "/app")

from main import app

@pytest.fixture(scope="module")
def api_client():
    """Provides an httpx Client pointing to a live server or an in-memory FastAPI instance."""
    base_url = os.getenv("API_BASE_URL")
    if base_url:
        print(f"Testing against live API server at {base_url}")
        with httpx.Client(base_url=base_url, timeout=30.0) as client:
            yield client
    else:
        print("Testing against in-memory FastAPI app")
        # In-memory test engine setup
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from database import Base, get_db

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        TestingSessionLocal = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        with httpx.Client(app=app, base_url="http://testserver", timeout=30.0) as client:
            yield client
        app.dependency_overrides.clear()


def test_full_patient_workflow(api_client):
    """
    Tests the complete user workflow:
    1. Register Child profile.
    2. Upload session JSON telemetry & video.
    3. Verify status transitions and scoring calculations.
    4. Submit doctor clinical judgment.
    5. Verify results stored in DB.
    """
    child_id = f"child-integration-{int(time.time())}"
    session_id = f"session-integration-{int(time.time())}"

    # ──── STEP 1: Register Child ────
    child_payload = {
        "id": child_id,
        "name": "Aradhya Sen",
        "age_months": 22,
        "gender": "female",
        "language": "hi",
        "doctor_id": None
    }
    
    r = api_client.post("/children", json=child_payload)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == child_id
    assert data["name"] == "Aradhya Sen"

    # ──── STEP 2: Upload Session ────
    session_json = {
        "session_id": session_id,
        "child_id": child_id,
        "started_at": "2026-06-10T12:00:00Z",
        "questionnaire_type": "mchat_r",
        "questionnaire_score": 9,  # High risk score
        "questionnaire_answers": {"q1": 1, "q2": 1, "q3": 0},
        # Simulate gaze preference: spending more time looking right (toy side)
        # horizontal ratios: mostly > 0.5 (right side)
        "gaze_task_a": [
            {"timestamp_ms": 100, "gaze_ratio_horizontal": 0.75, "gaze_ratio_vertical": 0.5, "head_yaw_degrees": 0.0, "head_pitch_degrees": 0.0, "blink_ear": 0.25},
            {"timestamp_ms": 200, "gaze_ratio_horizontal": 0.85, "gaze_ratio_vertical": 0.5, "head_yaw_degrees": 0.0, "head_pitch_degrees": 0.0, "blink_ear": 0.26},
            {"timestamp_ms": 300, "gaze_ratio_horizontal": 0.90, "gaze_ratio_vertical": 0.5, "head_yaw_degrees": 0.0, "head_pitch_degrees": 0.0, "blink_ear": 0.24}
        ],
        "name_trials": [
            {"trial_number": 1, "response_detected": False},
            {"trial_number": 2, "response_detected": False},
            {"trial_number": 3, "response_detected": False}
        ]
    }

    files = {
        "session_json": ("session.json", io_bytes(json_dumps(session_json)), "application/json"),
        # FIX: was a single "video" field. The backend now accepts
        # video_task_a/b/c (Tasks A/B/C each record their own clip; Task D
        # is touch-only). Using video_task_a here exercises the real upload
        # path instead of silently uploading to a field FastAPI ignores.
        "video_task_a": ("video.mp4", io_bytes(b"mock video data"), "video/mp4")
    }

    r = api_client.post("/sessions/upload", files=files)
    assert r.status_code == 200
    assert r.json()["session_id"] == session_id
    assert r.json()["status"] == "accepted"

    # ──── STEP 3: Wait / Poll for processing & assert calculations ────
    status = "pending"
    for _ in range(15):
        r = api_client.get(f"/sessions/{session_id}")
        assert r.status_code == 200
        res = r.json()
        status = res.get("processing_status")
        if status in ("completed", "error"):
            break
        time.sleep(1)

    # FIX: "done"/"completed_fallback" never existed as real values set by
    # routers/sessions.py -- the only success status it ever set is
    # "completed" (with processing_note explaining any missing/mock video
    # data). "mock video data" isn't a real MP4, so OpenFace/the pose
    # detector will both gracefully fall back for task_a -- that's fine,
    # since this assertion only cares that the session finished, not that
    # video analysis succeeded.
    assert status == "completed", f"Session processing failed or timed out. Last status: {status}"
    
    # Assert values calculated inside run_full_scoring
    assert res["risk_level"] == "high"
    assert res["flagged"] is True
    assert res["questionnaire_score"] == 9
    # Social preference gaze ratio calculation: all gaze_ratio_horizontal are > 0.5
    # So social gaze preference should be 0.0. score_gaze(0.0) yields 1.0 (high risk)
    assert res["social_gaze_ratio"] == 0.0
    # Name response rate is 0/3 trials = 0.0. score_name_response(0.0) yields 1.0 (high risk)
    assert res["name_response_rate"] == 0.0

    # ──── STEP 4: Submit Doctor Judgment ────
    judgment_payload = {
        "judgment": "refer_immediately",
        "notes": "Severe signs of social aversion. Refers to clinical diagnostics."
    }
    r = api_client.post(f"/doctor/{session_id}/judgment", json=judgment_payload)
    assert r.status_code == 200
    assert r.json() == {"ok": True, "judgment": "refer_immediately"}

    # ──── STEP 5: Verify Flagged status updates ────
    r = api_client.get("/doctor/flagged")
    assert r.status_code == 200
    flagged_sessions = r.json()
    assert any(s["id"] == session_id and s["doctor_judgment"] == "refer_immediately" for s in flagged_sessions)


def io_bytes(data: bytes) -> io.BytesIO:
    import io
    return io.BytesIO(data)

def json_dumps(data: dict) -> bytes:
    import json
    return json.dumps(data).encode("utf-8")
