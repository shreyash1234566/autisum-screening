from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import get_db, Session as SessionModel, Child

router = APIRouter(prefix="/doctor", tags=["doctor"])

class JudgmentIn(BaseModel):
    judgment: str   # typical | monitoring | high_concern | refer_immediately
    notes: Optional[str] = None

class SessionSummary(BaseModel):
    id: str
    child_name: str
    child_age_months: int
    started_at: datetime
    risk_level: Optional[str]
    combined_risk_score: Optional[float]
    flagged: Optional[bool]
    processing_status: str
    questionnaire_type: Optional[str]
    questionnaire_score: Optional[int]
    questionnaire_risk: Optional[str]
    social_gaze_ratio: Optional[float]
    name_response_rate: Optional[float]
    expression_rate: Optional[float]
    repetitive_score: Optional[float]
    doctor_judgment: Optional[str]

    class Config:
        from_attributes = True

@router.get("/flagged", response_model=List[SessionSummary])
def get_flagged_sessions(db: Session = Depends(get_db)):
    """Return all sessions flagged for doctor review, newest first."""
    rows = (
        db.query(SessionModel, Child)
        .join(Child, SessionModel.child_id == Child.id)
        .filter(SessionModel.flagged)
        .order_by(SessionModel.started_at.desc())
        .all()
    )
    return [_to_summary(s, c) for s, c in rows]

@router.get("/all", response_model=List[SessionSummary])
def get_all_sessions(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(SessionModel, Child)
        .join(Child, SessionModel.child_id == Child.id)
        .order_by(SessionModel.started_at.desc())
        .limit(limit)
        .all()
    )
    return [_to_summary(s, c) for s, c in rows]

@router.post("/{session_id}/judgment")
def submit_judgment(
    session_id: str,
    body: JudgmentIn,
    db: Session = Depends(get_db),
):
    valid = {"typical", "monitoring", "high_concern", "refer_immediately"}
    if body.judgment not in valid:
        raise HTTPException(422, f"judgment must be one of {valid}")

    s = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not s:
        raise HTTPException(404, "Session not found")

    s.doctor_judgment    = body.judgment
    s.doctor_notes       = body.notes
    s.doctor_reviewed_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "judgment": body.judgment}

def _to_summary(s: SessionModel, c: Child) -> dict:
    return {
        "id": s.id,
        "child_name": c.name,
        "child_age_months": c.age_months,
        "started_at": s.started_at,
        "risk_level": s.risk_level,
        "combined_risk_score": s.combined_risk_score,
        "flagged": s.flagged,
        "processing_status": s.processing_status,
        "questionnaire_type": s.questionnaire_type,
        "questionnaire_score": s.questionnaire_score,
        "questionnaire_risk": s.questionnaire_risk,
        "social_gaze_ratio": s.social_gaze_ratio,
        "name_response_rate": s.name_response_rate,
        "expression_rate": s.expression_rate,
        "repetitive_score": s.repetitive_score,
        "doctor_judgment": s.doctor_judgment,
    }
