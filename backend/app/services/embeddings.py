from hashlib import sha256
from typing import Protocol

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.services.ingestion_errors import DeterministicIngestionError, RetryableIngestionError


class EmbeddingProvider(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class EmbeddingValidationError(Exception): ...


def validate_embeddings(*, texts: list[str], vectors: list[list[float]], dimension: int) -> None:
    if len(vectors) != len(texts):
        raise EmbeddingValidationError(f"returned {len(vectors)} vectors for {len(texts)} texts")
    for i, vector in enumerate(vectors):
        if len(vector) != dimension:
            raise EmbeddingValidationError(
                f"vector {i} has dimension {len(vector)}; expected {dimension}"
            )


def _retryable_openai(exc: BaseException) -> bool:
    if isinstance(exc, (RateLimitError, APIConnectionError)):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code >= 500
    return False


class OpenAIEmbeddingProvider:
    def __init__(self, settings: Settings):
        if settings.OPENAI_API_KEY is None:
            raise ValueError("OPENAI_API_KEY is required for OpenAIEmbeddingProvider")
        kwargs = {"api_key": settings.OPENAI_API_KEY.get_secret_value()}
        if settings.EMBEDDING_BASE_URL:
            kwargs["base_url"] = settings.EMBEDDING_BASE_URL
        self.client = AsyncOpenAI(**kwargs)
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.batch_size = settings.EMBEDDING_BATCH_SIZE

    @retry(
        retry=retry_if_exception(_retryable_openai),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        try:
            for start in range(0, len(texts), self.batch_size):
                vectors.extend(await self._embed_batch(texts[start : start + self.batch_size]))
            validate_embeddings(texts=texts, vectors=vectors, dimension=self.dimension)
            return vectors
        except (RateLimitError, APIConnectionError) as exc:
            raise RetryableIngestionError("embedding", exc) from exc
        except APIStatusError as exc:
            if exc.status_code == 400:
                raise DeterministicIngestionError(str(exc), "embedding") from exc
            if exc.status_code >= 500:
                raise RetryableIngestionError("embedding", exc) from exc
            raise DeterministicIngestionError(str(exc), "embedding") from exc
        except EmbeddingValidationError as exc:
            raise DeterministicIngestionError(str(exc), "embedding") from exc


class FakeEmbeddingProvider:
    def __init__(self, dimension: int):
        self.dimension = dimension

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            digest = sha256(text.encode()).digest()
            vectors.append([digest[i % len(digest)] / 255 for i in range(self.dimension)])
        return vectors
