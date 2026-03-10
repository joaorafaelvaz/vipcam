import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass

import numpy as np
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = structlog.get_logger()


@dataclass
class MatchResult:
    person_id: uuid.UUID | None
    similarity: float
    is_new: bool


class FaceMatcher:
    """Face matching against pgvector database with local LRU cache."""

    def __init__(self, threshold: float | None = None, max_embeddings: int | None = None):
        self.threshold = threshold or settings.face_match_threshold
        self.max_embeddings = max_embeddings or settings.face_max_embeddings_per_person
        self._cache: OrderedDict[str, tuple[np.ndarray, float]] = OrderedDict()
        self._cache_max_age = 60.0  # seconds

    def _check_cache(self, embedding: np.ndarray) -> tuple[str | None, float]:
        """Check local cache for a match. Returns (person_id, similarity) or (None, 0)."""
        now = time.monotonic()
        expired = [k for k, (_, ts) in self._cache.items() if now - ts > self._cache_max_age]
        for k in expired:
            del self._cache[k]

        best_id = None
        best_sim = 0.0

        for pid, (cached_emb, _) in self._cache.items():
            sim = float(np.dot(embedding, cached_emb))
            if sim > best_sim:
                best_sim = sim
                best_id = pid

        return best_id, best_sim

    def update_cache(self, person_id: str, embedding: np.ndarray):
        self._cache[person_id] = (embedding, time.monotonic())
        self._cache.move_to_end(person_id)
        if len(self._cache) > 500:
            self._cache.popitem(last=False)

    async def match(self, db: AsyncSession, embedding: np.ndarray) -> MatchResult:
        # Check local cache first
        cached_id, cached_sim = self._check_cache(embedding)
        if cached_id and cached_sim >= self.threshold:
            return MatchResult(
                person_id=uuid.UUID(cached_id),
                similarity=cached_sim,
                is_new=False,
            )

        # Query pgvector
        embedding_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
        result = await db.execute(
            text("""
                SELECT person_id,
                       1 - (embedding <=> :emb::vector) AS similarity
                FROM face_embeddings
                ORDER BY embedding <=> :emb::vector
                LIMIT 1
            """),
            {"emb": embedding_str},
        )
        row = result.first()

        if row and row.similarity >= self.threshold:
            pid = str(row.person_id)
            self.update_cache(pid, embedding)
            return MatchResult(
                person_id=row.person_id,
                similarity=float(row.similarity),
                is_new=False,
            )

        return MatchResult(person_id=None, similarity=float(row.similarity) if row else 0.0, is_new=True)

    async def register_embedding(
        self,
        db: AsyncSession,
        person_id: uuid.UUID,
        embedding: np.ndarray,
        quality: float,
        camera_id: uuid.UUID | None = None,
    ):
        """Store a new embedding, replacing lowest quality if at max."""
        embedding_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"

        # Count existing embeddings
        count_result = await db.execute(
            text("SELECT COUNT(*) FROM face_embeddings WHERE person_id = :pid"),
            {"pid": str(person_id)},
        )
        count = count_result.scalar() or 0

        if count >= self.max_embeddings:
            # Replace lowest quality
            await db.execute(
                text("""
                    DELETE FROM face_embeddings
                    WHERE id = (
                        SELECT id FROM face_embeddings
                        WHERE person_id = :pid
                        ORDER BY quality_score ASC NULLS FIRST
                        LIMIT 1
                    )
                """),
                {"pid": str(person_id)},
            )

        await db.execute(
            text("""
                INSERT INTO face_embeddings (person_id, embedding, quality_score, source_camera_id)
                VALUES (:pid, :emb::vector, :quality, :cam_id)
            """),
            {
                "pid": str(person_id),
                "emb": embedding_str,
                "quality": quality,
                "cam_id": str(camera_id) if camera_id else None,
            },
        )

        self.update_cache(str(person_id), embedding)
