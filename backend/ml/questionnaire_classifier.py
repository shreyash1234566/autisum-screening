"""
questionnaire_classifier.py
Random Forest on UCI ASD Screening datasets (Thabtah et al. 2018)
Published accuracy: >95% on binary ASD/no-ASD classification
kaggle.com/fabdelja/autism-screening-for-toddlers
archive.ics.uci.edu/dataset/419
"""
import joblib
import numpy as np
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "questionnaire_model.pkl"
ENCODERS_PATH = Path(__file__).parent / "encoders.pkl"

# AQ-10 feature columns matching UCI dataset schema
# Source: Baron-Cohen et al. (2010) — AQ-10 instrument
AQ10_FEATURES = [
    "A1_Score","A2_Score","A3_Score","A4_Score","A5_Score",
    "A6_Score","A7_Score","A8_Score","A9_Score","A10_Score",
    "age", "gender", "ethnicity", "jundice",
    "austim",        # family member with ASD
    "contry_of_res", "used_app_before",
    "result",        # raw AQ-10 total
]

def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            "Run: python ml/train_model.py first."
        )
    return joblib.load(MODEL_PATH), joblib.load(ENCODERS_PATH)

def predict_asd_risk(features: dict) -> dict:
    """
    features: dict with AQ-10 answers (A1_Score..A10_Score = 0/1)
    Returns probability and binary classification.
    """
    clf, encoders = load_model()

    row = []
    for col in AQ10_FEATURES:
        val = features.get(col, 0)
        if col in encoders:
            val = encoders[col].transform([str(val)])[0]
        row.append(float(val))

    X = np.array([row])
    prob = clf.predict_proba(X)[0]
    pred = clf.predict(X)[0]

    return {
        "prediction": "ASD" if pred == 1 else "No ASD",
        "probability_asd": round(float(prob[1]), 4),
        "probability_no_asd": round(float(prob[0]), 4),
        "normalised_risk": round(float(prob[1]), 4),
    }
