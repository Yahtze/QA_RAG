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
            else:
                info = await client.get_collection(self.settings.QDRANT_COLLECTION_NAME)
                size = info.config.params.vectors.size
                distance = info.config.params.vectors.distance
                if size != self.settings.EMBEDDING_DIMENSION or distance != Distance.COSINE:
                    raise QdrantCollectionMismatchError(
                        "Qdrant collection mismatch: "
                        f"expected size={self.settings.EMBEDDING_DIMENSION},"
                        f"distance={Distance.COSINE}; got size={size},distance={distance}"
                    )
            await client.create_payload_index(
                collection_name=self.settings.QDRANT_COLLECTION_NAME,
                field_name="document_id",
                field_schema="keyword",
            )
            await client.create_payload_index(
                collection_name=self.settings.QDRANT_COLLECTION_NAME,
                field_name="user_id",
                field_schema="keyword",
            )
        finally:
            await client.close()
