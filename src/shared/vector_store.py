"""
Qdrant vector store operations.
Handles collection creation, document upsert, and semantic search.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from src.config import get_settings
from src.shared.embeddings import EmbeddingService
import uuid


class VectorStore:
    """Wrapper around Qdrant for vector storage and semantic search."""
    
    def __init__(self):
        settings = get_settings()
        kwargs = {"url": settings.qdrant_url}
        if settings.qdrant_api_key:
            kwargs["api_key"] = settings.qdrant_api_key
        self.client = QdrantClient(**kwargs)
        self.embedder = EmbeddingService()
    
    def create_collection(self, name: str, dimension: int = 384):
        """Create a collection if it doesn't already exist."""
        collections = [c.name for c in self.client.get_collections().collections]
        if name not in collections:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE,
                ),
            )
            print(f"[OK] Created collection: {name}")
        else:
            print(f"[i] Collection '{name}' already exists, skipping")
    
    def recreate_collection(self, name: str, dimension: int = 384):
        """Delete and recreate collection to clear old data."""
        collections = [c.name for c in self.client.get_collections().collections]
        if name in collections:
            self.client.delete_collection(collection_name=name)
            print(f"[OK] Deleted old collection: {name}")
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE,
            ),
        )
        print(f"[OK] Created fresh collection: {name}")
    
    def upsert(self, collection: str, documents: list[dict]):
        """Insert or update documents. Each doc needs 'id', 'text', and 'metadata' keys."""
        texts = [doc["text"] for doc in documents]
        embeddings = self.embedder.embed_batch(texts)
        
        points = []
        for doc, emb in zip(documents, embeddings):
            raw_id = doc.get("id", str(uuid.uuid4()))
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_id))
            
            point = PointStruct(
                id=point_id,
                vector=emb,
                payload={
                    **doc["metadata"],
                    "text": doc["text"],
                },
            )
            points.append(point)
        
        self.client.upsert(collection_name=collection, points=points)
        print(f"[OK] Upserted {len(points)} points to '{collection}'")
    
    def search(
        self,
        collection: str,
        query: str,
        top_k: int = 5,
        filter_conditions: dict | None = None,
    ) -> list[dict]:
        """Search for documents semantically similar to the query text."""
        query_embedding = self.embedder.embed(query)
        
        qdrant_filter = None
        if filter_conditions:
            qdrant_filter = Filter(
                must=[
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter_conditions.items()
                ]
            )
        
        results = self.client.query_points(
            collection_name=collection,
            query=query_embedding,
            limit=top_k,
            query_filter=qdrant_filter,
        )
        
        return [
            {
                "text": point.payload.get("text", ""),
                "metadata": {k: v for k, v in point.payload.items() if k != "text"},
                "score": point.score,
            }
            for point in results.points
        ]
