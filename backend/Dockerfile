# =============================================================================
# Stage 1: Convert HSEmotion model to ONNX in a clean Python environment
# (timm segfaults in the nvidia/cuda container, so we do this separately)
# =============================================================================
FROM python:3.11-slim AS onnx-converter

RUN pip install --no-cache-dir "torch<2.6" "torchvision<0.21" --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir "timm>=0.9.0,<1.0.0" onnxruntime onnx

WORKDIR /convert
COPY scripts/convert_emotion_onnx.py .
RUN python convert_emotion_onnx.py enet_b2_8 /models/enet_b2_8.onnx

# =============================================================================
# Stage 2: Main application image with NVIDIA CUDA runtime
# =============================================================================
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev python3-pip \
    build-essential g++ \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy pre-converted ONNX emotion model from stage 1
COPY --from=onnx-converter /models/enet_b2_8.onnx /models/enet_b2_8.onnx

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir ".[dev]"

# Copy application code
COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000}"]
