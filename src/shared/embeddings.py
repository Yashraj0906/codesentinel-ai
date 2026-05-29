"""
Embedding service using Sentence Transformers (BGE-small-en).
Converts text/code into 384-dimensional vectors for semantic search.
"""

from sentence_transformers import SentenceTransformer
from src.config import get_settings


class EmbeddingService:
    """Singleton embedding service. Model loads once and is reused."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = get_settings()
            print(f"[*] Loading embedding model: {settings.embedding_model}...")
            cls._instance.model = SentenceTransformer(settings.embedding_model)
            cls._instance.dimension = settings.embedding_dimension
            print(f"[OK] Embedding model loaded (dimension: {settings.embedding_dimension})")
        return cls._instance
    
    def embed(self, text: str) -> list[float]:
        """Convert a single text string into a vector of 384 floats."""
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Convert multiple texts into vectors at once."""
        return self.model.encode(texts, batch_size=batch_size).tolist()
