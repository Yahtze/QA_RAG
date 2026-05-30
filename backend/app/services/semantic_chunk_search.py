from typing import Protocol
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from app.core.config import Settings
from app.services.embeddings import EmbeddingProvider
from app.services.hybrid_retrieval import RankedChunkHit


class SemanticSearchUnavailable(Exception): ...


class SemanticChunkSearch(Protocol):
    async def search(
        self,
        *,
        user_id: UUID,
        document_ids: list[UUID],
        query: str,
        top_k: int,
    ) -> list[RankedChunkHit]: ...


class QdrantSemanticChunkSearch:
    def __init__(self, *, settings: Settings, embeddings: EmbeddingProvider):
        self.settings = settings
        self.embeddings = embeddings
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL)

    async def search(
        self,
        *,
        user_id: UUID,
        document_ids: list[UUID],
        query: str,
        top_k: int,
    ) -> list[RankedChunkHit]:
        if not document_ids or not query.strip():
            return []
        try:
            vector = (await self.embeddings.embed_texts([query]))[0]
            flt = qm.Filter(
                must=[
                    qm.FieldCondition(
                        key="user_id", match=qm.MatchValue(value=str(user_id))
                    ),
                    qm.FieldCondition(
                        key="document_id",
                        match=qm.MatchAny(any=[str(x) for x in document_ids]),
                    ),
                ]
            )
            response = await self.client.query_points(
                collection_name=self.settings.QDRANT_COLLECTION_NAME,
                query=vector,
                query_filter=flt,
                limit=top_k,
            )
            return [
                RankedChunkHit(
                    chunk_id=UUID(str(point.id)), rank=i, score=float(point.score)
                )
                for i, point in enumerate(response.points, start=1)
            ]
        except Exception as exc:  # pragma: no cover
            raise SemanticSearchUnavailable(str(exc)) from exc
