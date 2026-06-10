"""
openface_service.py
Wraps OpenFace 3.0 (CMU MultiComp Lab)
github.com/CMU-MultiComp-Lab/OpenFace-3.0
Install: pip install openface-test && openface download

Processes recorded session video server-side to extract:
  - Action Unit intensities (AU6, AU12 for smile detection)
  - Head pose (yaw, pitch, roll)
  - Gaze vectors (cross-validation with MediaPipe)

AU thresholds from FACS + OpenFace docs:
  AU6  > 1.0  → Cheek raise (Duchenne smile)
  AU12 > 1.5  → Lip corner pull (smile shape)
  Combined → genuine social smile
"""
import subprocess, csv, tempfile, os, logging
from pathlib import Path
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

def run_openface(video_path: Optional[str]) -> dict:
    """
    Run OpenFace FeatureExtraction on video.
    Returns dict of per-frame AU data and aggregate stats.
    """
    if not video_path or not os.path.exists(video_path):
        logger.warning(f"Video not found or empty path: {video_path}. Using mock OpenFace result.")
        return _mock_openface_result()

    with tempfile.TemporaryDirectory() as tmpdir:
        out_csv = os.path.join(tmpdir, "features.csv")

        cmd = [
            settings.OPENFACE_BIN,
            "-f", video_path,
            "-out_dir", tmpdir,
            "-aus",           # action units
            "-pose",          # head pose
            "-gaze",          # gaze vectors
            "-2Dfp",          # 2D facial landmarks
            "-quiet",
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                logger.error(f"OpenFace error: {result.stderr}")
                return _mock_openface_result()
        except subprocess.TimeoutExpired:
            logger.error("OpenFace timed out (>5 min)")
            return _mock_openface_result()
        except FileNotFoundError:
            logger.warning(
                "OpenFace binary not found. "
                "Install: pip install openface-test && openface download"
            )
            return _mock_openface_result()

        # Find output CSV
        csv_files = list(Path(tmpdir).glob("*.csv"))
        if not csv_files:
            logger.error("OpenFace produced no CSV output")
            return _mock_openface_result()

        return _parse_openface_csv(str(csv_files[0]))


def _parse_openface_csv(csv_path: str) -> dict:
    """
    Parse OpenFace output CSV.
    Key columns: AU06_r, AU12_r (intensity), pose_Rx/Ry/Rz, gaze_angle_x/y
    """
    frames = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only process frames with high confidence
            confidence = float(row.get("confidence", 0))
            if confidence < 0.8:
                continue

            au6  = float(row.get("AU06_r", 0))
            au12 = float(row.get("AU12_r", 0))

            frames.append({
                "frame":       int(row.get("frame", 0)),
                "timestamp_s": float(row.get("timestamp", 0)),
                "confidence":  confidence,
                "au6":         au6,
                "au12":        au12,
                # AU6 > 1.0 AND AU12 > 1.5 = genuine smile (FACS criteria)
                "smile":       (au6 > 1.0 and au12 > 1.5),
                "head_yaw":    float(row.get("pose_Ry", 0)),
                "head_pitch":  float(row.get("pose_Rx", 0)),
                "gaze_x":      float(row.get("gaze_angle_x", 0)),
                "gaze_y":      float(row.get("gaze_angle_y", 0)),
            })

    if not frames:
        return {
            "error": "no_confident_frames",
            "frames": [],
            "expression_rate": 0.0,
            "mean_au6": 0.0,
            "mean_au12": 0.0,
            "total_frames": 0,
            "smile_frames": 0,
        }

    smile_frames = [f for f in frames if f["smile"]]
    expression_rate = len(smile_frames) / len(frames)
    mean_au6  = sum(f["au6"]  for f in frames) / len(frames)
    mean_au12 = sum(f["au12"] for f in frames) / len(frames)

    return {
        "total_frames":    len(frames),
        "smile_frames":    len(smile_frames),
        "expression_rate": round(expression_rate, 4),
        "mean_au6":        round(mean_au6, 4),
        "mean_au12":       round(mean_au12, 4),
        "frames":          frames,
    }


def _mock_openface_result() -> dict:
    """Fallback when OpenFace binary unavailable (dev/test mode)."""
    logger.warning("Using mock OpenFace result — install OpenFace for real analysis")
    return {
        "total_frames": 0,
        "smile_frames": 0,
        "expression_rate": 0.0,
        "mean_au6": 0.0,
        "mean_au12": 0.0,
        "frames": [],
        "mock": True,
    }
