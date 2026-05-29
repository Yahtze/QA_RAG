import pytest


@pytest.mark.asyncio
async def test_documents_upload_list_get_delete(async_client, auth_headers):
    files = {"file": ("doc.pdf", b"%PDF-1.4 test", "application/pdf")}
    up = await async_client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
    assert up.status_code == 201
    doc_id = up.json()["id"]

    lst = await async_client.get("/api/v1/documents", headers=auth_headers)
    assert lst.status_code == 200
    assert len(lst.json()["items"]) == 1

    getr = await async_client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert getr.status_code == 200

    dele = await async_client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert dele.status_code == 204
