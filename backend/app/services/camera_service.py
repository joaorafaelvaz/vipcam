import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate


async def list_cameras(db: AsyncSession, active_only: bool = False) -> list[Camera]:
    query = select(Camera).order_by(Camera.name)
    if active_only:
        query = query.where(Camera.is_active == True)  # noqa: E712
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_camera(db: AsyncSession, camera_id: uuid.UUID) -> Camera | None:
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    return result.scalar_one_or_none()


async def create_camera(db: AsyncSession, data: CameraCreate) -> Camera:
    camera = Camera(**data.model_dump())
    db.add(camera)
    await db.flush()
    await db.refresh(camera)
    return camera


async def update_camera(db: AsyncSession, camera_id: uuid.UUID, data: CameraUpdate) -> Camera | None:
    values = data.model_dump(exclude_unset=True)
    if not values:
        return await get_camera(db, camera_id)
    await db.execute(update(Camera).where(Camera.id == camera_id).values(**values))
    await db.flush()
    return await get_camera(db, camera_id)


async def delete_camera(db: AsyncSession, camera_id: uuid.UUID) -> bool:
    camera = await get_camera(db, camera_id)
    if not camera:
        return False
    await db.execute(
        update(Camera).where(Camera.id == camera_id).values(is_active=False)
    )
    await db.flush()
    return True
