"""Pure chunking module. Must not import SQLAlchemy, Qdrant, OpenAI, or FastAPI."""

from dataclasses import dataclass
import hashlib
import uuid
from uuid import UUID

APP_NAMESPACE = uuid.UUID("7a3f1d2e-4b5c-6789-abcd-ef0123456789")


@dataclass(frozen=True)
class ChunkRecord:
    id: UUID
    document_id: UUID
    source: str
    page: int
    chunk_index: int
    char_start: int
    char_end: int
    text: str
    text_hash: str
    embedding_model: str


def make_point_id(
    document_id: UUID, page: int, chunk_index: int, char_start: int, char_end: int
) -> UUID:
    return uuid.uuid5(
        APP_NAMESPACE, f"{document_id}:{page}:{chunk_index}:{char_start}:{char_end}"
    )


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def chunk_pages(
    *,
    document_id: UUID,
    source: str,
    pages: list[tuple[int, str]],
    chunk_size: int,
    chunk_overlap: int,
    embedding_model: str,
) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    step = chunk_size - chunk_overlap
    for page, text in pages:
        if not text:
            continue
        start = 0
        chunk_index = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append(
                ChunkRecord(
                    id=make_point_id(document_id, page, chunk_index, start, end),
                    document_id=document_id,
                    source=source,
                    page=page,
                    chunk_index=chunk_index,
                    char_start=start,
                    char_end=end,
                    text=chunk_text,
                    text_hash=text_hash(chunk_text),
                    embedding_model=embedding_model,
                )
            )
            if end == len(text):
                break
            start += step
            chunk_index += 1
    return chunks
