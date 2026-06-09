import json, uuid, logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db, Session as SessionModel
from services.video_service import save_video
from services.openface_service import run_openface
from services.asdmotion_service import run_asdmotion
from services.scoring_service import run_full_scoring

router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_session(
    background_tasks: BackgroundTasks,
    session_json: UploadFile = File(...),
    video: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    # Parse session JSON from Flutter
    raw = await session_json.read()
    data = json.loads(raw)

    session_id = data.get("session_id") or str(uuid.uuid4())

    # Save video bytes if provided
    video_path = None
    if video and video.filename:
        video_bytes = await video.read()
        video_path = save_video(video_bytes, session_id)

    # Parse questionnaire result
    q_answers = data.get("questionnaire_answers", {})
    q_score   = data.get("questionnaire_score", 0)
    q_type    = data.get("questionnaire_type", "unknown")

    # Quick questionnaire risk level
    if q_type == "mchat_r":
        q_risk = "low" if q_score <= 2 else ("medium" if q_score <= 7 else "high")
        q_norm = q_score / 20.0
    elif q_type == "indt_asd":
        q_risk = "low" if q_score < 25 else ("medium" if q_score < 36 else "high")
        q_norm = q_score / 112.0
    else:
        q_risk = "unknown"; q_norm = 0.5

    session = SessionModel(
        id=session_id,
        child_id=data["child_id"],
        started_at=datetime.fromisoformat(data.get("started_at", datetime.utcnow().isoformat())),
        video_path=video_path,
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

    # Queue background processing
    background_tasks.add_task(_process_session, session_id, video_path)

    return {"session_id": session_id, "status": "accepted"}


def _process_session(session_id: str, video_path: str | None):
    """Background task: OpenFace + ASDMotion + scoring."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return

        session.processing_status = "processing"
        db.commit()

        # OpenFace
        openface_result = run_openface(video_path) if video_path else {}
        openface_result = openface_result or {}

        # ASDMotion
        asdmotion_result = run_asdmotion(video_path) if video_path else {}
        asdmotion_result = asdmotion_result or {}

        # Scoring
        scores = run_full_scoring(session, openface_result, asdmotion_result)

        # Write back
        session.social_gaze_ratio   = scores["social_gaze_ratio"]
        session.name_response_rate  = scores["name_response_rate"]
        session.expression_rate     = scores["expression_rate"]
        session.blink_rate_bpm      = scores["blink_rate_bpm"]
        session.repetitive_score    = scores["repetitive_score"]
        session.combined_risk_score = scores["combined_score"]
        session.risk_level          = scores["risk_level"]
        session.flagged             = scores["flagged"]
        session.processing_status   = "done"
        db.commit()
        logger.info(f"Session {session_id} processed: {scores['risk_level']}")

    except Exception as e:
        logger.exception(f"Processing failed for {session_id}: {e}")
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if session:
            session.processing_status = "error"
            session.processing_error = str(e)[:500]
            db.commit()
    finally:
        db.close()


@router.get("/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    s = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not s:
        raise HTTPException(404, "Session not found")
    return {
        "id": s.id, "child_id": s.child_id,
        "processing_status": s.processing_status,
        "risk_level": s.risk_level,
        "flagged": s.flagged,
        "combined_risk_score": s.combined_risk_score,
        "social_gaze_ratio":   s.social_gaze_ratio,
        "name_response_rate":  s.name_response_rate,
        "expression_rate":     s.expression_rate,
        "questionnaire_score": s.questionnaire_score,
        "questionnaire_type":  s.questionnaire_type,
        "questionnaire_risk":  s.questionnaire_risk,
    }
