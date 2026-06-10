from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean,
    DateTime, Text, JSON, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Models ────────────────────────────────────────────────────────────────────

class Child(Base):
    __tablename__ = "children"
    id            = Column(String, primary_key=True)
    name          = Column(String(100), nullable=False)
    age_months    = Column(Integer, nullable=False)
    gender        = Column(String(10))
    language      = Column(String(5), default="en")
    doctor_id     = Column(String, ForeignKey("doctors.id"), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    sessions      = relationship("Session", back_populates="child")

class Session(Base):
    __tablename__ = "sessions"
    id                   = Column(String, primary_key=True)
    child_id             = Column(String, ForeignKey("children.id"), nullable=False)
    started_at           = Column(DateTime, default=datetime.utcnow)
    video_path           = Column(String, nullable=True)

    # Raw behavioral data (JSON arrays)
    gaze_task_a          = Column(JSON, default=list)   # social preference
    gaze_task_b          = Column(JSON, default=list)   # name response
    name_trials          = Column(JSON, default=list)
    gaze_task_c          = Column(JSON, default=list)   # imitation
    bubble_events        = Column(JSON, default=list)

    # Questionnaire
    questionnaire_type   = Column(String(20))  # mchat_r | indt_asd
    questionnaire_score  = Column(Integer)
    questionnaire_answers= Column(JSON, default=dict)
    questionnaire_risk   = Column(String(10))  # low | medium | high
    questionnaire_norm   = Column(Float)       # 0-1 normalised score

    # Behavioral scores (computed server-side)
    social_gaze_ratio    = Column(Float)       # Task A — Perochon 2023
    name_response_rate   = Column(Float)       # Task B — 0-1
    expression_rate      = Column(Float)       # AU6+AU12 from OpenFace
    blink_rate_bpm       = Column(Float)
    repetitive_score     = Column(Float)       # ASDMotion output

    # Combined risk
    combined_risk_score  = Column(Float)       # 0-1
    risk_level           = Column(String(10))  # low | medium | high
    flagged              = Column(Boolean, default=False)

    processing_status    = Column(String(20), default="pending")
    # pending | processing | done | error | completed_fallback
    processing_error     = Column(Text, nullable=True)
    processing_note      = Column(Text, nullable=True)

    # Doctor judgment
    doctor_judgment      = Column(String(20), nullable=True)
    # typical | monitoring | high_concern | refer_immediately
    doctor_notes         = Column(Text, nullable=True)
    doctor_reviewed_at   = Column(DateTime, nullable=True)

    child = relationship("Child", back_populates="sessions")

class Doctor(Base):
    __tablename__ = "doctors"
    id         = Column(String, primary_key=True)
    name       = Column(String(100))
    email      = Column(String(200), unique=True)
    password   = Column(String(200))  # bcrypt hashed
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

if engine.dialect.name == "postgresql":
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS processing_note TEXT"))
        conn.commit()
