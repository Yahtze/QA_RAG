from uuid import UUID

from app.services.chunking import ChunkRecord
from app.services.vector_store import build_payload


def _chunk():
    return ChunkRecord(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        document_id=UUID("11111111-1111-1111-1111-111111111111"),
        source="report.pdf",
        page=7,
        chunk_index=2,
        char_start=10,
        char_end=20,
        text="hello",
        text_hash="abc123abc123abcd",
        embedding_model="model-a",
    )


def test_build_payload_contract_uses_string_uuids():
    payload = build_payload(user_id=UUID("33333333-3333-3333-3333-333333333333"), chunk=_chunk())
    assert payload == {
        "user_id": "33333333-3333-3333-3333-333333333333",
        "document_id": "11111111-1111-1111-1111-111111111111",
        "source": "report.pdf",
        "page": 7,
        "chunk_index": 2,
        "char_start": 10,
        "char_end": 20,
        "text": "hello",
        "text_hash": "abc123abc123abcd",
        "embedding_model": "model-a",
    }
