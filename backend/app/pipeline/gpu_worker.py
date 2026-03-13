import subprocess
import sys
import time
from dataclasses import dataclass

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

    def _test_hsemotion_load(self, device: str) -> bool:
        """Test HSEmotion load in subprocess to detect segfaults safely.

        Returns True if HSEmotion can be loaded on the given device without crashing.
        """
        test_code = (
            "import torch; "
            f"device = '{device}'; "
            "_orig = torch.load; "
            "def _patched(*a, **kw): kw.setdefault('weights_only', False); kw.setdefault('map_location', device); return _orig(*a, **kw)\n"
            "torch.load = _patched; "
            "from hsemotion.facial_emotions import HSEmotionRecognizer; "
            f"r = HSEmotionRecognizer(model_name='{settings.hsemotion_model_name}', device='{device}'); "
            "print('ok')"
        )
        try:
            result = subprocess.run(
                [sys.executable, "-c", test_code],
                capture_output=True, timeout=120, text=True,
            )
            ok = result.returncode == 0 and "ok" in result.stdout
            if not ok:
                logger.warning("HSEmotion subprocess test failed",
                               device=device,
                               returncode=result.returncode,
                               stderr=result.stderr[:500] if result.stderr else "")
            else:
                logger.info("HSEmotion subprocess test passed", device=device)
            return ok
        except Exception as e:
            logger.warning("HSEmotion subprocess test exception", device=device, error=str(e))
            return False

    def _load_hsemotion(self):
        """Try to load HSEmotion: test in subprocess first to avoid segfaults killing the main process."""
        import torch

        device = "cuda:0" if torch.cuda.is_available() else "cpu"

        # Test in subprocess first — segfaults kill the subprocess, not us
        if self._test_hsemotion_load(device):
            try:
                self._emotion_analyzer.load(device=device)
                logger.info("HSEmotion loaded", device=device)
                return
            except Exception as e:
                logger.warning("HSEmotion load failed after subprocess test passed", device=device, error=str(e))

        # If CUDA failed, try CPU in subprocess
        if device != "cpu":
            logger.warning("HSEmotion failed on CUDA — testing CPU in subprocess")
            if self._test_hsemotion_load("cpu"):
                try:
                    self._emotion_analyzer = EmotionAnalyzer(
                        model_name=settings.hsemotion_model_name,
                    )
                    self._emotion_analyzer.load(device="cpu")
                    logger.info("HSEmotion loaded on CPU (fallback)")
                    return
                except Exception as e:
                    logger.warning("HSEmotion CPU load failed after subprocess test passed", error=str(e))

        # All attempts failed — disable emotions
        logger.error("HSEmotion failed to load on all devices — emotions disabled (will use neutral fallback)")
        self._emotion_analyzer = None

    def _ensure_yolo_model(self):
        """Auto-download YOLO model if not found at configured path."""
        import os
        model_path = settings.yolo_model_path
        if os.path.exists(model_path):
            return model_path
        # If path doesn't exist, use just the filename so ultralytics auto-downloads
        basename = os.path.basename(model_path)
        logger.info("YOLO model not found at configured path, will auto-download", path=model_path, fallback=basename)
        # Try to save to configured directory if it exists
        model_dir = os.path.dirname(model_path)
        if model_dir and os.path.isdir(model_dir):
            from ultralytics import YOLO
            model = YOLO(basename)
            return basename
        return basename

    def load_models(self):
        if self._loaded:
            return
        logger.info("Loading models...")

        # Ensure YOLO model exists (auto-download if needed)
        try:
            yolo_path = self._ensure_yolo_model()
            self._detector.model_path = yolo_path
        except Exception as e:
            logger.warning("YOLO model download failed", error=str(e))

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

        # HSEmotion: try CUDA → CPU → disabled
        self._load_hsemotion()

        self._loaded = True

        import torch
        device = "CUDA" if torch.cuda.is_available() else "CPU"
        logger.info(
            "All models loaded",
            device=device,
            detector=self._detector is not None,
            recognizer=self._recognizer is not None,
            emotion_analyzer=self._emotion_analyzer is not None,
        )
        if torch.cuda.is_available():
            try:
                allocated = torch.cuda.memory_allocated() / 1024**3
                reserved = torch.cuda.memory_reserved() / 1024**3
                logger.info("VRAM usage", allocated_gb=f"{allocated:.2f}", reserved_gb=f"{reserved:.2f}")
            except Exception:
                pass

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
                except Exception as e:
                    logger.debug("Emotion analysis failed for face", error=str(e))
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
