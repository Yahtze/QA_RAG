from io import BytesIO
import uuid

import pytest

from app.services.storage import (
    DisallowedContentTypeError,
    InvalidPdfError,
    LocalStorageService,
    UploadTooLargeError,
)


@pytest.mark.asyncio
async def test_store_pdf_and_delete(settings):
    svc = LocalStorageService(settings)
    doc_id = uuid.uuid4()
    user_id = uuid.uuid4()
    out = await svc.store_upload(
        user_id=user_id,
        document_id=doc_id,
        filename="x.pdf",
        content_type="application/pdf",
        upload=BytesIO(b"%PDF-1.5 test"),
    )
    assert out.storage_path.endswith(f"{doc_id}.pdf")
    assert "x.pdf" not in out.storage_path
    await svc.delete(out.storage_path)


@pytest.mark.asyncio
async def test_rejects_bad_types_and_sizes(settings):
    svc = LocalStorageService(settings)
    with pytest.raises(DisallowedContentTypeError):
        await svc.store_upload(
            user_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            filename="x.exe",
            content_type="application/octet-stream",
            upload=BytesIO(b"bad"),
        )

    settings.MAX_UPLOAD_BYTES = 2
    with pytest.raises(UploadTooLargeError):
        await svc.store_upload(
            user_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            filename="x.txt",
            content_type="text/plain",
            upload=BytesIO(b"abcd"),
        )


@pytest.mark.asyncio
async def test_rejects_fake_pdf(settings):
    svc = LocalStorageService(settings)
    with pytest.raises(InvalidPdfError):
        await svc.store_upload(
            user_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            filename="x.pdf",
            content_type="application/pdf",
            upload=BytesIO(b"NOTPDF"),
        )
