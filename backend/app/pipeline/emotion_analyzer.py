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

    def load(self):
        from hsemotion.facial_emotions import HSEmotionRecognizer

        logger.info("Loading HSEmotion model...", model=self.model_name)
        self._recognizer = HSEmotionRecognizer(
            model_name=self.model_name,
            device="cuda:0",
        )
        logger.info("HSEmotion loaded successfully")

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

        emotion, raw_scores = self._recognizer.predict_emotions(face_crop, logits=True)

        # Build scores dict — HSEmotion returns scores in a specific order
        # Map the raw scores to our standard emotion names
        hsemotion_order = [
            "anger", "contempt", "disgust", "fear",
            "happiness", "neutral", "sadness", "surprise",
        ]

        if isinstance(raw_scores, dict):
            scores = {k.lower(): v for k, v in raw_scores.items()}
        else:
            # raw_scores is a numpy array
            scores = {}
            for i, name in enumerate(hsemotion_order):
                scores[name] = float(raw_scores[i]) if i < len(raw_scores) else 0.0

        # Normalize to probabilities
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
