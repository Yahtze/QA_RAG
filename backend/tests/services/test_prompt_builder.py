from uuid import uuid4

from app.services.citation_mapper import citation_rows, citations_event_map
from app.services.context_packer import pack_context
from app.services.prompt_builder import build_grounded_messages
from app.services.retrieval_types import RetrievalResult, RetrievedChunk


def chunk(text: str, rank: int = 1) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="guide.pdf",
        page=3,
        text=text,
        lexical_rank=rank,
        semantic_rank=None,
        fused_rank=rank,
        fused_score=1 / (60 + rank),
        citation_label="",
    )


def test_pack_context_assigns_labels_and_budget():
    result = RetrievalResult(
        chunks=[chunk("A" * 20, 1), chunk("B" * 20, 2)],
        no_context_reason=None,
    )
    packed = pack_context(result, final_top_k=8, max_chars=80)
    assert [c.citation_label for c in packed.chunks] == ["1", "2"]
    assert "[1] guide.pdf p.3" in packed.context_text
    assert len(packed.context_text) <= 80


def test_prompt_contains_strict_grounding_rules():
    packed = pack_context(
        RetrievalResult(
            chunks=[chunk("Refunds take five days.")], no_context_reason=None
        ),
        final_top_k=8,
        max_chars=12000,
    )
    messages = build_grounded_messages(
        question="When are refunds paid?",
        context_text=packed.context_text,
    )
    system = messages[0]["content"]
    assert "ONLY the context chunks" in system
    assert "Never use knowledge outside" in system
    assert (
        "I don't have enough information in the provided documents to answer this."
        in system
    )
    assert messages[1] == {"role": "user", "content": "When are refunds paid?"}


def test_citation_mapper_uses_retrieval_metadata():
    retrieved = chunk("Refunds take five days.")
    retrieved.citation_label = "1"
    event_map = citations_event_map([retrieved])
    assert event_map["1"]["filename"] == "guide.pdf"
    assert event_map["1"]["snippet"] == "Refunds take five days."
    rows = citation_rows(message_id=uuid4(), chunks=[retrieved])
    assert rows[0].label == "1"
    assert rows[0].filename == "guide.pdf"
