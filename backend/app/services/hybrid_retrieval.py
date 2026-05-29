from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import Document, DocumentChunk, DocumentStatus
from app.services.conversation_scope import QueryableConversationScope
from app.services.retrieval_types import NoContextReason, RetrievalResult, RetrievedChunk


@dataclass(frozen=True)
class RankedChunkHit:
    chunk_id: UUID
    rank: int
    score: float | None = None


@dataclass(frozen=True)
class FusedHit:
    chunk_id: UUID
    lexical_rank: int | None
    semantic_rank: int | None
    fused_rank: int
    fused_score: float


def reciprocal_rank_fusion(
    *,
    lexical: list[RankedChunkHit],
    semantic: list[RankedChunkHit],
    final_top_k: int,
    k: int = 60,
) -> list[FusedHit]:
    scores: dict[UUID, float] = {}
    lexical_ranks: dict[UUID, int] = {}
    semantic_ranks: dict[UUID, int] = {}

    for hit in lexical:
        lexical_ranks[hit.chunk_id] = hit.rank
        scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + hit.rank)

    for hit in semantic:
        semantic_ranks[hit.chunk_id] = hit.rank
        scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + hit.rank)

    ordered = sorted(scores.items(), key=lambda item: (-item[1], str(item[0])))[:final_top_k]
    return [
        FusedHit(
            chunk_id=chunk_id,
            lexical_rank=lexical_ranks.get(chunk_id),
            semantic_rank=semantic_ranks.get(chunk_id),
            fused_rank=i,
            fused_score=score,
        )
        for i, (chunk_id, score) in enumerate(ordered, start=1)
    ]


class HybridRetriever:
    def __init__(self, session: AsyncSession, *, lexical, semantic):
        self.session = session
        self.lexical = lexical
        self.semantic = semantic

    async def retrieve(
        self,
        *,
        user_id: UUID,
        scope: QueryableConversationScope,
        query: str,
        settings: Settings,
    ) -> RetrievalResult:
        if not scope.active_document_ids:
            return RetrievalResult([], NoContextReason.NO_ACTIVE_DOCUMENTS)
        if not scope.ready_document_ids:
            return RetrievalResult([], NoContextReason.ACTIVE_DOCUMENTS_NOT_READY)

        lexical_hits = await self.lexical.search(
            user_id=user_id,
            document_ids=scope.ready_document_ids,
            query=query,
            top_k=settings.RETRIEVAL_BM25_TOP_K,
        )
        semantic_hits = await self.semantic.search(
            user_id=user_id,
            document_ids=scope.ready_document_ids,
            query=query,
            top_k=settings.RETRIEVAL_SEMANTIC_TOP_K,
        )
        fused = reciprocal_rank_fusion(
            lexical=lexical_hits,
            semantic=semantic_hits,
            final_top_k=settings.RETRIEVAL_FINAL_TOP_K,
        )
        if not fused:
            return RetrievalResult([], NoContextReason.NO_MATCHING_CHUNKS)

        fused_by_id = {hit.chunk_id: hit for hit in fused}
        rows = list(
            (
                await self.session.execute(
                    select(DocumentChunk, Document)
                    .join(Document, Document.id == DocumentChunk.document_id)
                    .where(
                        DocumentChunk.id.in_(fused_by_id.keys()),
                        Document.user_id == user_id,
                        Document.id.in_(scope.ready_document_ids),
                        Document.status == DocumentStatus.READY.value,
                    )
                )
            ).all()
        )

        hydrated: list[RetrievedChunk] = []
        for chunk, doc in rows:
            hit = fused_by_id[chunk.id]
            hydrated.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=doc.id,
                    filename=doc.filename,
                    page=chunk.page,
                    text=chunk.text,
                    lexical_rank=hit.lexical_rank,
                    semantic_rank=hit.semantic_rank,
                    fused_rank=hit.fused_rank,
                    fused_score=hit.fused_score,
                )
            )

        hydrated.sort(key=lambda c: c.fused_rank)
        return RetrievalResult(
            hydrated,
            None if hydrated else NoContextReason.NO_MATCHING_CHUNKS,
        )
