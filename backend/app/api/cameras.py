import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.camera import CameraCreate, CameraRead, CameraUpdate
from app.services import camera_service
from app.services.redis_service import redis_service

router = APIRouter()


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
async def get_snapshot(camera_id: uuid.UUID):
    jpeg_bytes = await redis_service.get_snapshot(str(camera_id))
    if not jpeg_bytes:
        raise HTTPException(status_code=404, detail="No snapshot available")
    return Response(content=jpeg_bytes, media_type="image/jpeg")
