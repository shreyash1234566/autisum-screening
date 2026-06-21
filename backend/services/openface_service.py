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
import csv
import logging
import os
import subprocess
import tempfile
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
        # OpenFace 3.0 (openface-test) CLI: openface detect-video <video> -o <out_dir> -d <device>
        # The '-f' flag is NOT supported in this version (fixed in a prior commit).
        #
        # CRITICAL: '--device/-d' defaults to 'cuda' at the click-option level
        # (see openface/cli.py). This container ships CPU-only torch
        # (torch==2.3.1+cpu, chosen deliberately to avoid Codespaces disk
        # exhaustion from CUDA wheels). Omitting '-d cpu' causes a hard crash:
        #   FaceDetector.__init__ -> model.to('cuda') raises
        #   "AssertionError: Torch not compiled with CUDA enabled"
        # and even on a CUDA-capable build, LandmarkDetector.__init__ raises
        #   "ValueError: When using 'cuda', provide at least one valid device ID"
        # because its default device_ids=[-1] is invalid. So 'cpu' is the only
        # device value that actually works against this package, regardless
        # of whether a GPU is present.
        cmd = [
            settings.OPENFACE_BIN,
            "detect-video",
            video_path,
            "-o", tmpdir,
            "-d", "cpu",
        ]

        try:
            logger.info(f"Executing OpenFace: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600,
                # CRITICAL: openface-test hardcodes every weight path as a
                # relative './weights/...' string (no override exists -- see
                # Dockerfile comment above the `openface download` step for
                # the full explanation). video_path and -o tmpdir above are
                # both absolute, so changing cwd here is safe for them; it's
                # only here to make the relative weight lookups resolve to
                # /opt/weights instead of whatever uvicorn's cwd happens to
                # be (/app, which the dev bind mount can wipe out).
                cwd="/opt",
            )
            if result.returncode != 0:
                logger.error(f"OpenFace failed with return code {result.returncode}")
                logger.error(f"Stderr: {result.stderr}")
                ret = _mock_openface_result()
                ret["error"] = f"openface_nonzero_exit: {result.stderr[:200]}"
                return ret
        except subprocess.TimeoutExpired:
            logger.error("OpenFace timed out (>10 min)")
            ret = _mock_openface_result()
            ret["error"] = "timeout"
            return ret
        except FileNotFoundError:
            # FIX: this used to `raise RuntimeError(...)`, which propagated
            # all the way out of run_openface and crashed the background
            # task instead of letting it degrade gracefully like every other
            # "video unusable" case. A missing binary/package is an
            # infrastructure problem, not a reason to lose the rest of the
            # session's scoring (gaze/name-response/questionnaire don't need
            # video at all -- see scoring_service.py).
            logger.error(
                "OpenFace binary not found. "
                "Install: pip install openface-test && openface download"
            )
            ret = _mock_openface_result()
            ret["error"] = "openface_binary_not_found"
            return ret

        # Find output file. OpenFace 3.0 generates .tsv files.
        # The filename is usually based on the input video name.
        tsv_files = list(Path(tmpdir).glob("*.tsv"))
        if not tsv_files:
            # Fallback check for CSV just in case
            csv_files = list(Path(tmpdir).glob("*.csv"))
            if not csv_files:
                logger.error(f"No output files found in {tmpdir}. Files: {os.listdir(tmpdir)}")
                ret = _mock_openface_result()
                ret["error"] = "no_output_file"
                return ret
            return _parse_openface_output(str(csv_files[0]), delimiter=',')
        
        return _parse_openface_output(str(tsv_files[0]), delimiter='\t')


def _parse_openface_output(file_path: str, delimiter: str = '\t') -> dict:
    """
    Parse OpenFace output file (TSV or CSV).
    OpenFace 3.0 TSV Columns:
    timestamp, image_path, face_id, face_detection, landmarks, emotion, gaze_yaw, gaze_pitch, action_units
    
    action_units is a string like: "[0.1, 0.2, ...]"
    We need to map these to specific AUs if possible, or use the indices.
    According to OpenFace 3.0 docs/code, AU intensities are in action_units.
    """
    frames = []
    try:
        with open(file_path, newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for i, row in enumerate(reader):
                # OpenFace 3.0 might not have 'confidence' per frame in the same way
                # but 'face_detection' contains [x1, y1, x2, y2, score]
                try:
                    det_str = row.get("face_detection", "")
                    det = eval(det_str) if det_str.startswith('[') else None
                    # FIX: was `else 1.0` -- meaning a row with NO face
                    # detected at all (face_detection is empty/None, written
                    # by process_video()'s else-branch when len(dets) == 0)
                    # got treated as FULLY CONFIDENT and passed straight
                    # through the filter below. That's backwards: no
                    # detection should mean zero confidence, not perfect
                    # confidence. It also meant we'd go on to try parsing
                    # gaze_yaw/gaze_pitch for that row -- but those are
                    # written as Python None (-> empty string in the CSV)
                    # in that exact same no-face branch, so float(row['gaze_yaw'])
                    # would crash immediately after. Defaulting to 0.0 here
                    # means the `< 0.8` check below correctly `continue`s
                    # past these rows before we ever reach that parsing.
                    confidence = det[4] if det and len(det) > 4 else 0.0
                except Exception:
                    confidence = 0.0

                if confidence < 0.8: # Reject low-confidence AND no-detection frames
                    continue

                # Parse action units
                # OpenFace 3.0 AU mapping (typical):
                # 0:AU1, 1:AU2, 2:AU4, 3:AU6, 4:AU7, 5:AU10, 6:AU12, 7:AU14, 8:AU15, 9:AU17, 10:AU20, 11:AU23, 12:AU24
                try:
                    au_str = row.get("action_units", "[]")
                    aus = eval(au_str) if au_str.startswith('[') else []
                    # AU6 is index 3, AU12 is index 6
                    au6 = float(aus[3]) if len(aus) > 3 else 0.0
                    au12 = float(aus[6]) if len(aus) > 6 else 0.0
                except:
                    au6 = 0.0
                    au12 = 0.0

                frames.append({
                    "frame":       i,
                    # FIX: openface-test's process_video() writes
                    # datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # into the 'timestamp' column -- a wall-clock string
                    # (e.g. '2026-06-21 12:38:38'), not a video-relative
                    # number of seconds. Confirmed by reading the actual
                    # installed package source (openface/demo.py); this is
                    # not something that varies by input, so there's no
                    # fallback case where the column is ever numeric. The
                    # row.get("timestamp", i/30.0) default never helped --
                    # the key is always present, just always non-numeric --
                    # so float() reliably crashed on every real video.
                    # Just compute frame-index-based timing directly.
                    "timestamp_s": i / 30.0,
                    "confidence":  confidence,
                    "au6":         au6,
                    "au12":        au12,
                    "smile":       (au6 > 1.0 and au12 > 1.5),
                    "head_yaw":    float(row.get("gaze_yaw", 0)),
                    "head_pitch":  float(row.get("gaze_pitch", 0)),
                    "gaze_x":      float(row.get("gaze_yaw", 0)),
                    "gaze_y":      float(row.get("gaze_pitch", 0)),
                })
    except Exception as e:
        logger.error(f"Error parsing OpenFace output: {e}")
        ret = _mock_openface_result()
        ret["error"] = f"parse_failure: {str(e)[:200]}"
        return ret

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
