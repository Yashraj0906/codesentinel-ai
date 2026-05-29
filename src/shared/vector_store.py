# ============================================================
# vector_store.py — Store and search vectors in Qdrant
# ============================================================
# WHY THIS EXISTS:
# After embeddings.py converts text to vectors, you need somewhere
# to STORE them and SEARCH through them. That's Qdrant.
#
# Think of it like this:
#   1. You have 500 vulnerability descriptions (CWE database)
#   2. You convert each one to a vector and store in Qdrant
#   3. When you see new code, you convert it to a vector
#   4. You ask Qdrant: "Find the 5 most similar stored vectors"
#   5. Qdrant returns: "This code looks like SQL injection (CWE-89)"
#
# It's like Google search, but instead of searching by keywords,
# you search by MEANING.
#
# Qdrant runs as a separate service (via Docker):
#   docker run -p 6333:6333 qdrant/qdrant
# ============================================================

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,     # Defines how vectors are stored
    Distance,         # How to measure similarity (cosine = angle between vectors)
    PointStruct,      # A single entry (vector + metadata)
    Filter,           # For filtering search results
    FieldCondition,   # A single filter condition
    MatchValue,       # Match a specific value
)
from src.config import get_settings
from src.shared.embeddings import EmbeddingService
import uuid


class VectorStore:
    """
    Wrapper around Qdrant vector database.
    
    KEY CONCEPTS:
    - Collection: Like a table in a database. You have two:
      "cve_vulnerabilities" (security data) and "codebase_chunks" (code)
    - Point: One entry = a vector + metadata (text, source, type, etc.)
    - Search: "Find points whose vectors are closest to this query vector"
    
    USAGE:
        vs = VectorStore()
        
        # Create a collection:
        vs.create_collection("my_collection")
        
        # Add documents:
        vs.upsert("my_collection", [
            {"id": "1", "text": "SQL injection is...", "metadata": {"severity": "critical"}}
        ])
        
        # Search:
        results = vs.search("my_collection", "database hack", top_k=5)
        # Returns the 5 most similar documents
    """
    
    def __init__(self):
        settings = get_settings()
        # Connect to Qdrant (must be running on this URL)
        self.client = QdrantClient(url=settings.qdrant_url)
        # We need the embedding service to convert text → vectors
        self.embedder = EmbeddingService()
    
    def create_collection(self, name: str, dimension: int = 384):
        """
        Create a collection (like creating a table in a database).
        If it already exists, skip it.
        
        Parameters:
            name: Collection name (e.g., "cve_vulnerabilities")
            dimension: Vector size (384 for BGE-small model)
        """
        # Check if collection already exists
        collections = [c.name for c in self.client.get_collections().collections]
        if name not in collections:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE,  # Cosine similarity: 1.0 = identical, 0.0 = unrelated
                ),
            )
            print(f"[OK] Created collection: {name}")
        else:
            print(f"[i] Collection '{name}' already exists, skipping")
    
    def upsert(self, collection: str, documents: list[dict]):
        """
        Insert documents into the vector store.
        "Upsert" = insert if new, update if exists.
        
        Each document must have:
        {
            "id": "unique_id",         # Unique identifier
            "text": "the content...",   # Text to embed and search
            "metadata": {...}          # Extra info (severity, file_path, etc.)
        }
        """
        # Step 1: Extract all texts
        texts = [doc["text"] for doc in documents]
        
        # Step 2: Convert all texts to vectors (batch = fast)
        embeddings = self.embedder.embed_batch(texts)
        
        # Step 3: Create Qdrant points (vector + metadata)
        points = []
        for doc, emb in zip(documents, embeddings):
            # Qdrant requires IDs to be UUIDs or integers, not strings.
            # uuid5 converts any string → a deterministic UUID
            raw_id = doc.get("id", str(uuid.uuid4()))
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_id))
            
            point = PointStruct(
                id=point_id,
                vector=emb,                             # The embedding vector
                payload={                               # Metadata stored alongside the vector
                    **doc["metadata"],                  # Spread all metadata fields
                    "text": doc["text"],                # Also store the original text
                },
            )
            points.append(point)
        
        # Step 4: Upload to Qdrant
        self.client.upsert(collection_name=collection, points=points)
        print(f"[OK] Upserted {len(points)} points to '{collection}'")
    
    def search(
        self,
        collection: str,
        query: str,
        top_k: int = 5,
        filter_conditions: dict | None = None,
    ) -> list[dict]:
        """
        Search for documents similar to the query.
        
        Parameters:
            collection: Which collection to search
            query: The text to search for (will be embedded automatically)
            top_k: How many results to return
            filter_conditions: Optional filters like {"severity": "critical"}
        
        Returns:
            List of dicts, each with:
            {
                "text": "the matching document text",
                "metadata": {"severity": "critical", ...},
                "score": 0.89  # Similarity score (0-1, higher = more similar)
            }
        """
        # Step 1: Convert query text to vector
        query_embedding = self.embedder.embed(query)
        
        # Step 2: Build filter if provided
        qdrant_filter = None
        if filter_conditions:
            qdrant_filter = Filter(
                must=[
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter_conditions.items()
                ]
            )
        
        # Step 3: Search Qdrant (using query_points API)
        results = self.client.query_points(
            collection_name=collection,
            query=query_embedding,
            limit=top_k,
            query_filter=qdrant_filter,
        )
        
        # Step 4: Convert results to clean dicts
        return [
            {
                "text": point.payload.get("text", ""),
                "metadata": {k: v for k, v in point.payload.items() if k != "text"},
                "score": point.score,
            }
            for point in results.points
        ]
