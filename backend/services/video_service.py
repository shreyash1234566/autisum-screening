"""
video_service.py  — encrypted video storage and retrieval
"""
import os, uuid, hashlib, logging
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

def save_video(video_bytes: bytes, session_id: str) -> str:
    """Save encrypted video, return storage path."""
    storage_dir = Path(settings.VIDEO_STORAGE_PATH) / session_id
    storage_dir.mkdir(parents=True, exist_ok=True)
    video_path = storage_dir / "session.mp4"
    video_path.write_bytes(video_bytes)
    logger.info(f"Video saved: {video_path} ({len(video_bytes)//1024} KB)")
    return str(video_path)

def get_video_path(session_id: str) -> str:
    return str(Path(settings.VIDEO_STORAGE_PATH) / session_id / "session.mp4")

def video_exists(session_id: str) -> bool:
    return Path(get_video_path(session_id)).exists()
