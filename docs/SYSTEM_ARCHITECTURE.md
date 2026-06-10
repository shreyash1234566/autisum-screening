# System Architecture & Processing Pipeline

This document explains the data pipelines and processing algorithms implemented in AutiScreen.

---

## 1. High-Level Architectural Flow

AutiScreen combines client-side interactive visual tasks (mobile capture) with server-side computer vision and statistical analysis (ML and scoring engine).

```mermaid
graph TD
    A[Mobile App - Flutter] -- 1. Upload logs & video --> B(FastAPI Server)
    B -- 2. Save metadata & file --> C[(PostgreSQL DB)]
    B -- 3. Dispatch worker task --> D[Background Queue]
    D -- 4a. Run OpenFace --> E[Action Unit smile analysis]
    D -- 4b. Run ASDMotion --> F[Stereotypical movement detection]
    E & F -- 5. Extract features --> G[Scoring Service]
    C -- Load answers & trials --> G
    G -- 6. Run ML Classifier & formulas --> H[Calculate combined score & flags]
    H -- 7. Update status & scores --> C
    I[Dashboard - React] -- 8. Fetch results --> B
```

---

## 2. Gaze + Smile Co-occurrence Detection Pipeline

The primary clinical marker for screening social reciprocity is the **co-occurrence of interactive gaze and social smiles**.

### Step-by-Step Sequence:

```mermaid
sequenceDiagram
    autonumber
    participant App as Mobile App (Flutter)
    participant API as FastAPI Router
    participant Worker as Background Task
    participant OF as OpenFace Service
    participant Score as Scoring Service
    participant DB as PostgreSQL

    App->>API: POST /sessions/upload (JSON logs + Video file)
    Note over App,API: Contains gaze coordinates, name response latency, M-CHAT score
    API->>DB: Save session in 'pending' status
    API->>Worker: Enqueue processing job
    API-->>App: Return 200 OK (Accepted)

    activate Worker
    Worker->>DB: Set status to 'processing'
    Worker->>OF: Invoke FeatureExtraction (video path)
    activate OF
    Note over OF: Extract frame-by-frame landmarks & Action Units (AUs)
    OF-->>Worker: Return AU CSV data (AU06, AU12)
    deactivate OF

    Worker->>Score: run_full_scoring(Session, AUs, Motion)
    activate Score
    Note over Score: 1. Calculate Social Gaze Ratio (stimuli-aligned)<br/>2. Name Response latency mapping<br/>3. Compute Smile Rate (AU06 > 1.0 AND AU12 > 1.5)<br/>4. Weight: 40% Q + 30% Gaze + 20% Name + 10% Smile
    Score-->>Worker: Combined Risk Score & Review Flags
    deactivate Score

    Worker->>DB: Update Session (status='done', score, level, flagged)
    deactivate Worker
```

### Analysis Algorithms:
1. **Social Gaze Ratio:** Calculates the percentage of frames where the child's coordinate offset from the target stimulus was below the clinical threshold ($d \le 0.45$).
2. **Name Response Rate:** Checks latency in trials where the child's name was called. If response latency exceeds thresholds or child did not respond, it increments risk.
3. **Genuine Social Smile Detection:** Standard OpenFace FACS (Facial Action Coding System) criteria:
   $$\text{Genuine Smile} = (\text{AU06\_r} \ge 1.0) \land (\text{AU12\_r} \ge 1.5)$$
   The co-occurrence rate measures what proportion of gaze task attention matches the presence of a genuine smile.
4. **ASDMotion:** Uses Pose/Movement estimation tracking to check frequency of repetitive limb or torso patterns, outputting a movement score.
