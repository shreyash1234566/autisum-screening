"""
inference.py — loads the trained Random Forest model and runs predictions.

The model is trained on the UCI ASD Screening dataset (Thabtah et al. 2018)
using AQ-10 questionnaire items (A1_Score … A10_Score) plus optional
demographic fields (age, gender, ethnicity, etc.).

This module is NOT the primary clinical decision tool — that is the
combined_risk score in scoring_service.py. The ML prediction here is an
AUXILIARY signal produced independently from behavioral + questionnaire data.

Usage:
    from ml.inference import get_predictor
    predictor = get_predictor()          # returns None if model not yet trained
    if predictor:
        result = predictor.predict({
            "A1_Score": 1, "A2_Score": 0, ..., "A10_Score": 1,
            "age": 3.5, "gender": "m",
        })
        # → {"prediction": 1, "probability_asd": 0.87, "confidence": "high"}
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_PATH    = Path(__file__).parent / "questionnaire_model.pkl"
ENCODERS_PATH = Path(__file__).parent / "encoders.pkl"

# AQ-10 feature columns expected by the trained model
AQ10_SCORE_COLS = [f"A{i}_Score" for i in range(1, 11)]
OPTIONAL_DEMO_COLS = ["age", "gender", "ethnicity", "jundice", "austim",
                       "contry_of_res", "used_app_before", "relation", "result"]


class ASDPredictor:
    """
    Wraps the trained sklearn RandomForestClassifier.
    Instantiated once and cached in module-level _predictor.
    """

    def __init__(self, model, encoders: dict, feature_cols: list[str]):
        self._model    = model
        self._encoders = encoders
        self._feat_cols = feature_cols

    def predict(self, features: dict) -> dict:
        """
        Run inference on a single sample.

        features: dict with AQ-10 scores (A1_Score..A10_Score) and optionally
                  demographic fields (age, gender, ethnicity, …).

        Returns:
            {
                "prediction":      0 or 1        (0 = No ASD, 1 = ASD),
                "probability_asd": float 0–1,
                "confidence":      "low" | "medium" | "high",
                "features_used":   list[str],
                "missing_features": list[str],
            }
        """
        import numpy as np

        # Build feature vector in training order
        row = []
        used = []
        missing = []
        for col in self._feat_cols:
            if col in features:
                val = features[col]
                # Apply same LabelEncoder used during training for categorical cols
                if col in self._encoders:
                    le = self._encoders[col]
                    val_str = str(val).lower()
                    if val_str in le.classes_:
                        val = le.transform([val_str])[0]
                    else:
                        # Unseen category — use 0 (most common label)
                        val = 0
                        logger.warning(
                            f"ML inference: unknown category '{val_str}' for "
                            f"feature '{col}' — defaulting to 0"
                        )
                row.append(float(val))
                used.append(col)
            else:
                # Fill missing with median-ish neutral value
                # AQ-10 scores are binary (0/1) → 0 is safe neutral
                # Demographic → 0 (encoded unknown)
                row.append(0.0)
                missing.append(col)

        X = np.array([row])
        proba = self._model.predict_proba(X)[0]
        # Class order from RandomForest: [0, 1]
        classes = list(self._model.classes_)
        asd_idx = classes.index(1) if 1 in classes else -1
        prob_asd = float(proba[asd_idx]) if asd_idx >= 0 else 0.5

        prediction = int(self._model.predict(X)[0])

        # Confidence bucket
        if prob_asd >= 0.80 or prob_asd <= 0.20:
            confidence = "high"
        elif prob_asd >= 0.65 or prob_asd <= 0.35:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "prediction":       prediction,
            "probability_asd":  round(prob_asd, 4),
            "confidence":       confidence,
            "features_used":    used,
            "missing_features": missing,
        }


# ── Module-level cache ────────────────────────────────────────────────────────

_predictor: Optional[ASDPredictor] = None
_load_attempted = False


def get_predictor() -> Optional[ASDPredictor]:
    """
    Return a cached ASDPredictor, or None if the model file doesn't exist yet
    (i.e., train_model.py hasn't been run).

    Failure is intentionally soft: the rest of the system works without it.
    """
    global _predictor, _load_attempted
    if _load_attempted:
        return _predictor

    _load_attempted = True

    if not MODEL_PATH.exists():
        logger.warning(
            "ML model not found at %s — run 'python ml/train_model.py' to train it. "
            "The /ml/aq10-predict endpoint will return 503 until then.",
            MODEL_PATH,
        )
        return None

    try:
        import joblib

        model    = joblib.load(MODEL_PATH)
        encoders = joblib.load(ENCODERS_PATH) if ENCODERS_PATH.exists() else {}

        # Reconstruct feature_cols from the model's n_features_in_ and training order.
        # train_model.py uses AQ score cols first, then demo cols.
        n = model.n_features_in_
        all_possible = AQ10_SCORE_COLS + OPTIONAL_DEMO_COLS
        feature_cols = all_possible[:n]   # match training-time truncation

        _predictor = ASDPredictor(model, encoders, feature_cols)
        logger.info("ML model loaded from %s (%d features)", MODEL_PATH, n)
    except Exception as exc:
        logger.error("Failed to load ML model: %s", exc)

    return _predictor
