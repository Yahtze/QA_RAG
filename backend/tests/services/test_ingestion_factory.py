from app.services.ingestion import IngestionService
from app.services.ingestion_factory import build_ingestion_service


def test_factory_builds_ingestion_service(db_session, settings):
    service = build_ingestion_service(session=db_session, settings=settings)
    assert isinstance(service, IngestionService)
