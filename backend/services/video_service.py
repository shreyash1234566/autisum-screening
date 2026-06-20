"""
video_service.py — encrypted video storage and retrieval

Each session now produces up to THREE clips (Task A, B, C — gaze tasks that
use the camera). Task D never touches the camera, so it has no clip.
Each task's video is stored under its own filename so they never collide
or overwrite one another.
"""
import logging
from pathlib import Path
from typing import Literal
from config import settings

logger = logging.getLogger(__name__)

TaskName = Literal["task_a", "task_b", "task_c"]
VALID_TASKS = ("task_a", "task_b", "task_c")


def save_video(video_bytes: bytes, session_id: str, task: TaskName) -> str:
    """Save one task's video clip, return its storage path."""
    if task not in VALID_TASKS:
        raise ValueError(f"Invalid task '{task}'; must be one of {VALID_TASKS}")

    storage_dir = Path(settings.VIDEO_STORAGE_PATH) / session_id
    storage_dir.mkdir(parents=True, exist_ok=True)
    video_path = storage_dir / f"{task}.mp4"
    video_path.write_bytes(video_bytes)
    logger.info(f"Video saved [{task}]: {video_path} ({len(video_bytes)//1024} KB)")
    return str(video_path)


def get_video_path(session_id: str, task: TaskName) -> str:
    return str(Path(settings.VIDEO_STORAGE_PATH) / session_id / f"{task}.mp4")


def video_exists(session_id: str, task: TaskName) -> bool:
    return Path(get_video_path(session_id, task)).exists()
