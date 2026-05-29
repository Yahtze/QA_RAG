from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import Settings


class QdrantCollectionMismatchError(Exception): ...


class QdrantCollectionService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def ensure_collection(self) -> None:
        client = AsyncQdrantClient(url=self.settings.QDRANT_URL)
        try:
            collections = await client.get_collections()
            names = {c.name for c in collections.collections}
            if self.settings.QDRANT_COLLECTION_NAME not in names:
                await client.create_collection(
                    collection_name=self.settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.settings.EMBEDDING_DIMENSION, distance=Distance.COSINE
                    ),
                )
                return
            info = await client.get_collection(self.settings.QDRANT_COLLECTION_NAME)
            size = info.config.params.vectors.size
            if size != self.settings.EMBEDDING_DIMENSION:
                raise QdrantCollectionMismatchError(
                    "Qdrant dimension mismatch: "
                    f"expected {self.settings.EMBEDDING_DIMENSION}, got {size}"
                )
        finally:
            await client.close()
