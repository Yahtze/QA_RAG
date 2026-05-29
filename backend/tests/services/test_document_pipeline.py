import pytest

from app.services.document_pipeline import DocumentPipelineService


@pytest.mark.asyncio
async def test_pipeline_upload_delegates_to_ingestion(db_session):
    class Ingestion:
        async def ingest_upload(self, *, user, upload_file):
            return "uploaded"

    service = DocumentPipelineService(
        db_session, storage=None, ingestion_service=Ingestion(), vector_store=None
    )
    assert await service.upload(user=object(), upload_file=object()) == "uploaded"
