import asyncio
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

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
                    # Run GPU inference in thread pool (single thread = serial GPU access)
                    frame_result: FrameResult = await loop.run_in_executor(
                        self._executor,
                        self._gpu_worker.process_frame,
                        camera_id,
                        frame,
                    )

                    # Run face matching and persistence asynchronously
                    await self._process_result(frame_result)

                except Exception as e:
                    logger.error("Pipeline processing error", camera_id=camera_id, error=str(e))

            if not processed_any:
                await asyncio.sleep(0.05)  # 50ms idle sleep

    async def _process_result(self, result: FrameResult):
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

                    # Register embedding
                    await self._face_matcher.register_embedding(
                        db, person_id, embedding, quality,
                        camera_id=uuid.UUID(result.camera_id),
                    )
                else:
                    # Update last seen
                    await db.execute(
                        update(Person)
                        .where(Person.id == person_id)
                        .values(last_seen_at=now)
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
