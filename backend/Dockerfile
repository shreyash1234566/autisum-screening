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
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    git \
    cmake \
    libopencv-dev \
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
    /venv/bin/pip install --no-cache-dir ffmpeg-python omegaconf openface-test

# ─── Stage 2: lean runtime ───────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

WORKDIR /app

# Only the shared libraries opencv-python-headless needs at runtime.
# No build headers (libgl-dev, etc.) — those stay in the builder.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built venv from Stage 1.
# The final image contains zero build tools.
COPY --from=builder /venv /venv

# Download OpenFace models
RUN /venv/bin/openface download


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
