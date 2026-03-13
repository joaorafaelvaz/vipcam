from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()

EMOTION_NAMES = [
    "anger", "contempt", "disgust", "fear",
    "happiness", "neutral", "sadness", "surprise",
]


@dataclass
class EmotionResult:
    anger: float
    contempt: float
    disgust: float
    fear: float
    happiness: float
    neutral: float
    sadness: float
    surprise: float
    dominant_emotion: str
    valence: float
    arousal: float
    satisfaction_score: float

    def to_dict(self) -> dict[str, float]:
        return {name: getattr(self, name) for name in EMOTION_NAMES}


def compute_valence(scores: dict[str, float]) -> float:
    return (
        scores["happiness"] * 1.0
        + scores["surprise"] * 0.5
        + scores["neutral"] * 0.0
        + scores["sadness"] * -0.5
        + scores["fear"] * -0.7
        + scores["anger"] * -0.8
        + scores["disgust"] * -0.9
        + scores["contempt"] * -0.4
    )


def compute_arousal(scores: dict[str, float]) -> float:
    return (
        scores["anger"] * 0.9
        + scores["fear"] * 0.8
        + scores["surprise"] * 0.8
        + scores["happiness"] * 0.7
        + scores["disgust"] * 0.5
        + scores["contempt"] * 0.3
        + scores["sadness"] * 0.3
        + scores["neutral"] * 0.1
    )


def compute_satisfaction(scores: dict[str, float]) -> float:
    raw = (
        5.0
        + scores["happiness"] * 5.0
        + scores["surprise"] * 1.5
        - scores["anger"] * 4.0
        - scores["disgust"] * 3.5
        - scores["sadness"] * 2.5
        - scores["fear"] * 2.0
        - scores["contempt"] * 3.0
    )
    return max(0.0, min(10.0, raw))


# ImageNet normalization constants
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)


class EmotionAnalyzer:
    """Emotion recognition using ONNX Runtime.

    Uses a pre-converted ONNX model (from HSEmotion enet_b2_8 weights).
    This avoids the timm segfault issue in NVIDIA CUDA containers.
    """

    def __init__(self, model_name: str = "enet_b2_8"):
        self.model_name = model_name
        self._session = None

    def load(self, device: str = "cuda:0"):
        import onnxruntime as ort

        onnx_path = self._find_onnx_model()
        if not onnx_path:
            raise FileNotFoundError(
                f"ONNX emotion model not found for {self.model_name}. "
                "Run: python scripts/convert_emotion_onnx.py"
            )

        # Select providers based on device
        available = ort.get_available_providers()
        if "cuda" in device and "CUDAExecutionProvider" in available:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        else:
            providers = ["CPUExecutionProvider"]

        logger.info("Loading emotion ONNX model...", path=onnx_path, providers=providers)
        self._session = ort.InferenceSession(onnx_path, providers=providers)
        logger.info("Emotion ONNX model loaded successfully", providers=providers)

    def _find_onnx_model(self) -> str | None:
        """Search common locations for the ONNX model file."""
        candidates = [
            f"/models/{self.model_name}.onnx",
            f"/app/models/{self.model_name}.onnx",
            str(Path.home() / ".cache" / "hsemotion" / f"{self.model_name}.onnx"),
            f"models/{self.model_name}.onnx",
        ]
        for path in candidates:
            if Path(path).exists():
                return path
        return None

    def analyze(self, frame: np.ndarray, face_bbox: list[float]) -> EmotionResult:
        if self._session is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        x1, y1, x2, y2 = [int(v) for v in face_bbox]
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        face_crop = frame[y1:y2, x1:x2]
        if face_crop.size == 0:
            return self._neutral_result()

        # Resize small faces
        min_size = 64
        fh, fw = face_crop.shape[:2]
        if fh < min_size or fw < min_size:
            scale = max(min_size / fh, min_size / fw)
            face_crop = cv2.resize(
                face_crop,
                (int(fw * scale), int(fh * scale)),
                interpolation=cv2.INTER_LINEAR,
            )

        # Preprocess: BGR→RGB, resize to 260x260, normalize with ImageNet stats
        face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        face_resized = cv2.resize(face_rgb, (260, 260), interpolation=cv2.INTER_LINEAR)
        face_float = face_resized.astype(np.float32) / 255.0
        face_normalized = (face_float - IMAGENET_MEAN) / IMAGENET_STD

        # HWC → CHW → NCHW
        input_tensor = face_normalized.transpose(2, 0, 1)[np.newaxis, ...]
        input_tensor = input_tensor.astype(np.float32)

        # Run inference
        logits = self._session.run(None, {"input": input_tensor})[0].flatten()

        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / exp_logits.sum()

        # Map to emotion names
        hsemotion_order = [
            "anger", "contempt", "disgust", "fear",
            "happiness", "neutral", "sadness", "surprise",
        ]

        scores = {}
        for i, name in enumerate(hsemotion_order):
            scores[name] = float(probs[i]) if i < len(probs) else 0.0

        # Ensure all keys exist and normalize
        for name in EMOTION_NAMES:
            if name not in scores:
                scores[name] = 0.0
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}

        dominant = max(scores, key=scores.get)
        valence = compute_valence(scores)
        arousal = compute_arousal(scores)
        satisfaction = compute_satisfaction(scores)

        return EmotionResult(
            anger=scores.get("anger", 0),
            contempt=scores.get("contempt", 0),
            disgust=scores.get("disgust", 0),
            fear=scores.get("fear", 0),
            happiness=scores.get("happiness", 0),
            neutral=scores.get("neutral", 0),
            sadness=scores.get("sadness", 0),
            surprise=scores.get("surprise", 0),
            dominant_emotion=dominant,
            valence=valence,
            arousal=arousal,
            satisfaction_score=satisfaction,
        )

    def _neutral_result(self) -> EmotionResult:
        return EmotionResult(
            anger=0, contempt=0, disgust=0, fear=0,
            happiness=0, neutral=1.0, sadness=0, surprise=0,
            dominant_emotion="neutral",
            valence=0.0, arousal=0.1, satisfaction_score=5.0,
        )
