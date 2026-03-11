import asyncio
import uuid

import cv2
import structlog
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.camera import CameraCreate, CameraRead, CameraUpdate
from app.services import camera_service
from app.services.redis_service import redis_service

logger = structlog.get_logger()
router = APIRouter()


import os
os.environ.setdefault("OPENCV_FFMPEG_READ_ATTEMPTS", "4096")


def _grab_frame(rtsp_url: str, timeout_ms: int = 10000) -> bytes:
    """Grab a single JPEG frame from an RTSP URL (runs in thread)."""
    # Force TCP transport and set stimeout (microseconds) for RTSP via FFMPEG options
    url_with_opts = rtsp_url
    sep = "&" if "?" in rtsp_url else "?"
    if "rtsp_transport" not in rtsp_url:
        url_with_opts += f"{sep}rtsp_transport=tcp"
        sep = "&"
    if "stimeout" not in rtsp_url:
        url_with_opts += f"{sep}stimeout={timeout_ms * 1000}"

    cap = cv2.VideoCapture(url_with_opts, cv2.CAP_FFMPEG)
    try:
        if not cap.isOpened():
            raise ConnectionError(f"Cannot open RTSP stream: {rtsp_url}")
        ret, frame = cap.read()
        if not ret or frame is None:
            raise ConnectionError("Failed to read frame from stream")
        _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return jpeg.tobytes()
    finally:
        cap.release()


@router.get("", response_model=list[CameraRead])
async def list_cameras(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    return await camera_service.list_cameras(db, active_only=active_only)


@router.post("", response_model=CameraRead, status_code=201)
async def create_camera(
    data: CameraCreate,
    db: AsyncSession = Depends(get_db),
):
    return await camera_service.create_camera(db, data)


@router.get("/{camera_id}", response_model=CameraRead)
async def get_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    camera = await camera_service.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.patch("/{camera_id}", response_model=CameraRead)
async def update_camera(
    camera_id: uuid.UUID,
    data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
):
    camera = await camera_service.update_camera(db, camera_id, data)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.delete("/{camera_id}", status_code=204)
async def delete_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    deleted = await camera_service.delete_camera(db, camera_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Camera not found")


@router.get("/{camera_id}/snapshot")
async def get_snapshot(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    # First try Redis cache (from pipeline)
    jpeg_bytes = await redis_service.get_snapshot(str(camera_id))
    if jpeg_bytes:
        return Response(content=jpeg_bytes, media_type="image/jpeg")

    # Fallback: grab a live frame directly from RTSP
    camera = await camera_service.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    try:
        loop = asyncio.get_event_loop()
        jpeg_bytes = await loop.run_in_executor(None, _grab_frame, camera.rtsp_url)
        # Cache it in Redis for 10s so repeated requests don't hammer the camera
        await redis_service.set_snapshot(str(camera_id), jpeg_bytes, ttl=10)
        return Response(content=jpeg_bytes, media_type="image/jpeg")
    except Exception as e:
        logger.warning("Snapshot grab failed", camera_id=str(camera_id), error=str(e))
        raise HTTPException(status_code=502, detail=f"Could not grab frame: {e}")


@router.post("/{camera_id}/test")
async def test_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Test RTSP connection and return status + snapshot."""
    camera = await camera_service.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    try:
        loop = asyncio.get_event_loop()
        jpeg_bytes = await loop.run_in_executor(None, _grab_frame, camera.rtsp_url)
        await redis_service.set_snapshot(str(camera_id), jpeg_bytes, ttl=30)
        return {
            "status": "ok",
            "message": f"Conexao com {camera.name} bem-sucedida",
            "frame_size": len(jpeg_bytes),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Falha na conexao: {e}",
            "frame_size": 0,
        }
