import time
from dataclasses import dataclass, field

import numpy as np
import structlog

from app.config import settings
from app.pipeline.detector import Detection, PersonDetector
from app.pipeline.emotion_analyzer import EmotionAnalyzer, EmotionResult
from app.pipeline.recognizer import FaceData, FaceRecognizer

logger = structlog.get_logger()


@dataclass
class FaceResult:
    person_id: str | None
    bbox: list[float]
    emotions: EmotionResult
    face_data: FaceData
    similarity: float
    is_new: bool


@dataclass
class FrameResult:
    camera_id: str
    timestamp: float
    person_count: int
    detections: list[Detection]
    faces: list[FaceResult]
    processing_time_ms: float


class GPUWorker:
    """Single-process GPU inference orchestrator for all ML models."""

    def __init__(self):
        self._detector = PersonDetector(
            model_path=settings.yolo_model_path,
            imgsz=settings.yolo_imgsz,
            conf=settings.yolo_conf,
        )
        self._recognizer = FaceRecognizer(
            model_name=settings.insightface_model_name,
            det_size=settings.insightface_det_size,
        )
        self._emotion_analyzer = EmotionAnalyzer(
            model_name=settings.hsemotion_model_name,
        )
        self._loaded = False

    def load_models(self):
        if self._loaded:
            return
        logger.info("Loading GPU models...")

        # Load each model independently so a single failure doesn't kill the process
        try:
            self._detector.load()
            logger.info("YOLO detector loaded")
        except Exception as e:
            logger.error("Failed to load YOLO detector", error=str(e))
            self._detector = None

        try:
            self._recognizer.load()
            logger.info("InsightFace recognizer loaded")
        except Exception as e:
            logger.error("Failed to load InsightFace recognizer", error=str(e))
            self._recognizer = None

        # HSEmotion causes segfault in some environments — load in subprocess to test
        import subprocess
        import sys
        test_result = subprocess.run(
            [sys.executable, "-c", "from hsemotion.facial_emotions import HSEmotionRecognizer"],
            capture_output=True, timeout=30,
        )
        if test_result.returncode != 0:
            logger.warning(
                "HSEmotion import test failed (likely segfault) — skipping emotion analyzer",
                returncode=test_result.returncode,
            )
            self._emotion_analyzer = None
        else:
            try:
                self._emotion_analyzer.load()
                logger.info("HSEmotion analyzer loaded")
            except Exception as e:
                logger.error("Failed to load HSEmotion analyzer", error=str(e))
                self._emotion_analyzer = None

        self._loaded = True

        try:
            import torch
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / 1024**3
                reserved = torch.cuda.memory_reserved() / 1024**3
                logger.info(
                    "GPU models loaded",
                    vram_allocated_gb=f"{allocated:.2f}",
                    vram_reserved_gb=f"{reserved:.2f}",
                    detector=self._detector is not None,
                    recognizer=self._recognizer is not None,
                    emotion_analyzer=self._emotion_analyzer is not None,
                )
        except Exception:
            logger.info("GPU models loaded (VRAM info unavailable)")

    def process_frame(self, camera_id: str, frame: np.ndarray) -> FrameResult:
        if not self._loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")

        start = time.monotonic()

        # 1. Detect persons
        detections = []
        if self._detector is not None:
            detections = self._detector.detect_with_tracking(frame)

        # 2. Detect and analyze faces
        face_datas = []
        if self._recognizer is not None:
            face_datas = self._recognizer.analyze(frame)

        # 3. For each face, run emotion analysis (or use neutral fallback)
        face_results: list[FaceResult] = []
        for face in face_datas:
            if self._emotion_analyzer is not None:
                try:
                    emotion = self._emotion_analyzer.analyze(frame, face.bbox)
                except Exception:
                    emotion = self._emotion_analyzer._neutral_result()
            else:
                emotion = EmotionResult(
                    anger=0, contempt=0, disgust=0, fear=0,
                    happiness=0, neutral=1.0, sadness=0, surprise=0,
                    dominant_emotion="neutral",
                    valence=0.0, arousal=0.1, satisfaction_score=5.0,
                )
            face_results.append(
                FaceResult(
                    person_id=None,  # Will be filled by pipeline manager
                    bbox=face.bbox,
                    emotions=emotion,
                    face_data=face,
                    similarity=0.0,
                    is_new=True,
                )
            )

        elapsed_ms = (time.monotonic() - start) * 1000

        return FrameResult(
            camera_id=camera_id,
            timestamp=time.time(),
            person_count=len(detections),
            detections=detections,
            faces=face_results,
            processing_time_ms=elapsed_ms,
        )
