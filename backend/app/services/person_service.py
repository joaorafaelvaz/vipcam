import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emotion_record import EmotionRecord
from app.models.face_embedding import FaceEmbedding
from app.models.person import Person
from app.schemas.person import PersonCreate, PersonUpdate


async def list_persons(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    person_type: str | None = None,
) -> tuple[list[Person], int]:
    query = select(Person).order_by(Person.last_seen_at.desc())
    count_query = select(func.count(Person.id))

    if search:
        query = query.where(Person.display_name.ilike(f"%{search}%"))
        count_query = count_query.where(Person.display_name.ilike(f"%{search}%"))

    if person_type:
        query = query.where(Person.person_type == person_type)
        count_query = count_query.where(Person.person_type == person_type)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.limit(limit).offset(offset))
    return list(result.scalars().all()), total


async def get_person(db: AsyncSession, person_id: uuid.UUID) -> Person | None:
    result = await db.execute(select(Person).where(Person.id == person_id))
    return result.scalar_one_or_none()


async def create_person(db: AsyncSession, data: PersonCreate) -> Person:
    person = Person(**data.model_dump())
    db.add(person)
    await db.flush()
    await db.refresh(person)
    return person


async def update_person(db: AsyncSession, person_id: uuid.UUID, data: PersonUpdate) -> Person | None:
    values = data.model_dump(exclude_unset=True)
    if not values:
        return await get_person(db, person_id)
    await db.execute(update(Person).where(Person.id == person_id).values(**values))
    await db.flush()
    return await get_person(db, person_id)


async def delete_person(db: AsyncSession, person_id: uuid.UUID) -> bool:
    person = await get_person(db, person_id)
    if not person:
        return False
    await db.delete(person)
    await db.flush()
    return True


async def merge_persons(
    db: AsyncSession, source_id: uuid.UUID, target_id: uuid.UUID
) -> Person | None:
    source = await get_person(db, source_id)
    target = await get_person(db, target_id)
    if not source or not target:
        return None

    # Move embeddings to target
    await db.execute(
        update(FaceEmbedding)
        .where(FaceEmbedding.person_id == source_id)
        .values(person_id=target_id)
    )
    # Move emotion records to target
    await db.execute(
        update(EmotionRecord)
        .where(EmotionRecord.person_id == source_id)
        .values(person_id=target_id)
    )

    # Update target stats
    target.total_visits += source.total_visits
    if source.first_seen_at < target.first_seen_at:
        target.first_seen_at = source.first_seen_at
    if source.last_seen_at > target.last_seen_at:
        target.last_seen_at = source.last_seen_at

    await db.delete(source)
    await db.flush()
    await db.refresh(target)
    return target
