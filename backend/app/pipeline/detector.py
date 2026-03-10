from dataclasses import dataclass

import numpy as np
import structlog

logger = structlog.get_logger()


@dataclass
class Detection:
    bbox: list[float]  # [x1, y1, x2, y2]
    confidence: float
    track_id: int | None = None


class PersonDetector:
    """YOLOv8x wrapper for person detection."""

    def __init__(self, model_path: str = "yolov8x.pt", imgsz: int = 1280, conf: float = 0.5):
        self.model_path = model_path
        self.imgsz = imgsz
        self.conf = conf
        self._model = None

    def load(self):
        from ultralytics import YOLO

        logger.info("Loading YOLOv8x model...", path=self.model_path)
        self._model = YOLO(self.model_path)
        self._model.to("cuda:0")
        self._model.fuse()
        logger.info("YOLOv8x loaded successfully")

    def detect(self, frame: np.ndarray) -> list[Detection]:
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        results = self._model.predict(
            source=frame,
            classes=[0],  # person only
            conf=self.conf,
            iou=0.45,
            imgsz=self.imgsz,
            half=True,  # FP16
            verbose=False,
            device="cuda:0",
        )

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for i in range(len(boxes)):
                bbox = boxes.xyxy[i].cpu().numpy().tolist()
                confidence = float(boxes.conf[i].cpu().numpy())
                track_id = int(boxes.id[i].cpu().numpy()) if boxes.id is not None else None
                detections.append(Detection(bbox=bbox, confidence=confidence, track_id=track_id))

        return detections

    def detect_with_tracking(self, frame: np.ndarray) -> list[Detection]:
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        results = self._model.track(
            source=frame,
            classes=[0],
            conf=self.conf,
            iou=0.45,
            imgsz=self.imgsz,
            half=True,
            verbose=False,
            device="cuda:0",
            persist=True,
            tracker="bytetrack.yaml",
        )

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for i in range(len(boxes)):
                bbox = boxes.xyxy[i].cpu().numpy().tolist()
                confidence = float(boxes.conf[i].cpu().numpy())
                track_id = int(boxes.id[i].cpu().numpy()) if boxes.id is not None else None
                detections.append(Detection(bbox=bbox, confidence=confidence, track_id=track_id))

        return detections
