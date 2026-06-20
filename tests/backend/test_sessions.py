import io
import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from database import Child, Session as SessionModel
from ml.scoring_thresholds import score_gaze, score_name_response, score_expression, combined_risk


def test_scoring_math():
    """Unit test the scoring calculations from scoring_thresholds.py."""
    # 1. Gaze Risk
    assert score_gaze(0.60) == 0.0
    assert score_gaze(0.40) == 1.0
    # Linear interpolation: midway between 0.45 and 0.55 should be 0.5
    assert pytest.approx(score_gaze(0.50)) == 0.5

    # 2. Name Response
    assert score_name_response(0.80) == 0.0
    assert score_name_response(0.20) == 1.0
    # Midway between 0.33 and 0.67 is 0.5. Result should be 0.5
    assert pytest.approx(score_name_response(0.50)) == 0.5

    # 3. Expression Risk
    # Floor is 0.30. 0.15 smile rate should yield 0.5 risk
    assert pytest.approx(score_expression(0.15)) == 0.5
    assert score_expression(0.35) == 0.0

    # 4. Combined Risk
    # Weights: Q=0.40, gaze=0.30, name=0.20, expr=0.10
    # Low-risk scenario: all low (0.0) -> combined should be 0.0 (low risk)
    low_res = combined_risk(0.0, 0.0, 0.0, 0.0)
    assert low_res["combined_score"] == 0.0
    assert low_res["risk_level"] == "low"
    assert low_res["flagged"] is False

    # High-risk scenario: Q=1.0, Gaze=1.0, Name=1.0, Expr=1.0 -> combined should be 1.0
    high_res = combined_risk(1.0, 1.0, 1.0, 1.0)
    assert high_res["combined_score"] == 1.0
    assert high_res["risk_level"] == "high"
    assert high_res["flagged"] is True


