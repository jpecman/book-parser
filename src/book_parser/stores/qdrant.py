import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, ScoredPoint, VectorParams


class QdrantStore:
    def __init__(
        self,
        collection: str,
        vector_size: int,
        url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._client = QdrantClient(
            url=url or os.environ.get("QDRANT_URL", "http://localhost:6333"),
            api_key=api_key or os.environ.get("QDRANT_API_KEY"),
        )
        self._collection = collection
        self._vector_size = vector_size

    def ensure_collection(self) -> None:
        if self._client.collection_exists(self._collection):
            return
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=VectorParams(
                size=self._vector_size, distance=Distance.COSINE
            ),
        )

    # Qdrant only accepts unsigned integers or UUID strings as point ids.
    def upsert(
        self,
        ids: list[int | str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        points = [
            PointStruct(id=id, vector=vector, payload=payload)
            for id, vector, payload in zip(ids, vectors, payloads, strict=True)
        ]
        self._client.upsert(collection_name=self._collection, points=points)

    def search(self, vector: list[float], limit: int = 5) -> list[ScoredPoint]:
        result = self._client.query_points(
            collection_name=self._collection, query=vector, limit=limit
        )
        return result.points
