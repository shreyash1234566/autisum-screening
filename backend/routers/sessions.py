import json
import logging
import os
import re
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db, Session as SessionModel, Child
from services.video_service import save_video
from services.openface_service import run_openface
from services.asdmotion_service import run_asdmotion
from services.scoring_service import run_full_scoring

router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)

# Tasks A, B, C each carry their own camera-recorded clip. Task D is
# touch-only (bubble-popping) and never produces a video.
TASK_NAMES = ("task_a", "task_b", "task_c")


@router.post("/upload")
async def upload_session(
    background_tasks: BackgroundTasks,
    session_json: UploadFile = File(...),
    # FIX: was a single `video` field. The app now records Tasks A/B/C as
    # three separate clips (previously only Task C's ever survived to this
    # point client-side -- see mobile app fix). Each is optional: a failed
    # recording on one task should not block the others or the session.
    video_task_a: UploadFile = File(None),
    video_task_b: UploadFile = File(None),
    video_task_c: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    raw = await session_json.read()
    data = json.loads(raw)

    session_id = data.get("session_id") or str(uuid.uuid4())

    if not re.match(r"^[a-zA-Z0-9_\-]+$", session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    # ── VALIDATION ──────────────────────────────────────────────────────────
    child_id = data.get("child_id")
    if not child_id:
        raise HTTPException(status_code=400, detail="child_id is required")

    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=400, detail="Child not found")

    existing_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if existing_session:
        raise HTTPException(status_code=400, detail="Session already exists")

    started_at_str = data.get("started_at")
    try:
        started_at = datetime.fromisoformat(started_at_str) if started_at_str else datetime.utcnow()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid started_at ISO format")

    # ── Save each task's video independently ────────────────────────────────
    # A missing/empty upload for one task just means that task's clip wasn't
    # recorded (e.g. permission denied, recorder failure) -- it does not
    # block saving the other two or the session itself.
    video_paths: dict[str, Optional[str]] = {"task_a": None, "task_b": None, "task_c": None}
    uploads = {"task_a": video_task_a, "task_b": video_task_b, "task_c": video_task_c}

    for task, upload in uploads.items():
        if upload is not None and upload.filename:
            video_bytes = await upload.read()
            if len(video_bytes) > 0:
                video_paths[task] = save_video(video_bytes, session_id, task)
            else:
                logger.warning(f"Session {session_id}: {task} upload present but empty (0 bytes)")

    # Parse questionnaire result
    q_answers = data.get("questionnaire_answers", {})
    q_score   = data.get("questionnaire_score", 0)
    q_type    = data.get("questionnaire_type", "unknown")

    if q_type == "mchat_r":
        q_risk = "low" if q_score <= 2 else ("medium" if q_score <= 7 else "high")
        q_norm = q_score / 20.0
    elif q_type == "indt_asd":
        q_risk = "low" if q_score < 25 else ("medium" if q_score < 36 else "high")
        q_norm = q_score / 112.0
    else:
        q_risk = "unknown"
        q_norm = 0.5

    session = SessionModel(
        id=session_id,
        child_id=child_id,
        started_at=started_at,
        video_task_a_path=video_paths["task_a"],
        video_task_b_path=video_paths["task_b"],
        video_task_c_path=video_paths["task_c"],
        gaze_task_a=data.get("gaze_task_a", []),
        gaze_task_b=data.get("gaze_task_b", []),
        name_trials=data.get("name_trials", []),
        gaze_task_c=data.get("gaze_task_c", []),
        bubble_events=data.get("bubble_events", []),
        questionnaire_type=q_type,
        questionnaire_score=q_score,
        questionnaire_answers=q_answers,
        questionnaire_risk=q_risk,
        questionnaire_norm=q_norm,
        processing_status="pending",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    background_tasks.add_task(_process_session, session_id, video_paths)

    return {"session_id": session_id, "status": "accepted"}


def _process_session(session_id: str, video_paths: dict):
    """
    Background task: run OpenFace + the MediaPipe-Pose movement detector on
    each of the (up to three) task clips independently, then combine.

    Design note on failure handling: gaze ratio, name-response rate, and
    questionnaire score together carry 90% of the combined-risk weight
    (see scoring_thresholds.py) and come entirely from on-device data already
    in the session JSON -- they do NOT depend on video at all. Only
    `expression_rate` (10% weight) needs server-side video analysis. So a
    missing/corrupt clip on one or even all three tasks degrades signal
    quality but should not discard an otherwise-valid screening session.
    The session is marked "error" only for genuine unhandled exceptions, not
    simply for absent video -- that case is "completed" with a
    processing_note explaining which tasks lacked usable video.
    """
    from database import SessionLocal
    db = SessionLocal()
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return

        session.processing_status = "processing"
        db.commit()

        # Defensive: a caller passing None (e.g. "no video info available at
        # all") should degrade to "every task missing", not crash before we
        # even get a chance to record that as a processing_note.
        video_paths = video_paths or {}

        per_task_analysis = {}
        openface_results  = {}
        asdmotion_results = {}
        missing_tasks      = []
        mock_tasks         = []

        for task in TASK_NAMES:
            video_path = video_paths.get(task)

            if not video_path or not os.path.exists(video_path):
                missing_tasks.append(task)
                openface_results[task]  = {"mock": True, "expression_rate": 0.0}
                asdmotion_results[task] = {"mock": True, "repetitive_score": 0.0}
                per_task_analysis[task] = {
                    "video_available": False,
                    "openface": openface_results[task],
                    "asdmotion": asdmotion_results[task],
                }
                continue

            of_result  = run_openface(video_path) or {}
            asd_result = run_asdmotion(video_path) or {}

            openface_results[task]  = of_result
            asdmotion_results[task] = asd_result

            if of_result.get("mock") is True or asd_result.get("mock") is True:
                mock_tasks.append(task)

            per_task_analysis[task] = {
                "video_available": True,
                "openface": of_result,
                "asdmotion": asd_result,
            }

        session.per_task_video_analysis = per_task_analysis

        # ── Combine the three tasks' results into the scoring inputs ────────
        scores = run_full_scoring(session, openface_results, asdmotion_results)

        session.social_gaze_ratio   = scores["social_gaze_ratio"]
        session.name_response_rate  = scores["name_response_rate"]
        session.expression_rate     = scores["expression_rate"]
        session.blink_rate_bpm      = scores["blink_rate_bpm"]
        session.repetitive_score    = scores["repetitive_score"]
        session.combined_risk_score = scores["combined_score"]
        session.risk_level          = scores["risk_level"]
        session.flagged             = scores["flagged"]

        if missing_tasks or mock_tasks:
            notes = []
            if missing_tasks:
                notes.append(f"No video for: {', '.join(missing_tasks)}.")
            if mock_tasks:
                notes.append(f"Video unusable (mock fallback) for: {', '.join(mock_tasks)}.")
            notes.append(
                "Risk score still computed from available gaze/name-response/"
                "questionnaire data (90% of combined weight is video-independent)."
            )
            session.processing_note = " ".join(notes)
        else:
            session.processing_note = "Real video analysis completed for all available tasks."

        session.processing_status = "completed"
        session.processing_error  = None
        db.commit()
        logger.info(
            f"Session {session_id} processed (completed): {scores['risk_level']} "
            f"missing={missing_tasks} mock={mock_tasks}"
        )

    except Exception as e:
        logger.exception(f"Processing failed for {session_id}: {e}")
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if session:
            session.processing_status = "error"
            session.processing_error  = str(e)[:500]
            session.processing_note   = "An unrecoverable execution error occurred."
            db.commit()
    finally:
        db.close()


@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    s = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not s:
        raise HTTPException(404, "Session not found")
    return {
        "id":                     s.id,
        "child_id":               s.child_id,
        "processing_status":      s.processing_status,
        "processing_note":        s.processing_note,
        "processing_error":       s.processing_error,
        "risk_level":             s.risk_level,
        "flagged":                s.flagged,
        "combined_risk_score":    s.combined_risk_score,
        "social_gaze_ratio":      s.social_gaze_ratio,
        "name_response_rate":     s.name_response_rate,
        "expression_rate":        s.expression_rate,
        "repetitive_score":       s.repetitive_score,
        "per_task_video_analysis": s.per_task_video_analysis,
        "questionnaire_score":    s.questionnaire_score,
        "questionnaire_type":     s.questionnaire_type,
        "questionnaire_risk":     s.questionnaire_risk,
    }