def test_upload_session_success(client, db_session):
    """Test session upload endpoint accepts metadata and queues processing."""
    # Seed child first
    child = Child(id="child-test-123", name="Priya Patel", age_months=24, gender="female", language="en")
    db_session.add(child)
    db_session.commit()

    # Create dummy session JSON file contents
    session_data = {
        "session_id": "session-test-999",
        "child_id": "child-test-123",
        "started_at": datetime.utcnow().isoformat(),
        "questionnaire_type": "mchat_r",
        "questionnaire_score": 5,
        "questionnaire_answers": {"Q1": 0, "Q2": 1},
        "gaze_task_a": [{"timestamp_ms": 100, "gaze_ratio_horizontal": 0.3}],
        "name_trials": [{"trial_number": 1, "response_detected": True}]
    }
    
    session_json_file = io.BytesIO(json.dumps(session_data).encode("utf-8"))
    video_file = io.BytesIO(b"dummy_video_bytes")

    files = {
        "session_json": ("session.json", session_json_file, "application/json"),
        "video": ("video.mp4", video_file, "video/mp4")
    }

    with patch("routers.sessions.save_video") as mock_save, \
         patch("routers.sessions._process_session") as mock_process:
        
        mock_save.return_value = "/tmp/dummy/video.mp4"
        
        response = client.post("/sessions/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session-test-999"
        assert data["status"] == "accepted"

        # Verify initial database insertion
        sess_db = db_session.query(SessionModel).filter(SessionModel.id == "session-test-999").first()
        assert sess_db is not None
        assert sess_db.child_id == "child-test-123"
        assert sess_db.questionnaire_type == "mchat_r"
        assert sess_db.questionnaire_score == 5
        assert sess_db.processing_status == "pending"


def test_upload_session_invalid_child(client, db_session):
    """Test session upload returns 400 if child_id does not exist."""
    session_data = {
        "session_id": "session-test-888",
        "child_id": "nonexistent-child-123",
        "questionnaire_type": "mchat_r",
        "questionnaire_score": 5
    }
    session_json_file = io.BytesIO(json.dumps(session_data).encode("utf-8"))
    files = {
        "session_json": ("session.json", session_json_file, "application/json")
    }
    response = client.post("/sessions/upload", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Child not found"


def test_upload_session_duplicate_id(client, db_session):
    """Test session upload returns 400 if session_id already exists."""
    child = Child(id="child-test-123", name="Priya Patel", age_months=24, gender="female", language="en")
    db_session.add(child)
    
    sess = SessionModel(id="session-existing-111", child_id="child-test-123", processing_status="done")
    db_session.add(sess)
    db_session.commit()

    session_data = {
        "session_id": "session-existing-111",
        "child_id": "child-test-123",
        "questionnaire_type": "mchat_r",
        "questionnaire_score": 5
    }
    session_json_file = io.BytesIO(json.dumps(session_data).encode("utf-8"))
    files = {
        "session_json": ("session.json", session_json_file, "application/json")
    }
    response = client.post("/sessions/upload", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Session already exists"


def test_upload_session_invalid_timestamp(client, db_session):
    """Test session upload returns 400 if started_at is invalid ISO string."""
    child = Child(id="child-test-123", name="Priya Patel", age_months=24, gender="female", language="en")
    db_session.add(child)
    db_session.commit()

    session_data = {
        "session_id": "session-test-777",
        "child_id": "child-test-123",
        "started_at": "invalid-date-format-123"
    }
    session_json_file = io.BytesIO(json.dumps(session_data).encode("utf-8"))
    files = {
        "session_json": ("session.json", session_json_file, "application/json")
    }
    response = client.post("/sessions/upload", files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid started_at ISO format"


def test_process_session_fallback_missing_video(db_session):
    """
    Test background processing handles missing video gracefully.

    FIX: this used to construct SessionModel(video_path=...) and call
    _process_session(session_id, "<single path string>") -- both part of
    the old single-video API. The app now records three separate clips
    (Task A/B/C), so SessionModel takes video_task_a/b/c_path, and
    _process_session takes a dict of {"task_a": path, ...}.

    FIX: also updated the expected outcome. There never was a real
    "completed_fallback" code path in routers/sessions.py (that string only
    ever existed in a stale comment in database.py) -- a missing/unreadable
    video has always meant "completed", with the gap explained in
    processing_note. Gaze ratio, name-response rate, and questionnaire score
    are 90% of the combined-risk weight and come entirely from on-device
    data already in the session JSON, so they don't depend on video at all
    -- only the 10%-weighted expression_rate does.
    """
    from routers.sessions import _process_session

    child = Child(id="child-test-123", name="Priya Patel", age_months=24, gender="female", language="en")
    db_session.add(child)

    sess = SessionModel(
        id="session-test-fallback",
        child_id="child-test-123",
        processing_status="pending",
        video_task_a_path="/nonexistent/path/to/video.mp4",
    )
    db_session.add(sess)
    db_session.commit()

    with patch("database.SessionLocal", return_value=db_session):
        _process_session(
            "session-test-fallback",
            {"task_a": "/nonexistent/path/to/video.mp4", "task_b": None, "task_c": None},
        )

    # Refresh DB session state
    db_session.expire_all()
    sess_db = db_session.query(SessionModel).filter(SessionModel.id == "session-test-fallback").first()

    assert sess_db.processing_status == "completed"
    assert "No video for: task_a, task_b, task_c" in sess_db.processing_note
    assert sess_db.processing_error is None
    assert sess_db.expression_rate == 0.0
    assert sess_db.repetitive_score == 0.0


def test_openface_fallback_mock(client, db_session):
    """Test that openface_service triggers fallback mock when binary is missing."""
    from services.openface_service import run_openface

    # Simulate FileNotFoundError when running the subprocess
    with patch("subprocess.run", side_effect=FileNotFoundError), \
         patch("os.path.exists", return_value=True):
        result = run_openface("/tmp/any_video.mp4")
        assert result is not None
        assert result.get("mock") is True
        assert result.get("expression_rate") == 0.0


def test_openface_parser_success(client):
    """
    Test that openface_service correctly parses a simulated CSV file output.

    FIX: the test CSV previously used flat columns (confidence, AU06_r,
    AU12_r, gaze_angle_x/y) that don't match what `openface detect-video`
    actually produces. The real output (openface-test package, demo.py
    process_video()) writes `face_detection` as a stringified
    [x1, y1, x2, y2, score] list and `action_units` as a stringified list of
    AU intensities -- there are no flat per-AU columns. _parse_openface_output
    parses exactly that real shape (see its docstring), so the test now
    constructs CSV rows in the real format instead of inventing one that
    never existed in production.
    """
    from services.openface_service import run_openface
    import tempfile
    import os

    # Mock subprocess.run to complete successfully
    mock_run = MagicMock()
    mock_run.returncode = 0

    with patch("subprocess.run", return_value=mock_run), \
         patch("os.path.exists", return_value=True), \
         patch("tempfile.TemporaryDirectory") as mock_tmp:

        # Setup fake temporary directory and output CSV file
        temp_dir = tempfile.mkdtemp()
        mock_tmp.return_value.__enter__.return_value = temp_dir

        csv_path = os.path.join(temp_dir, "features.csv")
        with open(csv_path, "w") as f:
            f.write("timestamp,face_detection,action_units,gaze_yaw,gaze_pitch\n")
            # Frame 1: confidence 0.9 (>=0.8, kept), genuine smile: AU6=1.2 (idx3), AU12=1.8 (idx6)
            f.write('0.033,"[10,10,50,50,0.9]","[0,0,0,1.2,0,0,1.8]",-0.05,0.04\n')
            # Frame 2: confidence 0.5 (<0.8, should be skipped)
            f.write('0.066,"[10,10,50,50,0.5]","[0,0,0,1.5,0,0,2.0]",-0.05,0.04\n')
            # Frame 3: confidence 0.85 (>=0.8, kept), no smile: AU6=0.2, AU12=0.4
            f.write('0.100,"[10,10,50,50,0.85]","[0,0,0,0.2,0,0,0.4]",-0.05,0.04\n')

        result = run_openface("/tmp/test_video.mp4")
        assert result is not None
        assert result["total_frames"] == 2  # frame 1 and frame 3 (frame 2's confidence < 0.8)
        assert result["smile_frames"] == 1  # frame 1 only
        assert result["expression_rate"] == 0.5  # 1 out of 2 frames
        assert result["mean_au6"] == 0.7  # (1.2 + 0.2) / 2
        assert result["mean_au12"] == 1.1  # (1.8 + 0.4) / 2

        # Clean up temp files
        try:
            os.remove(csv_path)
            os.rmdir(temp_dir)
        except OSError:
            pass


def test_get_session_details(client, db_session):
    """Test retrieving session details by ID."""
    # Seed session
    sess = SessionModel(
        id="session-test-id",
        child_id="child-some-id",
        processing_status="done",
        risk_level="medium",
        flagged=False,
        combined_risk_score=0.35,
        social_gaze_ratio=0.52,
        name_response_rate=0.67,
        expression_rate=0.15,
        questionnaire_score=3,
        questionnaire_type="mchat_r",
        questionnaire_risk="medium"
    )
    db_session.add(sess)
    db_session.commit()

    response = client.get("/sessions/session-test-id")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "session-test-id"
    assert data["risk_level"] == "medium"
    assert data["combined_risk_score"] == 0.35
    assert data["social_gaze_ratio"] == 0.52
    assert data["name_response_rate"] == 0.67
    assert data["expression_rate"] == 0.15
    assert data["questionnaire_score"] == 3
    assert data["questionnaire_type"] == "mchat_r"
    assert data["questionnaire_risk"] == "medium"


def test_upload_session_missing_child_id(client, db_session):
    """Test session upload returns 400 if child_id is omitted or empty."""
    session_data = {
        "session_id": "session-test-889",
        "questionnaire_type": "mchat_r",
        "questionnaire_score": 5
    }
    session_json_file = io.BytesIO(json.dumps(session_data).encode("utf-8"))
    files = {
        "session_json": ("session.json", session_json_file, "application/json")
    }
    response = client.post("/sessions/upload", files=files)
    assert response.status_code == 400
    assert "child_id" in response.json()["detail"]


def test_upload_session_empty_payload(client):
    """Test session upload returns 422 for completely empty or missing file inputs."""
    response = client.post("/sessions/upload")
    assert response.status_code == 422


def test_get_session_not_found(client):
    """Test get session details returns 404 if session does not exist."""
    response = client.get("/sessions/non-existent-session-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def test_upload_session_indt_asd(client, db_session):
    """Test session upload with INDT-ASD questionnaire type works."""
    child = Child(id="child-test-indt", name="Indt Kid", age_months=30, gender="other", language="en")
    db_session.add(child)
    db_session.commit()

    session_data = {
        "session_id": "session-test-indt-999",
        "child_id": "child-test-indt",
        "questionnaire_type": "indt_asd",
        "questionnaire_score": 30,
        "questionnaire_answers": {"q1": 1}
    }
    session_json_file = io.BytesIO(json.dumps(session_data).encode("utf-8"))
    files = {
        "session_json": ("session.json", session_json_file, "application/json")
    }
    with patch("routers.sessions.save_video") as mock_save, \
         patch("routers.sessions._process_session") as mock_process:
        mock_save.return_value = "/tmp/dummy/video.mp4"
        response = client.post("/sessions/upload", files=files)
        assert response.status_code == 200

        sess_db = db_session.query(SessionModel).filter(SessionModel.id == "session-test-indt-999").first()
        assert sess_db is not None
        assert sess_db.questionnaire_type == "indt_asd"
        assert sess_db.questionnaire_score == 30
        assert sess_db.questionnaire_risk == "medium"
        assert sess_db.questionnaire_norm == pytest.approx(30 / 112.0)


def test_video_service(tmp_path):
    """
    Test video_service save, path, and exists functions.

    FIX: save_video/get_video_path/video_exists now take a required `task`
    parameter (one of task_a/task_b/task_c), since each session can have up
    to three separate clips instead of one.
    """
    from services.video_service import save_video, get_video_path, video_exists
    from config import settings

    # Temporarily override video storage path
    original_path = settings.VIDEO_STORAGE_PATH
    settings.VIDEO_STORAGE_PATH = str(tmp_path)

    try:
        session_id = "test-video-sess-123"
        dummy_bytes = b"dummy video bytes payload"

        path = save_video(dummy_bytes, session_id, "task_a")
        assert video_exists(session_id, "task_a") is True
        assert get_video_path(session_id, "task_a") == path

        # Read back bytes
        with open(path, "rb") as f:
            assert f.read() == dummy_bytes

        # Other tasks for this session haven't been saved
        assert video_exists(session_id, "task_b") is False
        assert video_exists("nonexistent-session", "task_a") is False
    finally:
        settings.VIDEO_STORAGE_PATH = original_path


def test_scoring_service_edge_cases(db_session):
    """Test compute_gaze_ratio and compute_name_response_rate empty branches, and run_full_scoring INDT-ASD path."""
    from services.scoring_service import compute_gaze_ratio, compute_name_response_rate, run_full_scoring
    
    assert compute_gaze_ratio([]) == 0.5
    assert compute_name_response_rate([]) == 0.0
    
    child = Child(id="child-test-987", name="Score Kid", age_months=30, gender="other", language="en")
    db_session.add(child)
    
    sess = SessionModel(
        id="session-test-scoring",
        child_id="child-test-987",
        questionnaire_type="indt_asd",
        questionnaire_score=40,
        questionnaire_risk="high",
        gaze_task_a=[{"timestamp_ms": 100, "blink_ear": 0.1}], # <2 frames blink rate
        name_trials=[]
    )
    db_session.add(sess)
    db_session.commit()
    
    scores = run_full_scoring(sess, {}, {})
    assert scores["repetitive_score"] == 0.0
    assert scores["questionnaire_type"] == "indt_asd"
    assert scores["questionnaire_score"] == 40
    assert scores["blink_rate_bpm"] == 0.0 # because <2 frames


def test_scoring_service_normal(db_session):
    """Test normal path of scoring service with valid gaze, name, and mchat_r questionnaire."""
    from services.scoring_service import run_full_scoring
    
    child = Child(id="child-test-normal", name="Normal Kid", age_months=24, gender="male", language="en")
    db_session.add(child)
    
    sess = SessionModel(
        id="session-test-scoring-normal",
        child_id="child-test-normal",
        questionnaire_type="mchat_r",
        questionnaire_score=5,
        questionnaire_risk="medium",
        gaze_task_a=[
            {"timestamp_ms": 0, "gaze_ratio_horizontal": 0.3, "blink_ear": 0.25},
            {"timestamp_ms": 30000, "gaze_ratio_horizontal": 0.7, "blink_ear": 0.1}
        ],
        name_trials=[{"trial_number": 1, "response_detected": True}]
    )
    db_session.add(sess)
    db_session.commit()
    
    # FIX: run_full_scoring now takes a dict of per-task results
    # ({"task_a": {...}, "task_b": {...}, "task_c": {...}}), not one flat
    # dict, since the app records three separate clips. total_frames/
    # total_segments must be present and > 0 for a task's result to be
    # picked up by the frame/segment-weighted average in scoring_service.py
    # -- a dict with no frame/segment count is treated as having no usable
    # data for that task (matches what a real openface/asdmotion result
    # always includes).
    scores = run_full_scoring(
        sess,
        {"task_a": {"total_frames": 10, "expression_rate": 0.2}},
        {"task_a": {"total_segments": 5, "repetitive_score": 0.1}},
    )
    assert scores["repetitive_score"] == 0.1
    assert scores["expression_rate"] == 0.2
    assert scores["questionnaire_type"] == "mchat_r"
    assert scores["questionnaire_score"] == 5
    assert scores["blink_rate_bpm"] == 2.0


def test_process_session_exception_handling(db_session):
    """Test that background task handles unhandled exceptions gracefully and sets status = 'error'."""
    from routers.sessions import _process_session
    
    child = Child(id="child-test-err", name="Error Kid", age_months=24, gender="female", language="en")
    db_session.add(child)
    
    sess = SessionModel(
        id="session-test-error-handling",
        child_id="child-test-err",
        processing_status="pending"
    )
    db_session.add(sess)
    db_session.commit()
    
    # Force run_full_scoring to raise an exception
    with patch("routers.sessions.run_full_scoring", side_effect=ValueError("Scoring math blew up")), \
         patch("database.SessionLocal", return_value=db_session):
        _process_session("session-test-error-handling", None)
        
    db_session.expire_all()
    sess_db = db_session.query(SessionModel).filter(SessionModel.id == "session-test-error-handling").first()
    assert sess_db.processing_status == "error"
    assert "Scoring math blew up" in sess_db.processing_error
    assert sess_db.processing_note == "An unrecoverable execution error occurred."


def test_asdmotion_service_errors():
    """
    Test run_asdmotion's failure/fallback paths.

    FIX: this used to mock subprocess.run and inspect its stderr/returncode/
    stdout, testing a design (call out to a separate ASDMotion process,
    parse its JSON stdout) that was replaced -- the real ASDMotion repo
    needs OpenPose + MMAction2 + GPU + Google-Drive-only weights, none of
    which docker-compose build can produce (see asdmotion_service.py's
    module docstring for the full audit). The actual implementation runs
    MediaPipe Pose in-process via cv2.VideoCapture; there is no subprocess
    at all, so these tests now mock cv2/os.path.exists instead.
    """
    from services.asdmotion_service import run_asdmotion

    # 1. Path doesn't exist at all -> mock with video_not_found
    res = run_asdmotion("/tmp/does_not_exist.mp4")
    assert res.get("mock") is True
    assert res.get("error") == "video_not_found"
    assert res.get("repetitive_score") == 0.0

    # 2. Path exists but cv2 can't open it (corrupt/unreadable file)
    with patch("os.path.exists", return_value=True), \
         patch("cv2.VideoCapture") as mock_cap_cls:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cap_cls.return_value = mock_cap

        res = run_asdmotion("/tmp/corrupt.mp4")
        assert res.get("mock") is True
        assert res.get("error") == "video_unreadable"
        assert res.get("repetitive_score") == 0.0

    # 3. Video opens but is too short for one analysis window (150 frames)
    import cv2 as real_cv2
    with patch("os.path.exists", return_value=True), \
         patch("cv2.VideoCapture") as mock_cap_cls:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: 30.0 if prop == real_cv2.CAP_PROP_FPS else 50
        mock_cap_cls.return_value = mock_cap

        res = run_asdmotion("/tmp/too_short.mp4")
        assert res.get("mock") is None  # not a mock result -- a real "too short" result
        assert res.get("note") == "video_too_short"
        assert res.get("repetitive_score") == 0.0

    # 4. mediapipe not installed -> ImportError caught, falls back to mock
    with patch("os.path.exists", return_value=True), \
         patch("cv2.VideoCapture") as mock_cap_cls:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        # CAP_PROP_FPS=30.0, CAP_PROP_FRAME_COUNT=200 (enough for one window)
        mock_cap.get.side_effect = lambda prop: 30.0 if prop == real_cv2.CAP_PROP_FPS else 200
        mock_cap_cls.return_value = mock_cap

        with patch.dict("sys.modules", {"mediapipe": None}):
            res = run_asdmotion("/tmp/no_mediapipe.mp4")
            assert res.get("mock") is True
            assert res.get("repetitive_score") == 0.0


def test_upload_session_invalid_session_id_format(client, db_session):
    """Test that uploading a session with invalid session_id (e.g. path traversal) fails."""
    import io
    import json
    # Register child first
    child_payload = {
        "id": "child-valid-sess-check",
        "name": "Jane",
        "age_months": 24,
        "gender": "F"
    }
    client.post("/children", json=child_payload)

    session_data = {
        "session_id": "../../invalid_id",
        "child_id": "child-valid-sess-check",
        "started_at": "2026-06-10T14:15:00Z"
    }
    payload_file = io.BytesIO(json.dumps(session_data).encode("utf-8"))
    
    r = client.post(
        "/sessions/upload",
        files={
            "session_json": ("session.json", payload_file, "application/json")
        }
    )
    assert r.status_code == 400
    assert "Invalid session_id format" in r.json()["detail"]

