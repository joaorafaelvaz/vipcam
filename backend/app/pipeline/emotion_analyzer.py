from dataclasses import dataclass

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


class EmotionAnalyzer:
    """HSEmotion enet_b2_8 wrapper for facial emotion recognition."""

    def __init__(self, model_name: str = "enet_b2_8"):
        self.model_name = model_name
        self._recognizer = None
        self._device = None

    def load(self, device: str = "cuda:0"):
        import torch
        from hsemotion.facial_emotions import HSEmotionRecognizer

        self._device = device
        logger.info("Loading HSEmotion model...", model=self.model_name, device=device)
        # PyTorch 2.6+ defaults weights_only=True which breaks hsemotion loading
        _original_load = torch.load
        torch.load = lambda *args, **kwargs: _original_load(
            *args, **{**kwargs, "weights_only": False},
        )
        try:
            self._recognizer = HSEmotionRecognizer(
                model_name=self.model_name,
                device=device,
            )
        finally:
            torch.load = _original_load
        logger.info("HSEmotion loaded successfully", device=device)

    def analyze(self, frame: np.ndarray, face_bbox: list[float]) -> EmotionResult:
        if self._recognizer is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        x1, y1, x2, y2 = [int(v) for v in face_bbox]
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        face_crop = frame[y1:y2, x1:x2]
        if face_crop.size == 0:
            return self._neutral_result()

        # Resize to a decent size for better emotion recognition
        min_size = 64
        fh, fw = face_crop.shape[:2]
        if fh < min_size or fw < min_size:
            scale = max(min_size / fh, min_size / fw)
            face_crop = cv2.resize(
                face_crop,
                (int(fw * scale), int(fh * scale)),
                interpolation=cv2.INTER_LINEAR,
            )

        # Try with logits=True first, fall back to logits=False
        try:
            emotion_label, raw_scores = self._recognizer.predict_emotions(face_crop, logits=True)
        except TypeError:
            # Some HSEmotion versions don't support logits param
            emotion_label, raw_scores = self._recognizer.predict_emotions(face_crop)

        # Build scores dict — HSEmotion returns scores in a specific order
        hsemotion_order = [
            "anger", "contempt", "disgust", "fear",
            "happiness", "neutral", "sadness", "surprise",
        ]

        if isinstance(raw_scores, dict):
            scores = {k.lower(): v for k, v in raw_scores.items()}
        elif hasattr(raw_scores, '__len__'):
            # raw_scores is a numpy array or list — apply softmax for proper probabilities
            arr = np.array(raw_scores, dtype=np.float64).flatten()
            exp_arr = np.exp(arr - np.max(arr))
            probs = exp_arr / exp_arr.sum()
            scores = {}
            for i, name in enumerate(hsemotion_order):
                scores[name] = float(probs[i]) if i < len(probs) else 0.0
        else:
            logger.debug("Unexpected raw_scores format from HSEmotion", type=type(raw_scores).__name__)
            return self._neutral_result()

        # Ensure all emotion keys exist
        for name in EMOTION_NAMES:
            if name not in scores:
                scores[name] = 0.0

        # Normalize to proper probabilities
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}

        # Use HSEmotion's label as dominant if valid, otherwise pick highest score
        emotion_str = str(emotion_label).lower().strip()
        if emotion_str in scores and scores[emotion_str] > 0.01:
            dominant = emotion_str
        else:
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
