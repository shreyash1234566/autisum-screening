"""
train_model.py
Downloads UCI ASD datasets and trains Random Forest.
Run once: python ml/train_model.py

Datasets (Thabtah et al. 2018, CC BY 4.0):
  - Toddler:  kaggle.com/fabdelja/autism-screening-for-toddlers
  - Children: archive.ics.uci.edu/dataset/419
  - Adult:    archive.ics.uci.edu/dataset/426

Expected accuracy: >95% (as per published papers)
"""
import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score

DATA_DIR  = Path(__file__).parent.parent.parent / "ml" / "data"
MODEL_DIR = Path(__file__).parent
MODEL_PATH    = MODEL_DIR / "questionnaire_model.pkl"
ENCODERS_PATH = MODEL_DIR / "encoders.pkl"

# Categorical columns needing encoding
CAT_COLS = ["gender", "ethnicity", "jundice", "austim",
            "contry_of_res", "used_app_before", "relation"]

TARGET_COL = "Class/ASD"

def load_data():
    frames = []
    for fname in DATA_DIR.glob("*.csv"):
        df = pd.read_csv(fname)
        df.columns = [c.strip() for c in df.columns]
        frames.append(df)
    if not frames:
        raise FileNotFoundError(
            f"No CSV files in {DATA_DIR}\n"
            "Download from:\n"
            "  Toddler: kaggle datasets download -d fabdelja/autism-screening-for-toddlers\n"
            "  Children: wget https://archive.ics.uci.edu/ml/machine-learning-databases/00419/Autism-Child-Data.arff\n"
            "  Then convert arff to csv and place in ml/data/"
        )
    return pd.concat(frames, ignore_index=True)

def preprocess(df: pd.DataFrame):
    # Drop rows missing target
    df = df.dropna(subset=[TARGET_COL])

    # Encode target: 'YES'/'1' → 1, 'NO'/'0' → 0
    df[TARGET_COL] = df[TARGET_COL].astype(str).str.upper().map(
        lambda x: 1 if x in ("YES", "1", "ASD") else 0)

    # Identify AQ-10 score columns (A1..A10)
    score_cols = [c for c in df.columns if c.startswith("A") and "_Score" in c]

    # Fill missing scores with median
    for col in score_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col].fillna(df[col].median(), inplace=True)

    encoders = {}
    for col in CAT_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("unknown")
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            encoders[col] = le

    feature_cols = score_cols
    for col in CAT_COLS + ["age", "result"]:
        if col in df.columns:
            feature_cols.append(col)

    feature_cols = [c for c in feature_cols if c in df.columns]
    X = df[feature_cols].values
    y = df[TARGET_COL].values
    return X, y, encoders, feature_cols

def train():
    print("Loading data...")
    df = load_data()
    print(f"Total samples: {len(df)}")

    X, y, encoders, feature_cols = preprocess(df)
    print(f"Features: {feature_cols}")
    print(f"Class balance: ASD={y.sum()}, No-ASD={len(y)-y.sum()}")

    # Random Forest — best performer per Thabtah et al. 2018
    # n_estimators=100, default hyperparameters achieve >95% accuracy
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",
    )

    # 5-fold cross-validation (matching paper methodology)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X, y, cv=cv, scoring="accuracy")
    print(f"\n5-Fold CV Accuracy: {scores.mean():.4f} ± {scores.std():.4f}")
    print(f"Individual folds:   {[f'{s:.3f}' for s in scores]}")

    # Train final model on full data
    clf.fit(X, y)
    y_pred = clf.predict(X)
    print(f"\nFull-data Accuracy: {accuracy_score(y, y_pred):.4f}")
    print(classification_report(y, y_pred, target_names=["No ASD", "ASD"]))

    # Feature importance
    importances = sorted(zip(feature_cols, clf.feature_importances_),
                         key=lambda x: -x[1])
    print("\nTop 5 features:")
    for feat, imp in importances[:5]:
        print(f"  {feat}: {imp:.4f}")

    # Save
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(encoders, ENCODERS_PATH)
    print(f"\nModel saved → {MODEL_PATH}")
    print(f"Encoders saved → {ENCODERS_PATH}")

if __name__ == "__main__":
    train()
