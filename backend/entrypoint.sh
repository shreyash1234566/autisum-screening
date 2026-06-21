#!/bin/bash
# entrypoint.sh
#
# WHY THIS EXISTS:
# OpenFace weights used to be downloaded during `docker build` (RUN openface
# download --output /opt/weights), baked directly into the image layer.
# That meant EVERY Dockerfile edit -- and there have been several over the
# course of fixing OpenFace's relative-path bug, its frame-vs-path crash,
# and the HF download timeout -- triggered a full rebuild that re-downloaded
# and re-baked ~300-500MB of weights into a brand new image layer. The old
# image (with its own copy of the same weights) becomes dangling but still
# eats disk until pruned. Across 5+ rebuild attempts in a disk-constrained
# Codespace, that adds up to multiple GB of duplicate weight layers sitting
# around doing nothing.
#
# Fix: weights now live in a named Docker volume (openface_weights:/opt/weights
# in docker-compose.yml), decoupled from the image entirely. This script runs
# at container START, not build time: download once, on first run; every
# subsequent container start (including after a code-only rebuild) finds the
# weights already in the volume and skips straight to starting the app.
set -e

WEIGHTS_DIR="/opt/weights"
MARKER_FILE="$WEIGHTS_DIR/Alignment_RetinaFace.pth"

if [ ! -f "$MARKER_FILE" ]; then
    echo "[entrypoint] OpenFace weights not found in volume at $WEIGHTS_DIR -- downloading (first run only)..."

    # Same timeout/retry logic that used to live in the Dockerfile -- HF's
    # own default read timeout (10s) is too tight for a slow/throttled
    # network, and snapshot_download() resumes/skips files it already has,
    # so retrying is cheap even on a partial failure.
    export HF_HUB_DOWNLOAD_TIMEOUT=120

    # IMPORTANT: this calls snapshot_download() directly via Python, NOT
    # the `openface download` CLI command. Checked the actual installed
    # package source (openface/cli.py):
    #   if not os.path.exists(save_path):
    #       ... snapshot_download(...) ...
    #   else:
    #       print("Weights already exist. Skipping download.")
    # That check only looks at whether the DIRECTORY exists -- not whether
    # it's empty or contains the expected files. Docker creates a named
    # volume's mount point as an empty directory the instant it's attached,
    # before this script even runs. So `os.path.exists(save_path)` is True
    # on the very first run against a fresh volume, the CLI concludes
    # "weights already exist", and permanently skips downloading anything
    # -- every single time, forever. snapshot_download() itself has no such
    # bug: it checks each file's own completeness, so it's safe to call
    # directly and safe to retry.
    success=0
    for i in 1 2 3 4 5; do
        if /venv/bin/python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='nutPace/openface_weights', local_dir='$WEIGHTS_DIR', repo_type='model')
print('snapshot_download completed')
"; then
            success=1
            break
        fi
        echo "[entrypoint] weights download attempt $i/5 failed, retrying in 10s..."
        sleep 10
    done

    if [ "$success" -ne 1 ] || [ ! -f "$MARKER_FILE" ]; then
        echo "[entrypoint] ERROR: OpenFace weights download failed after $i attempt(s)." >&2
        echo "[entrypoint] Backend will still start -- openface_service.py falls back to a mock result when weights are missing, it will not crash the app." >&2
    else
        echo "[entrypoint] OpenFace weights downloaded successfully."
    fi
else
    echo "[entrypoint] OpenFace weights already present in volume, skipping download."
fi

# Hand off to whatever CMD docker-compose specified (e.g. the --reload
# uvicorn command in dev, or the Dockerfile's own CMD if none is given).
exec "$@"
