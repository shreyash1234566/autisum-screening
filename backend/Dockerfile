# =============================================================================
# AutiScreen — Backend Dockerfile  (multi-stage, optimised)
#
# Stage 1  compiles C-extension wheels (gcc etc.) inside a builder image.
# Stage 2  is the lean runtime — compiler never makes it to production.
#
# ASDMotion note:
#   Real ASDMotion (Dinstein-Lab) requires OpenPose + MMAction2 + GPU +
#   Google-Drive-only weights -- not deployable via docker-compose build.
#   asdmotion_service.py uses a MediaPipe Pose + FFT detector instead,
#   which is real (non-mock) analysis running entirely on CPU.
# =============================================================================

# ─── Stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# ─── Build-only tools ────────────────────────────────────────────────────────
# NOTE: removed libopencv-dev and cmake. Every OpenCV/mediapipe dependency
# here resolves to a precompiled manylinux wheel (opencv-python-headless,
# mediapipe) -- nothing in this build actually compiles against OpenCV C
# headers or runs a CMake build. libopencv-dev alone is commonly 800MB-1.5GB
# installed, which was a major contributor to running out of disk during
# `docker compose build` in Codespaces. gcc/g++/build-essential are kept
# since a couple of transitive deps (e.g. psycopg2 fallback paths) can still
# need a C compiler if a wheel isn't available for the exact platform/Python
# combo -- those three together are a fraction of libopencv-dev's size.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# NOTE: We previously cloned https://github.com/Dinstein-Lab/ASDMotion here.
# Audit finding: real ASDMotion cannot run in this image. Its CLI entry
# point (src/asdmotion/detector/executor.py) requires a working OpenPose
# binary (CUDA + Caffe build) and a separate MMAction2 Python environment
# with pretrained weights that are Google-Drive-only (not in the repo).
# resources/configs/config.yaml ships with literal placeholder paths.
# asdmotion_service.py now uses MediaPipe Pose + FFT instead (pip-installable,
# CPU-only, no external binaries). The git clone is removed to save build
# time and image size.


COPY requirements.txt .

# Create an isolated venv, upgrade pip, install all deps inside it.
# Using a venv means we can COPY the whole /venv dir cleanly to the runtime stage.
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir --upgrade pip && \
    /venv/bin/pip install --no-cache-dir \
        torch==2.3.1+cpu torchvision==0.18.1+cpu \
        --extra-index-url https://download.pytorch.org/whl/cpu && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /venv/bin/pip install --no-cache-dir openface-test
    # NOTE: removed ffmpeg-python and omegaconf -- grepped the entire
    # backend/ codebase, neither is imported anywhere. openface-test's own
    # published dependencies (checked against its actual PyPI metadata)
    # don't list either of them, so they were pure dead weight.

# ─── Stage 2: lean runtime ───────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

WORKDIR /app

# Only the shared libraries OpenCV needs at runtime to even import cv2
# (openface-test's own dependencies pull in full opencv-python, not just
# opencv-python-headless -- see requirements.txt comment -- so these libs
# are needed for dlopen() at import time even though nothing here ever
# opens a GUI window). No build headers, no git, no ffmpeg binary -- the
# only thing that used to need ffmpeg (ffmpeg-python) has been removed.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built venv from Stage 1.
# The final image contains zero build tools.
COPY --from=builder /venv /venv

# Download OpenFace models.
#
# CRITICAL: --output is set to /opt/weights, NOT the default './weights'
# (relative to WORKDIR /app). Every weight path inside the openface-test
# package is hardcoded as a relative './weights/...' string with no env
# var or CLI override (confirmed against the actual package source:
# openface/demo.py and the vendored Pytorch_Retinaface/models/retinaface.py
# both do this). docker-compose.yml mounts ./backend:/app for dev hot-
# reload, which REPLACES the entire /app directory at container start --
# including anything baked into /app/weights during this build step. Since
# the host's backend/ folder has no weights/ dir (the download only ever
# happened inside the image), that bind mount silently erased the weights
# at runtime. /opt is never touched by any volume mount, so it survives.
# openface_service.py runs the detect-video subprocess with cwd="/opt" so
# the hardcoded "./weights/..." lookups resolve to /opt/weights/... here.
RUN /venv/bin/openface download --output /opt/weights

# PATCH: openface-test==0.1.26's FaceDetector.preprocess_image() crashes
# unconditionally on every video -- it always calls cv2.imread(image_path),
# but process_video() (the actual code behind `openface detect-video`)
# passes a raw decoded frame (np.ndarray from cv2.VideoCapture().read()),
# not a path. This is a 100%-reproducible upstream bug, confirmed by
# reading the installed package source and reproducing the exact
# "Expected 'filename' to be a str or path-like object" error locally.
# See backend/patches/openface_face_detection.py for the full writeup and
# an isolated before/after test. Overwriting the installed copy is the
# cleanest fix available without forking the whole package.
COPY patches/openface_face_detection.py /venv/lib/python3.11/site-packages/openface/face_detection.py


# App source — overridden at dev time by volume mount (see docker-compose.yml).
# Baked in here so the image works standalone without a volume mount.
COPY . .

# Video storage directory — persisted via Docker volume at runtime.
RUN mkdir -p /data/videos

EXPOSE 8000

# Python-stdlib healthcheck — no extra curl/wget package needed.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c \
      "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
      || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
