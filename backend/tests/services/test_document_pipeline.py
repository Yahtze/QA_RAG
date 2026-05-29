from io import BytesIO

import pytest
from sqlalchemy import select

from app.models import Document, User
from app.services.document_pipeline import DocumentPipelineService
from app.services.storage import LocalStorageService


@pytest.mark.asyncio
async def test_upload_list_get_delete(db_session, settings):
    user = User(email="u@example.com", hashed_password="x", name="u")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    svc = DocumentPipelineService(db_session, LocalStorageService(settings))

    class Upload:
        filename = "a.pdf"
        content_type = "application/pdf"
        file = BytesIO(b"%PDF-1.5 data")

    doc = await svc.upload(user=user, upload_file=Upload())
    assert doc.status == "ready"

    page = await svc.list(user=user, cursor=None, limit=20)
    assert len(page.items) == 1

    got = await svc.get(user=user, document_id=doc.id)
    assert got.id == doc.id

    await svc.delete(user=user, document_id=doc.id)
    rows = (await db_session.execute(select(Document))).scalars().all()
    assert rows == []
