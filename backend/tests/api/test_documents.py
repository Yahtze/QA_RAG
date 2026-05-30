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

    from app.services.ingestion_queue import FakeIngestionQueue

    monkeypatch.setattr(
        "app.api.v1.documents.CeleryIngestionQueue",
        lambda settings: FakeIngestionQueue(),
    )

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


@pytest.mark.asyncio
async def test_upload_route_returns_pending_and_no_task_id(async_client, auth_headers, monkeypatch):
    from app.services.ingestion_queue import FakeIngestionQueue

    q = FakeIngestionQueue()
    monkeypatch.setattr("app.api.v1.documents.CeleryIngestionQueue", lambda settings: q)

    files = {"file": ("async.txt", b"hello", "text/plain")}
    r = await async_client.post("/api/v1/documents/upload", files=files, headers=auth_headers)

    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"
    assert "task_id" not in body
    assert [str(x) for x in q.enqueued] == [body["id"]]


@pytest.mark.asyncio
async def test_upload_route_maps_enqueue_failure_to_500(async_client, auth_headers, monkeypatch):
    from app.services.ingestion_queue import FakeIngestionQueue

    monkeypatch.setattr(
        "app.api.v1.documents.CeleryIngestionQueue", lambda settings: FakeIngestionQueue(fail=True)
    )

    files = {"file": ("async.txt", b"hello", "text/plain")}
    r = await async_client.post("/api/v1/documents/upload", files=files, headers=auth_headers)

    assert r.status_code == 500
    assert r.json()["detail"] == "Failed to enqueue ingestion task."


@pytest.mark.asyncio
async def test_upload_batch_mixed_valid_invalid_returns_207(async_client, auth_headers, monkeypatch):
    from app.services.ingestion_queue import FakeIngestionQueue

    monkeypatch.setattr("app.api.v1.documents.CeleryIngestionQueue", lambda settings: FakeIngestionQueue())

    files = [
        ("files", ("good-1.txt", b"hello", "text/plain")),
        ("files", ("bad-1.exe", b"abc", "application/x-msdownload")),
        ("files", ("good-2.md", b"# ok", "text/markdown")),
    ]

    r = await async_client.post("/api/v1/documents/upload-batch", files=files, headers=auth_headers)

    assert r.status_code == 207
    body = r.json()
    assert body["total"] == 3
    assert body["accepted"] == 2
    assert body["failed"] == 1
    assert [item["status"] for item in body["results"]] == ["accepted", "failed", "accepted"]


@pytest.mark.asyncio
async def test_upload_batch_all_valid_returns_207(async_client, auth_headers, monkeypatch):
    from app.services.ingestion_queue import FakeIngestionQueue

    monkeypatch.setattr("app.api.v1.documents.CeleryIngestionQueue", lambda settings: FakeIngestionQueue())

    files = [
        ("files", ("one.txt", b"hello", "text/plain")),
        ("files", ("two.md", b"# world", "text/markdown")),
    ]

    r = await async_client.post("/api/v1/documents/upload-batch", files=files, headers=auth_headers)

    assert r.status_code == 207
    body = r.json()
    assert body["total"] == 2
    assert body["accepted"] == 2
    assert body["failed"] == 0
    assert all(item["status"] == "accepted" for item in body["results"])


@pytest.mark.asyncio
async def test_upload_batch_all_invalid_returns_207(async_client, auth_headers, monkeypatch):
    from app.services.ingestion_queue import FakeIngestionQueue

    monkeypatch.setattr("app.api.v1.documents.CeleryIngestionQueue", lambda settings: FakeIngestionQueue())

    files = [
        ("files", ("bad-1.exe", b"abc", "application/x-msdownload")),
        ("files", ("bad-2.exe", b"def", "application/x-msdownload")),
    ]

    r = await async_client.post("/api/v1/documents/upload-batch", files=files, headers=auth_headers)

    assert r.status_code == 207
    body = r.json()
    assert body["total"] == 2
    assert body["accepted"] == 0
    assert body["failed"] == 2
    assert all(item["status"] == "failed" for item in body["results"])


@pytest.mark.asyncio
async def test_upload_batch_empty_list_returns_422(async_client, auth_headers, monkeypatch):
    from app.services.ingestion_queue import FakeIngestionQueue

    monkeypatch.setattr("app.api.v1.documents.CeleryIngestionQueue", lambda settings: FakeIngestionQueue())

    r = await async_client.post("/api/v1/documents/upload-batch", files=[], headers=auth_headers)

    assert r.status_code == 422


def test_upload_route_does_not_import_worker_or_celery():
    import inspect
    import app.api.v1.documents as documents

    source = inspect.getsource(documents.upload)
    assert "send_task" not in source
    # CeleryIngestionQueue is the abstraction layer; ensure no direct celery imports
    assert "from celery" not in source.lower()
    assert "celery_app" not in source
