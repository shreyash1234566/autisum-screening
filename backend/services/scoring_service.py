"""
scoring_service.py
Combines all behavioral + questionnaire signals into a final risk score.
All weights and thresholds from cited research papers in scoring_thresholds.py

FIX: run_full_scoring() previously took ONE openface_result + ONE
asdmotion_result, from a single session-wide video. The app now records
Tasks A/B/C as three separate clips, so this now takes a dict of results
per task ({"task_a": {...}, "task_b": {...}, "task_c": {...}}) and combines
them via frame/segment-weighted averaging rather than picking just one.
"""
import logging
from ml.scoring_thresholds import (
    score_gaze, score_name_response, score_expression,
    score_questionnaire_mchat, score_questionnaire_indt,
    combined_risk,
)

logger = logging.getLogger(__name__)

TASK_NAMES = ("task_a", "task_b", "task_c")


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


def _combine_expression_rate(openface_results: dict) -> float:
    """
    Frame-count-weighted average of expression_rate across whichever task
    clips produced real (non-mock) OpenFace results. Clips with more
    detected frames get proportionally more say, rather than a flat mean
    across tasks of very different length/quality.
    """
    total_frames = 0
    weighted_sum = 0.0
    for task in TASK_NAMES:
        result = openface_results.get(task, {}) or {}
        if result.get("mock") is True:
            continue
        frames = result.get("total_frames", 0)
        rate   = result.get("expression_rate", 0.0)
        if frames > 0:
            weighted_sum += rate * frames
            total_frames += frames

    return weighted_sum / total_frames if total_frames > 0 else 0.0


def _combine_repetitive_score(asdmotion_results: dict) -> float:
    """
    Segment-count-weighted average of repetitive_score across whichever
    task clips produced real (non-mock) MediaPipe-Pose results.

    NOTE (research-backed): this score is informational only -- it is
    deliberately NOT included in combined_risk()'s weights. Tasks A/B/C are
    framed tight on the face for gaze accuracy, which is the wrong camera
    distance for reliable hand-flapping/stereotypy detection (full-body
    framing is required -- see Stenum et al. 2026, Developmental Science,
    which reports only 70.2% accuracy / 31.8% F1 for OpenPose+LSTM
    stereotypy classification even WITH proper full-body toddler footage).
    Treat this value as a logged signal for future research, not a
    clinical input.
    """
    total_segments = 0
    weighted_sum = 0.0
    for task in TASK_NAMES:
        result = asdmotion_results.get(task, {}) or {}
        if result.get("mock") is True:
            continue
        segments = result.get("total_segments", 0)
        score    = result.get("repetitive_score", 0.0)
        if segments > 0:
            weighted_sum += score * segments
            total_segments += segments

    return weighted_sum / total_segments if total_segments > 0 else 0.0


def run_full_scoring(session_db, openface_results: dict, asdmotion_results: dict) -> dict:
    """
    Master scoring function. Called after video analysis completes.

    session_db: SQLAlchemy Session ORM object with all fields populated
    openface_results: {"task_a": {...}, "task_b": {...}, "task_c": {...}}
        each value is a dict from openface_service.run_openface()
    asdmotion_results: same shape, from asdmotion_service.run_asdmotion()

    Returns complete risk assessment dict.
    """
    # ── 1. Gaze (Task A, on-device data — independent of server-side video) ──
    gaze_data    = session_db.gaze_task_a or []
    social_ratio = compute_gaze_ratio(gaze_data)
    gaze_risk    = score_gaze(social_ratio)

    # ── 2. Name Response (Task B, on-device data) ────────────────────────────
    trials    = session_db.name_trials or []
    name_rate = compute_name_response_rate(trials)
    name_risk = score_name_response(name_rate)

    # ── 3. Expression (OpenFace AUs, combined across A/B/C clips) ────────────
    expr_rate = _combine_expression_rate(openface_results)
    expr_risk = score_expression(expr_rate)

    # ── 4. Repetitive Movement (MediaPipe Pose, combined — informational) ───
    repetitive = _combine_repetitive_score(asdmotion_results)

    # ── 5. Questionnaire ──────────────────────────────────────────────────────
    q_type  = session_db.questionnaire_type or "unknown"
    q_score = session_db.questionnaire_score or 0

    if q_type == "mchat_r":
        q_norm = score_questionnaire_mchat(q_score)
    elif q_type == "indt_asd":
        q_norm = score_questionnaire_indt(q_score)
    else:
        q_norm = 0.5

    # ── 6. Combined (weights exclude repetitive_score — see _combine_repetitive_score) ──
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
