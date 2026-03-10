import time
from collections import deque

from app.config import settings
from app.pipeline.emotion_analyzer import (
    EMOTION_NAMES,
    EmotionResult,
    compute_arousal,
    compute_satisfaction,
    compute_valence,
)


class EmotionSmoother:
    """EMA-based temporal smoothing for per-person emotion readings."""

    def __init__(
        self,
        alpha: float | None = None,
        buffer_size: int = 10,
        evict_after: float = 30.0,
        shift_min_frames: int | None = None,
    ):
        self.alpha = alpha or settings.emotion_ema_alpha
        self.buffer_size = buffer_size
        self.evict_after = evict_after
        self.shift_min_frames = shift_min_frames or settings.emotion_shift_min_frames

        # person_id -> (buffer of raw results, last smoothed result, last update time)
        self._buffers: dict[str, deque[EmotionResult]] = {}
        self._smoothed: dict[str, EmotionResult] = {}
        self._last_update: dict[str, float] = {}
        self._dominant_streak: dict[str, tuple[str, int]] = {}  # (emotion, count)

    def smooth(self, person_id: str, raw: EmotionResult) -> tuple[EmotionResult, bool]:
        """
        Smooth a raw emotion reading.
        Returns (smoothed_result, sentiment_shifted).
        """
        now = time.monotonic()
        self._evict_stale(now)
        self._last_update[person_id] = now

        if person_id not in self._buffers:
            self._buffers[person_id] = deque(maxlen=self.buffer_size)
            self._smoothed[person_id] = raw
            self._buffers[person_id].append(raw)
            self._dominant_streak[person_id] = (raw.dominant_emotion, 1)
            return raw, False

        self._buffers[person_id].append(raw)
        prev = self._smoothed[person_id]

        # Apply EMA per-emotion
        smoothed_scores = {}
        for name in EMOTION_NAMES:
            raw_val = getattr(raw, name)
            prev_val = getattr(prev, name)
            smoothed_scores[name] = self.alpha * raw_val + (1 - self.alpha) * prev_val

        # Renormalize
        total = sum(smoothed_scores.values())
        if total > 0:
            smoothed_scores = {k: v / total for k, v in smoothed_scores.items()}

        dominant = max(smoothed_scores, key=smoothed_scores.get)
        valence = compute_valence(smoothed_scores)
        arousal = compute_arousal(smoothed_scores)
        satisfaction = compute_satisfaction(smoothed_scores)

        result = EmotionResult(
            **smoothed_scores,
            dominant_emotion=dominant,
            valence=valence,
            arousal=arousal,
            satisfaction_score=satisfaction,
        )
        self._smoothed[person_id] = result

        # Track dominant emotion streak for shift detection
        prev_dominant, streak = self._dominant_streak.get(person_id, (dominant, 0))
        shifted = False
        if dominant == prev_dominant:
            streak += 1
        else:
            streak = 1
        self._dominant_streak[person_id] = (dominant, streak)

        if dominant != prev_dominant and streak >= self.shift_min_frames:
            shifted = True

        return result, shifted

    def evict(self, person_id: str):
        self._buffers.pop(person_id, None)
        self._smoothed.pop(person_id, None)
        self._last_update.pop(person_id, None)
        self._dominant_streak.pop(person_id, None)

    def _evict_stale(self, now: float):
        expired = [
            pid for pid, ts in self._last_update.items()
            if now - ts > self.evict_after
        ]
        for pid in expired:
            self.evict(pid)
