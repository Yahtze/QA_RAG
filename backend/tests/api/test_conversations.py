import pytest


@pytest.mark.asyncio
async def test_conversation_flow(async_client, auth_headers, monkeypatch):
    async def _embed(self, texts):
        return [[0.1] * self.dimension for _ in texts]

    async def _noop(self, *args, **kwargs):
        return None

    monkeypatch.setattr("app.services.embeddings.OpenAIEmbeddingProvider.embed_texts", _embed)
    monkeypatch.setattr("app.services.vector_store.QdrantVectorStore.ensure_collection", _noop)
    monkeypatch.setattr("app.services.vector_store.QdrantVectorStore.delete_document_points", _noop)
    monkeypatch.setattr("app.services.vector_store.QdrantVectorStore.upsert_chunks", _noop)

    files = {"file": ("doc.txt", b"hello world", "text/plain")}
    up = await async_client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
    doc_id = up.json()["id"]

    conv = await async_client.post(
        "/api/v1/conversations", json={"document_id": doc_id}, headers=auth_headers
    )
    assert conv.status_code == 201
    conv_id = conv.json()["id"]

    msg = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "hello"},
        headers=auth_headers,
    )
    assert msg.status_code == 200
    assert msg.json()["assistant_message"]["content"].startswith("This is a placeholder")

    history = await async_client.get(
        f"/api/v1/conversations/{conv_id}/messages", headers=auth_headers
    )
    assert history.status_code == 200
    assert len(history.json()["items"]) == 2
