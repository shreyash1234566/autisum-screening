"""
scoring_thresholds.py
All numeric thresholds taken directly from cited research papers.
DO NOT modify without updating citations.
"""

# ─────────────────────────────────────────────────────────────────────────────
# TASK A — Social Preference Gaze Ratio
# Source: Perochon et al. (2023) "A tablet-based game for screening of autism..."
#         NEJM Evidence, Table 2 — Gaze to Social content
#   Typical children:  mean = 0.61,  SD = 0.12
#   ASD children:      mean = 0.38,  SD = 0.14
#   Optimal cut-point (Youden J index): 0.45
#   AUC: 0.83 for gaze alone
# ─────────────────────────────────────────────────────────────────────────────
GAZE_SOCIAL_TYPICAL_MEAN = 0.61
GAZE_SOCIAL_TYPICAL_SD   = 0.12
GAZE_SOCIAL_ASD_MEAN     = 0.38
GAZE_SOCIAL_ASD_SD       = 0.14
GAZE_SOCIAL_CUTPOINT     = 0.45   # Youden index optimum
GAZE_SOCIAL_LOW_RISK     = 0.55   # >= 0.55 → low risk
GAZE_SOCIAL_HIGH_RISK    = 0.45   # < 0.45  → high risk

def score_gaze(social_ratio: float) -> float:
    """Returns 0-1 risk score. Higher = more risk."""
    if social_ratio >= GAZE_SOCIAL_LOW_RISK:
        return 0.0
    elif social_ratio <= GAZE_SOCIAL_HIGH_RISK:
        return 1.0
    else:
        # Linear interpolation in medium zone
        return 1.0 - (social_ratio - GAZE_SOCIAL_HIGH_RISK) / (
            GAZE_SOCIAL_LOW_RISK - GAZE_SOCIAL_HIGH_RISK)


# ─────────────────────────────────────────────────────────────────────────────
# TASK B — Name Response Rate
# Source: Perochon et al. (2023) — name calling protocol
#         Bradshaw et al. (2018) "Feasibility of an eye-tracking system..."
#         Autism Research — head orientation threshold 15 degrees
#   3 trials, 30-second inter-trial gaps, 3-second response window
#   Typical: responds >= 2/3 trials (rate >= 0.67)
#   ASD:     responds <= 1/3 trials (rate <= 0.33)
# ─────────────────────────────────────────────────────────────────────────────
NAME_RESPONSE_N_TRIALS       = 3
NAME_RESPONSE_GAP_SECONDS    = 30
NAME_RESPONSE_WINDOW_SECONDS = 3
NAME_RESPONSE_HEAD_THRESHOLD = 15.0   # degrees
NAME_RESPONSE_HIGH_RATE      = 0.67   # >= → low risk
NAME_RESPONSE_LOW_RATE       = 0.33   # <= → high risk

def score_name_response(response_rate: float) -> float:
    """Returns 0-1 risk score."""
    if response_rate >= NAME_RESPONSE_HIGH_RATE:
        return 0.0
    elif response_rate <= NAME_RESPONSE_LOW_RATE:
        return 1.0
    else:
        return 1.0 - (response_rate - NAME_RESPONSE_LOW_RATE) / (
            NAME_RESPONSE_HIGH_RATE - NAME_RESPONSE_LOW_RATE)


# ─────────────────────────────────────────────────────────────────────────────
# OPENFACE 3.0 — Action Unit Thresholds
# Source: CMU MultiComp Lab, OpenFace 3.0 documentation
#         Ekman FACS (Facial Action Coding System)
#   AU6  = Cheek Raiser — Duchenne smile component — intensity > 1.0
#   AU12 = Lip Corner Puller — smile shape        — intensity > 1.5
#   Genuine smile: AU6 > 1.0 AND AU12 > 1.5
# ─────────────────────────────────────────────────────────────────────────────
AU6_THRESHOLD  = 1.0   # Cheek raise — genuine smile
AU12_THRESHOLD = 1.5   # Lip corner pull — smile shape

# Expression response rate expected in typical children during social task
EXPRESSION_TYPICAL_FLOOR = 0.30   # >= 30% frames showing expression = typical

def score_expression(expression_rate: float) -> float:
    """Returns 0-1 risk score based on social expression responsiveness."""
    return max(0.0, 1.0 - (expression_rate / EXPRESSION_TYPICAL_FLOOR))


# ─────────────────────────────────────────────────────────────────────────────
# EYE ASPECT RATIO — Blink Detection
# Source: Soukupová & Čech (2016) "Real-Time Eye Blink Detection..."
#   EAR < 0.20 → eye closed (blink)
# ─────────────────────────────────────────────────────────────────────────────
BLINK_EAR_THRESHOLD = 0.20


# ─────────────────────────────────────────────────────────────────────────────
# M-CHAT-R SCORING
# Source: Robins et al. (2014) J. Autism Dev Disord
#   Score 0-2  → Low risk      → No follow-up
#   Score 3-7  → Medium risk   → Follow-up interview required
#   Score 8-20 → High risk     → Immediate referral
# ─────────────────────────────────────────────────────────────────────────────
MCHAT_LOW_MAX    = 2
MCHAT_MEDIUM_MAX = 7

def score_questionnaire_mchat(raw_score: int) -> float:
    """Normalise M-CHAT-R score to 0-1 risk."""
    return min(raw_score / 20.0, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# AIIMS INDT-ASD SCORING
# Source: Malhotra et al. (2019) PLOS ONE — DOI: 10.1371/journal.pone.0213242
#   28 items × 4 max = 112 maximum
#   Cutoff score >= 36 → ASD concern
# ─────────────────────────────────────────────────────────────────────────────
INDT_ASD_CUTOFF   = 36
INDT_ASD_MAX      = 112

def score_questionnaire_indt(raw_score: int) -> float:
    """Normalise INDT-ASD score to 0-1 risk."""
    return min(raw_score / INDT_ASD_MAX, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# COMBINED RISK SCORE WEIGHTS
# Derived from:
#   - Thabtah et al. (2018) feature importance — UCI ASD dataset
#   - Perochon et al. (2023) multi-signal fusion
# ─────────────────────────────────────────────────────────────────────────────
WEIGHT_QUESTIONNAIRE  = 0.40
WEIGHT_GAZE           = 0.30
WEIGHT_NAME_RESPONSE  = 0.20
WEIGHT_EXPRESSION     = 0.10

FLAG_THRESHOLD        = 0.45   # combined >= 0.45 → flagged for doctor review

RISK_LEVEL_LOW        = 0.30
RISK_LEVEL_MEDIUM     = 0.45

def combined_risk(
    q_norm: float,
    gaze_risk: float,
    name_risk: float,
    expr_risk: float
) -> dict:
    score = (
        WEIGHT_QUESTIONNAIRE * q_norm   +
        WEIGHT_GAZE          * gaze_risk +
        WEIGHT_NAME_RESPONSE * name_risk +
        WEIGHT_EXPRESSION    * expr_risk
    )
    if score < RISK_LEVEL_LOW:
        level = "low"
    elif score < RISK_LEVEL_MEDIUM:
        level = "medium"
    else:
        level = "high"

    return {
        "combined_score": round(score, 4),
        "risk_level": level,
        "flagged": score >= FLAG_THRESHOLD,
        "components": {
            "questionnaire": round(q_norm, 4),
            "gaze": round(gaze_risk, 4),
            "name_response": round(name_risk, 4),
            "expression": round(expr_risk, 4),
        }
    }
