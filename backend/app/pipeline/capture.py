import os
import queue
import threading
import time

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()

# Force TCP transport for RTSP; tls_verify=0 for rtsps:// with self-signed certs (Ubiquiti)
os.environ.setdefault(
    "OPENCV_FFMPEG_CAPTURE_OPTIONS",
    "rtsp_transport;tcp|tls_verify;0|allowed_media_types;video",
)


class RTSPCapture:
    """Threaded RTSP frame capture with auto-reconnection."""

    def __init__(self, camera_id: str, rtsp_url: str, fps_target: int = 5):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.fps_target = fps_target
        self.frame_interval = 1.0 / fps_target

        self._queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=2)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._is_connected = False
        self._current_fps = 0.0
        self._last_frame_time = 0.0

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def current_fps(self) -> float:
        return self._current_fps

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("RTSP capture started", camera_id=self.camera_id)

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("RTSP capture stopped", camera_id=self.camera_id)

    def get_frame(self) -> np.ndarray | None:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def _capture_loop(self):
        backoff = 1.0
        max_backoff = 30.0

        while not self._stop_event.is_set():
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                logger.warning(
                    "Failed to open RTSP stream, retrying...",
                    camera_id=self.camera_id, backoff=backoff,
                )
                self._is_connected = False
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
                continue

            self._is_connected = True
            backoff = 1.0
            logger.info("RTSP stream connected", camera_id=self.camera_id)

            frame_count = 0
            fps_start_time = time.monotonic()

            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Frame read failed", camera_id=self.camera_id)
                    self._is_connected = False
                    break

                now = time.monotonic()

                # Rate limit to target FPS
                if now - self._last_frame_time < self.frame_interval:
                    continue

                self._last_frame_time = now
                frame_count += 1

                # Calculate FPS every second
                elapsed = now - fps_start_time
                if elapsed >= 1.0:
                    self._current_fps = frame_count / elapsed
                    frame_count = 0
                    fps_start_time = now

                # Drop oldest frame if queue is full
                if self._queue.full():
                    try:
                        self._queue.get_nowait()
                    except queue.Empty:
                        pass

                self._queue.put(frame)

            cap.release()

            if not self._stop_event.is_set():
                logger.info("Reconnecting RTSP...", camera_id=self.camera_id, backoff=backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
