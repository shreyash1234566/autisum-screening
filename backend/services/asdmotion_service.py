"""
asdmotion_service.py
Stereotypical repetitive-movement detection.

WHY THIS IS NOT THE Dinstein-Lab ASDMotion REPO (audit findings):

1. The backend previously targeted src/asdmotion/detector/detector.py.
   That file is a plain module (Predictor class) with NO __main__ guard,
   NO argparse -- it accepts no CLI arguments at all. Calling it as a
   subprocess with --video/--output silently no-ops: detector.py imports
   cleanly and exits 0 with empty stdout. Downstream json.loads("") then
   raises JSONDecodeError. (Confirmed: `grep __main__/argparse` on the
   real file returns nothing.)

2. The REAL CLI entry point is src/asdmotion/detector/executor.py, which
   accepts -cfg/-video/-out/-gpu. But even calling that correctly fails,
   because resources/configs/config.yaml ships with literal placeholders:
       open_pose_path:  <Path to openpose root directory>
       mmaction_path:   <Path to mmaction2 root directory>
       mmlab_python_path: <Path to open-mmlab python executable>
   executor.py's VideoTransformer/Predictor require a working OpenPose
   binary (Caffe-based skeleton extraction, GPU build) and a separate
   MMAction2 Python environment with pretrained classification weights.
   None of these can be produced by `docker-compose build` -- OpenPose's
   build alone needs CUDA + Caffe + several GB of disk, and MMAction2's
   weights are not redistributed in the repo (Google-Drive-only).

Given this, real ASDMotion cannot run in this Docker stack. This module
replaces it with a from-scratch MediaPipe Pose + FFT detector that:
  - Runs on CPU, pip-installable (mediapipe), no external binaries
  - Produces real per-segment scores (never a hardcoded/mocked value)
  - Targets the same physical signal ASDMotion targets: stereotypical
    repetitive movement (hand-flapping ~1-4 Hz, body rocking ~0.5-2 Hz)

Method:
  1. Extract 33-point MediaPipe Pose landmarks per frame
  2. Track wrist/elbow/shoulder y-displacement (bilateral)
  3. Slide a ~5s window (150 frames @30fps, 45-frame step) over the video
  4. Per window: Hanning-windowed FFT on the detrended signal
  5. Score = spectral power in 0.5-4 Hz band / total power
  6. Flag windows where score > 0.30

This is a heuristic, not a clinically validated detector. See report.
"""
import logging
import os
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# -- Pose landmark indices (MediaPipe Pose 33-point model) -------------------
LEFT_WRIST, RIGHT_WRIST       = 15, 16
LEFT_ELBOW, RIGHT_ELBOW       = 13, 14
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12

TRACKED_JOINTS = [LEFT_WRIST, RIGHT_WRIST, LEFT_ELBOW, RIGHT_ELBOW, LEFT_SHOULDER, RIGHT_SHOULDER]

WINDOW_FRAMES  = 150   # ~5s @ 30fps
STEP_FRAMES    = 45    # ~1.5s step
ROCKING_LOW    = 0.5   # Hz
HAND_FLAP_HIGH = 4.0   # Hz
FLAG_THRESHOLD = 0.30


def run_asdmotion(video_path: Optional[str]) -> dict:
    """
    Run repetitive-movement detection on a session video.
    Returns per-segment stereotypy scores and an aggregate repetitive_score.
    Never returns mock=True except when the video itself is unusable.
    """
    if not video_path or not os.path.exists(video_path):
        logger.warning(f"Video not found or empty path: {video_path}")
        ret = _mock_asdmotion()
        ret["error"] = "video_not_found"
        return ret

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning(f"Cannot open video for ASDMotion analysis: {video_path}")
        cap.release()
        ret = _mock_asdmotion()
        ret["error"] = "video_unreadable"
        return ret

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if frame_count < WINDOW_FRAMES:
        logger.warning(
            f"Video too short for ASDMotion analysis: {frame_count} frames "
            f"(need >= {WINDOW_FRAMES}). Returning empty (non-mock) result."
        )
        return {"repetitive_score": 0.0, "segments": [], "note": "video_too_short"}

    try:
        return _analyse_video(video_path, fps)
    except ImportError:
        logger.error("mediapipe not installed. Add mediapipe==0.10.14 to requirements.txt")
        return _mock_asdmotion()
    except Exception as e:
        logger.error(f"ASDMotion (MediaPipe) analysis failed: {e}", exc_info=True)
        ret = _mock_asdmotion()
        ret["error"] = str(e)[:300]
        return ret


