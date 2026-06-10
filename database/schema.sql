-- AutiScreen PostgreSQL schema
-- SQLAlchemy creates this automatically via Base.metadata.create_all()
-- This file is for reference and manual setup

CREATE TABLE IF NOT EXISTS doctors (
    id          VARCHAR PRIMARY KEY,
    name        VARCHAR(100),
    email       VARCHAR(200) UNIQUE,
    password    VARCHAR(200),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS children (
    id          VARCHAR PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    age_months  INTEGER NOT NULL,
    gender      VARCHAR(10),
    language    VARCHAR(5) DEFAULT 'en',
    doctor_id   VARCHAR REFERENCES doctors(id),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    id                    VARCHAR PRIMARY KEY,
    child_id              VARCHAR NOT NULL REFERENCES children(id),
    started_at            TIMESTAMP DEFAULT NOW(),
    video_path            VARCHAR,

    -- Raw behavioral JSON (from MediaPipe on-device)
    gaze_task_a           JSONB DEFAULT '[]',
    gaze_task_b           JSONB DEFAULT '[]',
    name_trials           JSONB DEFAULT '[]',
    gaze_task_c           JSONB DEFAULT '[]',
    bubble_events         JSONB DEFAULT '[]',

    -- Questionnaire (M-CHAT-R or AIIMS INDT-ASD)
    questionnaire_type    VARCHAR(20),
    questionnaire_score   INTEGER,
    questionnaire_answers JSONB DEFAULT '{}',
    questionnaire_risk    VARCHAR(10),
    questionnaire_norm    FLOAT,

    -- Behavioral scores (computed server-side)
    social_gaze_ratio     FLOAT,   -- Task A — Perochon 2023, cutoff 0.45
    name_response_rate    FLOAT,   -- Task B — 0-1, cutoff 0.33
    expression_rate       FLOAT,   -- OpenFace AU6>1.0 & AU12>1.5
    blink_rate_bpm        FLOAT,   -- EAR threshold 0.20
    repetitive_score      FLOAT,   -- ASDMotion output

    -- Combined risk (weights: Q=0.40, gaze=0.30, name=0.20, expr=0.10)
    combined_risk_score   FLOAT,
    risk_level            VARCHAR(10),
    flagged               BOOLEAN DEFAULT FALSE,

    -- Processing pipeline
    processing_status     VARCHAR(20) DEFAULT 'pending',
    processing_error      TEXT,
    processing_note       TEXT,

    -- Doctor judgment (becomes training label)
    doctor_judgment       VARCHAR(30),
    doctor_notes          TEXT,
    doctor_reviewed_at    TIMESTAMP
);

-- Index for fast dashboard queries
CREATE INDEX IF NOT EXISTS idx_sessions_flagged     ON sessions(flagged);
CREATE INDEX IF NOT EXISTS idx_sessions_child       ON sessions(child_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started     ON sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_processing  ON sessions(processing_status);
