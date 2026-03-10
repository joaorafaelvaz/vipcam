#!/bin/bash
set -e

MODEL_DIR="${1:-./models}"
mkdir -p "$MODEL_DIR"

echo "=== Downloading AI models for VIPCam ==="

# 1. YOLOv8x
echo "[1/3] Downloading YOLOv8x..."
if [ ! -f "$MODEL_DIR/yolov8x.pt" ]; then
    python3 -c "from ultralytics import YOLO; YOLO('yolov8x.pt')"
    mv yolov8x.pt "$MODEL_DIR/" 2>/dev/null || true
    echo "  YOLOv8x downloaded."
else
    echo "  YOLOv8x already exists, skipping."
fi

# 2. InsightFace buffalo_l
echo "[2/3] Downloading InsightFace buffalo_l..."
python3 -c "
from insightface.app import FaceAnalysis
app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=-1, det_size=(640, 640))
print('  InsightFace buffalo_l downloaded and cached.')
"

# 3. HSEmotion enet_b2_8
echo "[3/3] Downloading HSEmotion enet_b2_8..."
python3 -c "
from hsemotion.facial_emotions import HSEmotionRecognizer
recognizer = HSEmotionRecognizer(model_name='enet_b2_8', device='cpu')
print('  HSEmotion enet_b2_8 downloaded and cached.')
"

echo "=== All models downloaded successfully ==="
echo "Model directory: $MODEL_DIR"
