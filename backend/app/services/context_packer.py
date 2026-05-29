from dataclasses import dataclass

from app.services.retrieval_types import RetrievalResult, RetrievedChunk


@dataclass(frozen=True)
class PackedContext:
    chunks: list[RetrievedChunk]
    context_text: str


def _block(chunk: RetrievedChunk, label: str) -> str:
    page = f" p.{chunk.page}" if chunk.page is not None else ""
    return f"[{label}] {chunk.filename}{page}\n{chunk.text.strip()}"


def pack_context(result: RetrievalResult, *, final_top_k: int, max_chars: int) -> PackedContext:
    selected: list[RetrievedChunk] = []
    blocks: list[str] = []
    used = 0

    for idx, chunk in enumerate(result.chunks[:final_top_k], start=1):
        label = str(idx)
        candidate = _block(chunk, label)
        extra = len(candidate) + (2 if blocks else 0)
        if blocks and used + extra >= max_chars:
            break
        if not blocks and extra > max_chars:
            candidate = candidate[:max_chars]
            extra = len(candidate)
        chunk.citation_label = label
        selected.append(chunk)
        blocks.append(candidate)
        used += extra

    return PackedContext(chunks=selected, context_text="\n\n".join(blocks))
