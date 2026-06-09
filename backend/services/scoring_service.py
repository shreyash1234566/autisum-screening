"""
scoring_service.py
Combines all behavioral + questionnaire signals into a final risk score.
All weights and thresholds from cited research papers in scoring_thresholds.py
"""
import logging
from typing import Optional
from ml.scoring_thresholds import (
    score_gaze, score_name_response, score_expression,
    score_questionnaire_mchat, score_questionnaire_indt,
    combined_risk, INDT_ASD_CUTOFF,
)

logger = logging.getLogger(__name__)


def compute_gaze_ratio(gaze_task_a: list) -> float:
    """
    Social preference ratio from Task A gaze data.
    social_ratio = frames looking LEFT (social side) / total frames
    Source: Perochon et al. 2023
    """
    if not gaze_task_a:
        return 0.5   # neutral — insufficient data

    social_frames = sum(
        1 for p in gaze_task_a
        if p.get("gaze_ratio_horizontal", 0.5) < 0.5
    )
    return social_frames / len(gaze_task_a)


def compute_name_response_rate(name_trials: list) -> float:
    """
    Proportion of name-call trials with detected response (0-1).
    Source: Perochon et al. 2023 — 3 trials, 3-second window
    """
    if not name_trials:
        return 0.0
    responses = sum(1 for t in name_trials if t.get("response_detected", False))
    return responses / len(name_trials)


def run_full_scoring(session_db, openface_result: dict, asdmotion_result: dict) -> dict:
    """
    Master scoring function. Called after video analysis completes.

    session_db: SQLAlchemy Session ORM object with all fields populated
    openface_result: dict from openface_service.run_openface()
    asdmotion_result: dict from asdmotion_service.run_asdmotion()

    Returns complete risk assessment dict.
    """
    # ── 1. Gaze (Task A) ─────────────────────────────────────────────────────
    gaze_data   = session_db.gaze_task_a or []
    social_ratio = compute_gaze_ratio(gaze_data)
    gaze_risk    = score_gaze(social_ratio)

    # ── 2. Name Response (Task B) ────────────────────────────────────────────
    trials        = session_db.name_trials or []
    name_rate     = compute_name_response_rate(trials)
    name_risk     = score_name_response(name_rate)

    # ── 3. Expression (OpenFace AUs) ─────────────────────────────────────────
    expr_rate  = openface_result.get("expression_rate", 0.0)
    expr_risk  = score_expression(expr_rate)

    # ── 4. Repetitive Movement (ASDMotion) ───────────────────────────────────
    repetitive = asdmotion_result.get("repetitive_score", 0.0)

    # ── 5. Questionnaire ─────────────────────────────────────────────────────
    q_type  = session_db.questionnaire_type or "unknown"
    q_score = session_db.questionnaire_score or 0
    q_risk  = session_db.questionnaire_risk  or "unknown"

    if q_type == "mchat_r":
        q_norm = score_questionnaire_mchat(q_score)
    elif q_type == "indt_asd":
        q_norm = score_questionnaire_indt(q_score)
    else:
        q_norm = 0.5   # unknown type — conservative neutral

    # ── 6. Combined ──────────────────────────────────────────────────────────
    result = combined_risk(
        q_norm=q_norm,
        gaze_risk=gaze_risk,
        name_risk=name_risk,
        expr_risk=expr_risk,
    )

    result.update({
        "social_gaze_ratio":   round(social_ratio, 4),
        "name_response_rate":  round(name_rate, 4),
        "expression_rate":     round(expr_rate, 4),
        "repetitive_score":    round(repetitive, 4),
        "blink_rate_bpm":      _compute_blink_rate(gaze_data),
        "questionnaire_norm":  round(q_norm, 4),
        "questionnaire_type":  q_type,
        "questionnaire_score": q_score,
    })

    logger.info(
        f"Session {session_db.id} scored: "
        f"combined={result['combined_score']:.3f} "
        f"level={result['risk_level']} "
        f"flagged={result['flagged']}"
    )
    return result


def _compute_blink_rate(gaze_data: list) -> float:
    """
    Blink rate in blinks-per-minute.
    EAR threshold 0.20 (Soukupová & Čech 2016)
    """
    if len(gaze_data) < 2:
        return 0.0

    from ml.scoring_thresholds import BLINK_EAR_THRESHOLD
    blinks = 0
    was_closed = False
    for p in gaze_data:
        closed = p.get("blink_ear", 1.0) < BLINK_EAR_THRESHOLD
        if closed and not was_closed:
            blinks += 1
        was_closed = closed

    t0 = gaze_data[0].get("timestamp_ms", 0)
    t1 = gaze_data[-1].get("timestamp_ms", 0)
    minutes = (t1 - t0) / 60000.0
    return round(blinks / minutes, 2) if minutes > 0 else 0.0
