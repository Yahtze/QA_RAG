from uuid import UUID

from app.models import Citation
from app.services.retrieval_types import RetrievedChunk


def snippet(text: str, limit: int = 320) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def citations_event_map(chunks: list[RetrievedChunk]) -> dict[str, dict[str, object]]:
    return {
        chunk.citation_label: {
            "chunk_id": str(chunk.chunk_id),
            "doc_id": str(chunk.document_id),
            "filename": chunk.filename,
            "page": chunk.page,
            "snippet": snippet(chunk.text),
        }
        for chunk in chunks
    }


def citation_rows(*, message_id: UUID, chunks: list[RetrievedChunk]) -> list[Citation]:
    return [
        Citation(
            message_id=message_id,
            document_id=chunk.document_id,
            chunk_id=chunk.chunk_id,
            label=chunk.citation_label,
            filename=chunk.filename,
            chunk_text=chunk.text,
            snippet=snippet(chunk.text),
            page_number=chunk.page,
            score=max(0.0, min(1.0, chunk.fused_score or 0.0)),
            lexical_rank=chunk.lexical_rank,
            semantic_rank=chunk.semantic_rank,
            fused_rank=chunk.fused_rank,
            fused_score=chunk.fused_score,
        )
        for chunk in chunks
    ]
