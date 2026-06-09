FROM python:3.11-slim

WORKDIR /app

# System dependencies for OpenCV + OpenFace
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
    build-essential cmake git wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download OpenFace model
RUN openface download || true

COPY . .

# Create video storage directory
RUN mkdir -p /data/videos

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
