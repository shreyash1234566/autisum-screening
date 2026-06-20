"""
ml_router.py — Exposes the trained UCI ASD Random Forest model via REST.

Endpoint: POST /ml/aq10-predict
Input:    AQ-10 questionnaire scores (A1..A10, binary 0/1) + optional demographics.
Output:   ML prediction as an auxiliary signal.

IMPORTANT: This endpoint is a SUPPLEMENTARY tool for research and audit.
It uses the Thabtah et al. 2018 UCI dataset (AQ-10 format), which is
different from the M-CHAT-R and INDT-ASD instruments used by the mobile app.
Clinical decisions must be based on the full combined_risk score, not this alone.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional

from ml.inference import get_predictor

router = APIRouter(prefix="/ml", tags=["ml"])


class AQ10Input(BaseModel):
    # AQ-10 items — binary (0 = typical, 1 = atypical)
    A1_Score:  int = Field(..., ge=0, le=1, description="Social communication")
    A2_Score:  int = Field(..., ge=0, le=1)
    A3_Score:  int = Field(..., ge=0, le=1)
    A4_Score:  int = Field(..., ge=0, le=1)
    A5_Score:  int = Field(..., ge=0, le=1)
    A6_Score:  int = Field(..., ge=0, le=1)
    A7_Score:  int = Field(..., ge=0, le=1)
    A8_Score:  int = Field(..., ge=0, le=1)
    A9_Score:  int = Field(..., ge=0, le=1)
    A10_Score: int = Field(..., ge=0, le=1)

    # Optional demographic fields (same columns used during training)
    age:              Optional[float] = Field(None, ge=0, le=120)
    gender:           Optional[str]   = Field(None, description="'m' or 'f'")
    ethnicity:        Optional[str]   = None
    jundice:          Optional[str]   = Field(None, description="'yes' or 'no'")
    austim:           Optional[str]   = Field(None, description="'yes' or 'no'")
    contry_of_res:    Optional[str]   = None
    used_app_before:  Optional[str]   = Field(None, description="'yes' or 'no'")
    relation:         Optional[str]   = None
    result:           Optional[float] = Field(None, description="Raw AQ sum score (0–10)")

    @validator("gender")
    def normalise_gender(cls, v):
        if v is not None:
            v = v.lower().strip()
            if v not in ("m", "f", "male", "female"):
                raise ValueError("gender must be 'm'/'male' or 'f'/'female'")
        return v


class PredictionResponse(BaseModel):
    prediction:        int           # 0 = No ASD, 1 = ASD
    probability_asd:   float         # 0.0 – 1.0
    confidence:        str           # "low" | "medium" | "high"
    aq10_sum:          int           # convenience: sum of A1..A10
    features_used:     list[str]
    missing_features:  list[str]
    disclaimer:        str


@router.post(
    "/aq10-predict",
    response_model=PredictionResponse,
    summary="Auxiliary ML prediction from AQ-10 scores",
    description=(
        "Runs the UCI-dataset-trained Random Forest on AQ-10 questionnaire items. "
        "Returns a supplementary prediction only — not a standalone clinical diagnosis. "
        "Requires prior execution of `python ml/train_model.py`."
    ),
)
def predict_aq10(body: AQ10Input) -> PredictionResponse:
    predictor = get_predictor()
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "ML model not trained yet. "
                "Run 'python ml/train_model.py' to train it first."
            ),
        )

    features = body.dict(exclude_none=False)
    result   = predictor.predict(features)

    aq10_sum = sum(
        getattr(body, f"A{i}_Score") for i in range(1, 11)
    )

    return PredictionResponse(
        prediction=result["prediction"],
        probability_asd=result["probability_asd"],
        confidence=result["confidence"],
        aq10_sum=aq10_sum,
        features_used=result["features_used"],
        missing_features=result["missing_features"],
        disclaimer=(
            "Auxiliary research tool only. Trained on UCI ASD dataset (AQ-10 format). "
            "Not a substitute for clinician evaluation or the combined_risk score."
        ),
    )


@router.get(
    "/model-status",
    summary="Check whether the ML model has been trained and loaded",
)
def model_status():
    predictor = get_predictor()
    if predictor is None:
        return {
            "loaded": False,
            "message": "Model not found. Run 'python ml/train_model.py'.",
        }
    return {
        "loaded":       True,
        "n_features":   predictor._model.n_features_in_,
        "n_estimators": predictor._model.n_estimators,
        "feature_cols": predictor._feat_cols,
        "message":      "Model ready.",
    }
