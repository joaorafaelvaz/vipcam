import asyncio
import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import structlog
from sqlalchemy import text, update

from app.config import settings
from app.db.session import async_session
from app.models.camera_event import CameraEvent
from app.models.emotion_record import EmotionRecord
from app.models.person import Person
from app.pipeline.capture import RTSPCapture
from app.pipeline.face_matcher import FaceMatcher
from app.pipeline.gpu_worker import FrameResult, GPUWorker
from app.pipeline.smoother import EmotionSmoother
from app.services.redis_service import redis_service

logger = structlog.get_logger()


class PipelineManager:
    """Central orchestrator: captures → GPU → matching → persistence → WebSocket."""

    def __init__(self):
        self._captures: dict[str, RTSPCapture] = {}
        self._gpu_worker = GPUWorker()
        self._face_matcher = FaceMatcher()
        self._smoother = EmotionSmoother()
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        if self._running:
            return

        # Load GPU models in thread pool (blocking)
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(self._executor, self._gpu_worker.load_models)
        except Exception as e:
            logger.error("GPU model loading failed", error=str(e))
            raise

        # Load cameras from DB
        async with async_session() as db:
            result = await db.execute(
                text("SELECT id, name, rtsp_url, fps_target FROM cameras WHERE is_active = true")
            )
            cameras = result.fetchall()

        for cam in cameras:
            self._add_capture(str(cam.id), cam.rtsp_url, cam.fps_target)

        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Pipeline manager started", cameras=len(self._captures))

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        for capture in self._captures.values():
            capture.stop()
        self._captures.clear()
        self._executor.shutdown(wait=False)
        logger.info("Pipeline manager stopped")

    def _add_capture(self, camera_id: str, rtsp_url: str, fps_target: int):
        capture = RTSPCapture(camera_id, rtsp_url, fps_target)
        capture.start()
        self._captures[camera_id] = capture

    async def _process_loop(self):
        loop = asyncio.get_event_loop()

        while self._running:
            processed_any = False

            for camera_id, capture in list(self._captures.items()):
                frame = capture.get_frame()
                if frame is None:
                    continue

                processed_any = True

                try:
                    # Store latest frame as JPEG snapshot in Redis (for /cameras/{id}/snapshot)
                    await self._cache_snapshot(camera_id, frame)

                    # Run GPU inference in thread pool (single thread = serial GPU access)
                    frame_result: FrameResult = await loop.run_in_executor(
                        self._executor,
                        self._gpu_worker.process_frame,
                        camera_id,
                        frame,
                    )

                    # Run face matching and persistence asynchronously
                    await self._process_result(frame_result, frame)

                except Exception as e:
                    logger.error("Pipeline processing error", camera_id=camera_id, error=str(e))

            if not processed_any:
                await asyncio.sleep(0.05)  # 50ms idle sleep

    async def _process_result(self, result: FrameResult, frame: np.ndarray):
        now = datetime.now(timezone.utc)

        async with async_session() as db:
            # Match faces and persist
            for face_result in result.faces:
                embedding = face_result.face_data.embedding
                quality = face_result.face_data.det_score

                if quality < settings.face_quality_min:
                    continue

                # Match against database
                match = await self._face_matcher.match(db, embedding)
                face_result.person_id = str(match.person_id) if match.person_id else None
                face_result.similarity = match.similarity
                face_result.is_new = match.is_new

                person_id = match.person_id

                if match.is_new:
                    # Create new person
                    person = Person(
                        first_seen_at=now,
                        last_seen_at=now,
                        estimated_age=face_result.face_data.age,
                        estimated_gender=face_result.face_data.gender,
                    )
                    db.add(person)
                    await db.flush()
                    person_id = person.id
                    face_result.person_id = str(person_id)

                    # Save face crop and set thumbnail for new person
                    crop_path = self._save_face_crop(frame, face_result.face_data.bbox, person_id)
                    if crop_path:
                        person.thumbnail_path = crop_path

                    # Register embedding with bbox and crop path
                    await self._face_matcher.register_embedding(
                        db, person_id, embedding, quality,
                        camera_id=uuid.UUID(result.camera_id),
                        face_bbox=face_result.face_data.bbox,
                        image_path=crop_path,
                    )
                else:
                    # Update last seen
                    await db.execute(
                        update(Person)
                        .where(Person.id == person_id)
                        .values(last_seen_at=now)
                    )

                    # Update thumbnail if current quality is better (every ~50 frames)
                    if quality > 0.85 and time.monotonic() % 50 < 1:
                        crop_path = self._save_face_crop(frame, face_result.face_data.bbox, person_id)
                        if crop_path:
                            await db.execute(
                                update(Person)
                                .where(Person.id == person_id)
                                .values(thumbnail_path=crop_path)
                            )

                # Smooth emotions
                smoothed, shifted = self._smoother.smooth(
                    str(person_id), face_result.emotions
                )
                face_result.emotions = smoothed

                # Persist emotion record
                emotion_record = EmotionRecord(
                    person_id=person_id,
                    camera_id=uuid.UUID(result.camera_id),
                    anger=smoothed.anger,
                    contempt=smoothed.contempt,
                    disgust=smoothed.disgust,
                    fear=smoothed.fear,
                    happiness=smoothed.happiness,
                    neutral=smoothed.neutral,
                    sadness=smoothed.sadness,
                    surprise=smoothed.surprise,
                    dominant_emotion=smoothed.dominant_emotion,
                    valence=smoothed.valence,
                    arousal=smoothed.arousal,
                    satisfaction_score=smoothed.satisfaction_score,
                    face_confidence=quality,
                    captured_at=now,
                )
                db.add(emotion_record)

            # Persist camera event
            event = CameraEvent(
                camera_id=uuid.UUID(result.camera_id),
                event_type="occupancy_update",
                person_count=result.person_count,
                avg_satisfaction=self._avg_satisfaction(result),
                captured_at=now,
            )
            db.add(event)
            await db.commit()

        # Publish to Redis for WebSocket
        await self._publish_result(result)

    def _save_face_crop(
        self, frame: np.ndarray, bbox: list[float], person_id: uuid.UUID
    ) -> str | None:
        """Crop face from frame, save to disk, return relative path."""
        try:
            h, w = frame.shape[:2]
            x1, y1, x2, y2 = [int(v) for v in bbox]

            # Add 30% padding around the face for a nicer crop
            pad_w = int((x2 - x1) * 0.3)
            pad_h = int((y2 - y1) * 0.3)
            x1 = max(0, x1 - pad_w)
            y1 = max(0, y1 - pad_h)
            x2 = min(w, x2 + pad_w)
            y2 = min(h, y2 + pad_h)

            face_crop = frame[y1:y2, x1:x2]
            if face_crop.size == 0:
                return None

            # Resize to standard thumbnail size (200x200)
            face_crop = cv2.resize(face_crop, (200, 200), interpolation=cv2.INTER_AREA)

            # Save with person_id-based path: /data/face_crops/<first2>/<person_id>.jpg
            pid_str = str(person_id)
            subdir = pid_str[:2]
            crop_dir = Path(settings.face_crop_dir) / subdir
            crop_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{pid_str}.jpg"
            filepath = crop_dir / filename
            cv2.imwrite(str(filepath), face_crop, [cv2.IMWRITE_JPEG_QUALITY, 90])

            # Return relative path from face_crop_dir root
            return f"{subdir}/{filename}"
        except Exception as e:
            logger.debug("Failed to save face crop", person_id=str(person_id), error=str(e))
            return None

    async def _cache_snapshot(self, camera_id: str, frame: np.ndarray):
        try:
            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            await redis_service.set_snapshot(camera_id, jpeg.tobytes(), ttl=10)
        except Exception as e:
            logger.debug("Failed to cache snapshot", camera_id=camera_id, error=str(e))

    def _avg_satisfaction(self, result: FrameResult) -> float | None:
        scores = [f.emotions.satisfaction_score for f in result.faces if f.emotions]
        return sum(scores) / len(scores) if scores else None

    async def _publish_result(self, result: FrameResult):
        message = {
            "type": "analysis_update",
            "camera_id": result.camera_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "person_count": result.person_count,
            "faces_detected": len(result.faces),
            "persons": [
                {
                    "person_id": f.person_id,
                    "dominant_emotion": f.emotions.dominant_emotion,
                    "satisfaction_score": f.emotions.satisfaction_score,
                    "valence": f.emotions.valence,
                    "emotions": f.emotions.to_dict(),
                    "bbox": f.bbox,
                    "age": f.face_data.age,
                    "gender": f.face_data.gender,
                    "is_new": f.is_new,
                }
                for f in result.faces
            ],
            "processing_time_ms": result.processing_time_ms,
        }

        try:
            await redis_service.publish(
                f"vipcam:frames:{result.camera_id}", message
            )
        except Exception as e:
            logger.error("Redis publish error", error=str(e))


pipeline_manager = PipelineManager()