def _analyse_video(video_path: str, fps: float) -> dict:
    import mediapipe as mp
    mp_pose = mp.solutions.pose

    joint_trajectories = {j: [] for j in TRACKED_JOINTS}
    timestamps = []

    cap = cv2.VideoCapture(video_path)
    frame_idx = 0

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        while cap.isOpened():
            ret, bgr = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = pose.process(rgb)

            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                for j in TRACKED_JOINTS:
                    joint_trajectories[j].append((lm[j].y, lm[j].x, lm[j].visibility))
            else:
                for j in TRACKED_JOINTS:
                    joint_trajectories[j].append((float('nan'), float('nan'), 0.0))

            timestamps.append(frame_idx / fps)
            frame_idx += 1

    cap.release()
    logger.info(f"ASDMotion (MediaPipe): extracted {frame_idx} frames from {video_path}")

    if frame_idx < WINDOW_FRAMES:
        return {"repetitive_score": 0.0, "segments": [], "note": "too_few_pose_frames"}

    segments = _windowed_spectral_analysis(joint_trajectories, timestamps, fps)
    return _aggregate_asdmotion(segments)


def _windowed_spectral_analysis(trajectories: dict, timestamps: list, fps: float) -> list:
    n = len(timestamps)
    segments = []

    for start in range(0, n - WINDOW_FRAMES + 1, STEP_FRAMES):
        end = start + WINDOW_FRAMES
        t_start, t_end = timestamps[start], timestamps[min(end - 1, n - 1)]

        all_signals = []
        for j in TRACKED_JOINTS:
            traj = trajectories[j][start:end]
            ys  = np.array([p[0] for p in traj], dtype=float)
            vis = np.array([p[2] for p in traj], dtype=float)

            visible_mask = (vis > 0.5) & ~np.isnan(ys)
            if visible_mask.sum() < WINDOW_FRAMES * 0.5:
                continue

            ys_interp = _interp_nan(ys)
            all_signals.append(ys_interp - np.nanmean(ys_interp))

        if not all_signals:
            segments.append({
                "start_s": round(t_start, 2), "end_s": round(t_end, 2),
                "stereotypy_score": 0.0, "dominant_freq_hz": 0.0,
                "note": "no_visible_joints",
            })
            continue

        combined = np.mean(all_signals, axis=0)
        score, dominant_freq = _spectral_score(combined, fps)

        segments.append({
            "start_s": round(t_start, 2), "end_s": round(t_end, 2),
            "stereotypy_score": round(score, 4),
            "dominant_freq_hz": round(dominant_freq, 3),
            "flagged": score > FLAG_THRESHOLD,
        })

    return segments


def _spectral_score(signal: np.ndarray, fps: float) -> tuple:
    n = len(signal)
    if n < 8:
        return 0.0, 0.0

    windowed = signal * np.hanning(n)
    fft_mag  = np.abs(np.fft.rfft(windowed))
    freqs    = np.fft.rfftfreq(n, d=1.0 / fps)

    total_power = np.sum(fft_mag ** 2)
    if total_power < 1e-10:
        return 0.0, 0.0

    band_mask  = (freqs >= ROCKING_LOW) & (freqs <= HAND_FLAP_HIGH)
    band_power = np.sum(fft_mag[band_mask] ** 2)
    score = float(band_power / total_power)

    dominant_idx  = int(np.argmax(fft_mag))
    dominant_freq = float(freqs[dominant_idx]) if dominant_idx < len(freqs) else 0.0
    return score, dominant_freq


def _interp_nan(y: np.ndarray) -> np.ndarray:
    nans = np.isnan(y)
    if not nans.any():
        return y
    x = np.arange(len(y))
    y_interp = y.copy()
    y_interp[nans] = np.interp(x[nans], x[~nans], y[~nans]) if (~nans).any() else 0.0
    return y_interp


def _aggregate_asdmotion(segments: list) -> dict:
    if not segments:
        return {"repetitive_score": 0.0, "segments": []}

    scores = [s.get("stereotypy_score", 0.0) for s in segments]
    mean_score = float(np.mean(scores))
    max_score  = float(np.max(scores))
    flagged    = sum(1 for s in scores if s > FLAG_THRESHOLD)

    logger.info(
        f"ASDMotion (MediaPipe): {len(segments)} segments, "
        f"mean={mean_score:.3f}, max={max_score:.3f}, flagged={flagged}"
    )

    return {
        "repetitive_score":  round(mean_score, 4),
        "max_segment_score": round(max_score, 4),
        "flagged_segments":  flagged,
        "total_segments":    len(segments),
        "segments":          segments,
    }


def _mock_asdmotion() -> dict:
    logger.warning("Using mock ASDMotion -- video unusable for pose analysis")
    return {"repetitive_score": 0.0, "mock": True}
