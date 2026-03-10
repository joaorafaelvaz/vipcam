import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.emotion import EmotionRead
from app.schemas.person import PersonCreate, PersonMerge, PersonRead, PersonUpdate
from app.services import emotion_service, person_service

router = APIRouter()


@router.get("", response_model=list[PersonRead])
async def list_persons(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    person_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    persons, _ = await person_service.list_persons(
        db, limit=limit, offset=offset, search=search, person_type=person_type
    )
    return persons


@router.post("", response_model=PersonRead, status_code=201)
async def create_person(
    data: PersonCreate,
    db: AsyncSession = Depends(get_db),
):
    return await person_service.create_person(db, data)


@router.get("/{person_id}", response_model=PersonRead)
async def get_person(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    person = await person_service.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.patch("/{person_id}", response_model=PersonRead)
async def update_person(
    person_id: uuid.UUID,
    data: PersonUpdate,
    db: AsyncSession = Depends(get_db),
):
    person = await person_service.update_person(db, person_id, data)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.delete("/{person_id}", status_code=204)
async def delete_person(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    deleted = await person_service.delete_person(db, person_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Person not found")


@router.post("/merge", response_model=PersonRead)
async def merge_persons(
    data: PersonMerge,
    db: AsyncSession = Depends(get_db),
):
    result = await person_service.merge_persons(db, data.source_id, data.target_id)
    if not result:
        raise HTTPException(status_code=404, detail="One or both persons not found")
    return result


@router.get("/{person_id}/emotions", response_model=list[EmotionRead])
async def get_person_emotions(
    person_id: uuid.UUID,
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await emotion_service.get_recent_emotions(db, person_id=person_id, limit=limit)
