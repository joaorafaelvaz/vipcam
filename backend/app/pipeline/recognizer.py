from dataclasses import dataclass, field

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()


@dataclass
class FaceData:
    bbox: list[float]  # [x1, y1, x2, y2]
    embedding: np.ndarray  # 512-D normalized vector
    det_score: float
    age: int
    gender: str  # "M" or "F"
    landmarks: np.ndarray | None = None


class FaceRecognizer:
    """InsightFace buffalo_l wrapper for face detection and recognition."""

    def __init__(self, model_name: str = "buffalo_l", det_size: int = 640):
        self.model_name = model_name
        self.det_size = (det_size, det_size)
        self._app = None

    def load(self):
        import onnxruntime
        from insightface.app import FaceAnalysis

        available = onnxruntime.get_available_providers()
        if "CUDAExecutionProvider" in available:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            ctx_id = 0
        else:
            providers = ["CPUExecutionProvider"]
            ctx_id = -1

        logger.info("Loading InsightFace model...", model=self.model_name, providers=providers)
        self._app = FaceAnalysis(
            name=self.model_name,
            providers=providers,
        )
        self._app.prepare(ctx_id=ctx_id, det_size=self.det_size)
        logger.info("InsightFace loaded successfully", providers=providers)

    def analyze(self, frame: np.ndarray) -> list[FaceData]:
        if self._app is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        # InsightFace expects RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self._app.get(frame_rgb)

        results = []
        for face in faces:
            gender_str = "M" if face.gender == 1 else "F"
            results.append(
                FaceData(
                    bbox=face.bbox.tolist(),
                    embedding=face.normed_embedding,
                    det_score=float(face.det_score),
                    age=int(face.age),
                    gender=gender_str,
                    landmarks=face.kps if hasattr(face, "kps") else None,
                )
            )

        return results
