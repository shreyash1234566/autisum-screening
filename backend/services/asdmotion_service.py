"""
asdmotion_service.py
Wraps ASDMotion (Dinstein Lab, Israel)
github.com/Dinstein-Lab/ASDMotion

Detects stereotypical repetitive movements (hand-flapping, rocking, spinning)
which are common in ASD. Runs server-side on session video via OpenPose.
"""
import subprocess, json, os, logging
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

ASDMOTION_SCRIPT = os.path.join(settings.ASDMOTION_PATH, "detect_stereotypy.py")


def run_asdmotion(video_path: str) -> dict:
    """
    Run ASDMotion stereotypy detection on a video file.
    Returns per-segment repetitive movement scores.
    """
    if not os.path.exists(video_path):
        return {"error": "video_not_found"}

    if not os.path.exists(ASDMOTION_SCRIPT):
        logger.warning(
            "ASDMotion not found. "
            "Clone: git clone https://github.com/Dinstein-Lab/ASDMotion "
            f"to {settings.ASDMOTION_PATH}"
        )
        return _mock_asdmotion()

    try:
        result = subprocess.run(
            ["python", ASDMOTION_SCRIPT,
             "--video", video_path,
             "--output", "json"],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode != 0:
            logger.error(f"ASDMotion error: {result.stderr}")
            return {"error": result.stderr[:500]}

        data = json.loads(result.stdout)
        return _aggregate_asdmotion(data)

    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except json.JSONDecodeError as e:
        return {"error": f"json_parse: {e}"}


def _aggregate_asdmotion(raw: dict) -> dict:
    """
    Aggregate raw ASDMotion output into a single repetitive score.
    Score 0-1: higher = more stereotyped movement detected.
    """
    segments = raw.get("segments", [])
    if not segments:
        return {"repetitive_score": 0.0, "segments": []}

    scores = [s.get("stereotypy_score", 0.0) for s in segments]
    mean_score = sum(scores) / len(scores)

    return {
        "repetitive_score": round(mean_score, 4),
        "max_segment_score": round(max(scores), 4),
        "flagged_segments":  sum(1 for s in scores if s > 0.5),
        "total_segments":    len(segments),
        "segments":          segments,
    }


def _mock_asdmotion() -> dict:
    logger.warning("Using mock ASDMotion — clone repo for real detection")
    return {"repetitive_score": 0.0, "mock": True}
