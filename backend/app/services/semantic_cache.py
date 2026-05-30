import asyncio
import json
from array import array
from dataclasses import dataclass
from hashlib import sha256
from time import time
from uuid import uuid4

import redis.asyncio as redis

from app.core.config import Settings


@dataclass(frozen=True)
class SemanticCacheHit:
    answer: str
    citations: dict[str, dict[str, object]]


class RedisSemanticCache:
    def __init__(self, settings: Settings, embeddings):
        self.settings = settings
        self.embeddings = embeddings
        timeout_s = settings.SEMANTIC_CACHE_TIMEOUT_MS / 1000
        self.client = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=timeout_s,
            socket_timeout=timeout_s,
            retry_on_timeout=False,
            decode_responses=False,
        )
        self.index_name = settings.SEMANTIC_CACHE_INDEX_NAME
        self.key_prefix = settings.SEMANTIC_CACHE_KEY_PREFIX
        self._index_ready = False
        self._ensure_lock = asyncio.Lock()

    async def get(self, *, query: str) -> SemanticCacheHit | None:
        vector = await self._embed_query(query)
        if vector is None:
            return None
        await self._ensure_index()

        query_str = "*=>[KNN 1 @question_embedding $vec AS distance]"
        result = await self.client.execute_command(
            "FT.SEARCH",
            self.index_name,
            query_str,
            "PARAMS",
            "2",
            "vec",
            vector,
            "RETURN",
            "3",
            "response",
            "citations",
            "distance",
            "SORTBY",
            "distance",
            "ASC",
            "DIALECT",
            "2",
        )
        if not isinstance(result, list) or not result or int(result[0]) < 1:
            return None

        fields = result[2]
        field_map: dict[str, bytes] = {}
        for i in range(0, len(fields), 2):
            field_map[fields[i].decode()] = fields[i + 1]

        distance = float(field_map.get("distance", b"1"))
        max_distance = 1 - self.settings.SEMANTIC_CACHE_MIN_SIMILARITY
        if distance > max_distance:
            return None

        answer = field_map.get("response", b"").decode()
        citations_raw = field_map.get("citations", b"{}").decode()
        citations = json.loads(citations_raw)
        return SemanticCacheHit(answer=answer, citations=citations)

    async def set(
        self,
        *,
        query: str,
        answer: str,
        citations: dict[str, dict[str, object]],
    ) -> None:
        vector = await self._embed_query(query)
        if vector is None:
            return
        await self._ensure_index()

        query_hash = sha256(query.encode()).hexdigest()[:12]
        key = f"{self.key_prefix}{query_hash}:{uuid4().hex}"
        await self.client.hset(
            key,
            mapping={
                "query": query,
                "response": answer,
                "citations": json.dumps(citations),
                "question_embedding": vector,
                "created_at": str(int(time())),
            },
        )
        await self.client.expire(key, self.settings.SEMANTIC_CACHE_TTL_SECONDS)

    async def _embed_query(self, query: str) -> bytes | None:
        vectors = await self.embeddings.embed_texts([query])
        if not vectors:
            return None
        return array("f", vectors[0]).tobytes()

    async def _ensure_index(self) -> None:
        if self._index_ready:
            return
        async with self._ensure_lock:
            if self._index_ready:
                return
            dimension = self.settings.EMBEDDING_DIMENSION
            try:
                await self.client.execute_command(
                    "FT.CREATE",
                    self.index_name,
                    "ON",
                    "HASH",
                    "PREFIX",
                    "1",
                    self.key_prefix,
                    "SCHEMA",
                    "query",
                    "TEXT",
                    "response",
                    "TEXT",
                    "citations",
                    "TEXT",
                    "created_at",
                    "NUMERIC",
                    "question_embedding",
                    "VECTOR",
                    "HNSW",
                    "6",
                    "TYPE",
                    "FLOAT32",
                    "DIM",
                    str(dimension),
                    "DISTANCE_METRIC",
                    "COSINE",
                )
            except Exception as exc:
                if "Index already exists" not in str(exc):
                    raise
            self._index_ready = True
