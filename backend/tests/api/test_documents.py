import pytest

from app.models.document import DocumentStatus
from app.schemas.document import DeletedDocumentOut, DocumentAdminOut, DocumentOut


def test_document_out_has_ingestion_fields():
    fields = DocumentOut.model_fields
    assert fields["status"].annotation is DocumentStatus
    assert {"page_count", "chunk_count", "error_message", "updated_at"} <= set(fields)
    assert "storage_path" not in fields


def test_admin_out_extends_operational_fields_without_http_route():
    fields = DocumentAdminOut.model_fields
    assert {"qdrant_synced_at", "retention_note", "retry_count", "last_retry_at"} <= set(fields)


def test_deleted_document_out_shape():
    assert (
        DeletedDocumentOut(id="00000000-0000-0000-0000-000000000000", deleted=True).deleted is True
    )


@pytest.mark.asyncio
async def test_documents_upload_list_get_delete(async_client, auth_headers, monkeypatch):
    async def _noop(self, *args, **kwargs):
        return None

    monkeypatch.setattr("app.services.vector_store.QdrantVectorStore.ensure_collection", _noop)
    monkeypatch.setattr("app.services.vector_store.QdrantVectorStore.delete_document_points", _noop)
    monkeypatch.setattr("app.services.vector_store.QdrantVectorStore.upsert_chunks", _noop)

    files = {"file": ("doc.txt", b"hello", "text/plain")}
    up = await async_client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
    assert up.status_code == 201
    doc_id = up.json()["id"]

    lst = await async_client.get("/api/v1/documents", headers=auth_headers)
    assert lst.status_code == 200
    assert len(lst.json()["items"]) == 1

    getr = await async_client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert getr.status_code == 200

    dele = await async_client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert dele.status_code == 200
    assert dele.json() == {"id": doc_id, "deleted": True}
