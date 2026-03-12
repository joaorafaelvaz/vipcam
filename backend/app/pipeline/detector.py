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
        import torch
        from ultralytics import YOLO

        self._device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self._use_half = self._device != "cpu"

        logger.info("Loading YOLOv8x model...", path=self.model_path, device=self._device)
        self._model = YOLO(self.model_path)
        self._model.to(self._device)
        if self._device != "cpu":
            self._model.fuse()
        logger.info("YOLOv8x loaded successfully", device=self._device)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        results = self._model.predict(
            source=frame,
            classes=[0],  # person only
            conf=self.conf,
            iou=0.45,
            imgsz=self.imgsz,
            half=self._use_half,
            verbose=False,
            device=self._device,
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
            half=self._use_half,
            verbose=False,
            device=self._device,
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
