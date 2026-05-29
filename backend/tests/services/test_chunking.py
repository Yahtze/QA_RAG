from uuid import UUID

from app.services.chunking import APP_NAMESPACE, chunk_pages, make_point_id


def test_chunk_pages_uses_offsets_overlap_and_hash():
    document_id = UUID("11111111-1111-1111-1111-111111111111")
    chunks = chunk_pages(
        document_id=document_id,
        source="report.pdf",
        pages=[(7, "abcdefghij")],
        chunk_size=4,
        chunk_overlap=1,
        embedding_model="model-a",
    )
    assert [(c.page, c.chunk_index, c.char_start, c.char_end, c.text) for c in chunks] == [
        (7, 0, 0, 4, "abcd"),
        (7, 1, 3, 7, "defg"),
        (7, 2, 6, 10, "ghij"),
    ]
    assert all(len(c.text_hash) == 16 for c in chunks)
    assert chunks[0].id == make_point_id(document_id, 7, 0, 0, 4)


def test_chunk_pages_never_crosses_page_boundary():
    document_id = UUID("11111111-1111-1111-1111-111111111111")
    chunks = chunk_pages(
        document_id=document_id,
        source="x.pdf",
        pages=[(1, "abc"), (2, "def")],
        chunk_size=10,
        chunk_overlap=2,
        embedding_model="m",
    )
    assert [(c.page, c.text) for c in chunks] == [(1, "abc"), (2, "def")]


def test_point_id_namespace_is_committed():
    assert APP_NAMESPACE == UUID("7a3f1d2e-4b5c-6789-abcd-ef0123456789")
    assert make_point_id(UUID("11111111-1111-1111-1111-111111111111"), 1, 0, 0, 3) == make_point_id(
        UUID("11111111-1111-1111-1111-111111111111"), 1, 0, 0, 3
    )
