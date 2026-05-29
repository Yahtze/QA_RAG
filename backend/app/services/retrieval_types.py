from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class NoContextReason(StrEnum):
    NO_ACTIVE_DOCUMENTS = "no_active_documents"
    ACTIVE_DOCUMENTS_NOT_READY = "active_documents_not_ready"
    NO_MATCHING_CHUNKS = "no_matching_chunks"
    RETRIEVAL_UNAVAILABLE = "retrieval_unavailable"


@dataclass
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    filename: str
    page: int | None
    text: str
    lexical_rank: int | None
    semantic_rank: int | None
    fused_rank: int
    fused_score: float | None
    citation_label: str = ""


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    no_context_reason: NoContextReason | None = None
