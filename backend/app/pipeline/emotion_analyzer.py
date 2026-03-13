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

# Model name → (timm backbone, num_classes)
MODEL_CONFIG = {
    "enet_b0_8_best_afew": ("tf_efficientnet_b0", 8),
    "enet_b0_8_best_vgaf": ("tf_efficientnet_b0", 8),
    "enet_b0_8_va_mtl": ("tf_efficientnet_b0", 8),
    "enet_b2_8": ("tf_efficientnet_b2", 8),
    "enet_b2_7": ("tf_efficientnet_b2", 7),
}

# HSEmotion model URLs (same as hsemotion package uses)
MODEL_URLS = {
    "enet_b0_8_best_afew": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b0_8_best_afew.pt",
    "enet_b0_8_best_vgaf": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b0_8_best_vgaf.pt",
    "enet_b0_8_va_mtl": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b0_8_va_mtl.pt",
    "enet_b2_8": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b2_8.pt",
    "enet_b2_7": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b2_7.pt",
}


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


class EmotionAnalyzer:
    """Emotion recognition using timm + HSEmotion weights directly.

    Bypasses the HSEmotionRecognizer class which can segfault on certain
    CUDA/timm/torch combinations. Loads the model backbone via timm and
    applies the HSEmotion pretrained weights manually.
    """

    def __init__(self, model_name: str = "enet_b2_8"):
        self.model_name = model_name
        self._model = None
        self._device = None
        self._transform = None

    def load(self, device: str = "cuda:0"):
        import torch
        import timm
        from torchvision import transforms

        self._device = device
        logger.info("Loading emotion model (direct timm)...", model=self.model_name, device=device)

        if self.model_name not in MODEL_CONFIG:
            raise ValueError(f"Unknown model: {self.model_name}. Available: {list(MODEL_CONFIG.keys())}")

        backbone_name, num_classes = MODEL_CONFIG[self.model_name]

        # Create the timm model
        model = timm.create_model(backbone_name, pretrained=False, num_classes=num_classes)

        # Download weights if not cached
        weights_path = self._get_weights_path()

        # Load weights
        state_dict = torch.load(weights_path, map_location=device, weights_only=False)

        # HSEmotion saves the full model state, not just state_dict.
        # Handle both cases.
        if isinstance(state_dict, dict) and "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]
        elif not isinstance(state_dict, dict):
            # It might be the full model — extract state_dict
            if hasattr(state_dict, "state_dict"):
                state_dict = state_dict.state_dict()

        # Try to load. Some HSEmotion weights have different key names.
        try:
            model.load_state_dict(state_dict, strict=False)
        except Exception as e:
            logger.warning("Partial state_dict load", error=str(e))

        model.to(device)
        model.eval()
        self._model = model

        # Standard ImageNet normalization (what HSEmotion uses internally)
        self._transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((260, 260)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        logger.info("Emotion model loaded successfully (direct timm)", device=device, model=self.model_name)

    def _get_weights_path(self) -> str:
        """Get the path to model weights, downloading if necessary."""
        import torch

        cache_dir = Path.home() / ".cache" / "hsemotion"
        cache_dir.mkdir(parents=True, exist_ok=True)
        weights_file = cache_dir / f"{self.model_name}.pt"

        if weights_file.exists():
            logger.info("Using cached emotion weights", path=str(weights_file))
            return str(weights_file)

        # Try torch hub cache too (where HSEmotionRecognizer would have put it)
        hub_dir = Path(torch.hub.get_dir()) / "checkpoints"
        hub_file = hub_dir / f"{self.model_name}.pt"
        if hub_file.exists():
            logger.info("Using torch hub cached weights", path=str(hub_file))
            return str(hub_file)

        # Download
        url = MODEL_URLS.get(self.model_name)
        if not url:
            raise FileNotFoundError(f"No download URL for model {self.model_name}")

        logger.info("Downloading emotion model weights...", url=url)
        torch.hub.download_url_to_file(url, str(weights_file))
        logger.info("Emotion weights downloaded", path=str(weights_file))
        return str(weights_file)

    def analyze(self, frame: np.ndarray, face_bbox: list[float]) -> EmotionResult:
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        import torch

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

        # Convert BGR → RGB
        face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)

        # Transform and run inference
        input_tensor = self._transform(face_rgb).unsqueeze(0).to(self._device)

        with torch.no_grad():
            logits = self._model(input_tensor)

        # Convert logits to probabilities via softmax
        probs = torch.nn.functional.softmax(logits, dim=1).cpu().numpy().flatten()

        # Map to emotion names
        hsemotion_order = [
            "anger", "contempt", "disgust", "fear",
            "happiness", "neutral", "sadness", "surprise",
        ]

        scores = {}
        for i, name in enumerate(hsemotion_order):
            scores[name] = float(probs[i]) if i < len(probs) else 0.0

        # Ensure all keys exist
        for name in EMOTION_NAMES:
            if name not in scores:
                scores[name] = 0.0

        # Normalize
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
