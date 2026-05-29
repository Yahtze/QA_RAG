from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.embeddings import OpenAIEmbeddingProvider
from app.services.ingestion import IngestionService
from app.services.storage import LocalStorageService
from app.services.vector_store import QdrantVectorStore


def build_ingestion_service(*, session: AsyncSession, settings: Settings) -> IngestionService:
    storage = LocalStorageService(settings)
    return IngestionService(
        session=session,
        settings=settings,
        storage=storage,
        embedding_provider=OpenAIEmbeddingProvider(settings),
        vector_store=QdrantVectorStore(settings),
    )
