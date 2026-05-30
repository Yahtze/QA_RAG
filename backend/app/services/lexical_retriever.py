from uuid import UUID

from sqlalchemy import bindparam, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk, DocumentStatus
from app.services.hybrid_retrieval import RankedChunkHit


class LexicalRetriever:
    def __init__(self, session: AsyncSession):
        self.session = session

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

        dialect = (
            self.session.bind.dialect.name if self.session.bind is not None else ""
        )
        if dialect == "postgresql":
            sql = text(
                """
                SELECT dc.id,
                       ts_rank_cd(
                           to_tsvector('english', dc.text),
                           plainto_tsquery('english', :query)
                       ) AS rank_score
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE d.user_id = :user_id
                  AND d.id = ANY(:document_ids)
                  AND d.status = 'ready'
                  AND to_tsvector('english', dc.text) @@ plainto_tsquery('english', :query)
                ORDER BY rank_score DESC, dc.id
                LIMIT :top_k
                """
            ).bindparams(bindparam("document_ids"))
            rows = (
                await self.session.execute(
                    sql,
                    {
                        "user_id": user_id,
                        "document_ids": document_ids,
                        "query": query,
                        "top_k": top_k,
                    },
                )
            ).all()
        else:
            pattern = f"%{query.strip().lower()}%"
            rows = (
                await self.session.execute(
                    select(DocumentChunk.id, DocumentChunk.text)
                    .join(Document)
                    .where(
                        Document.user_id == user_id,
                        Document.id.in_(document_ids),
                        Document.status == DocumentStatus.READY.value,
                        DocumentChunk.text.ilike(pattern),
                    )
                    .limit(top_k)
                )
            ).all()
            rows = [(row[0], 1.0) for row in rows]

        return [
            RankedChunkHit(chunk_id=row[0], rank=i, score=float(row[1] or 0.0))
            for i, row in enumerate(rows, start=1)
        ]
