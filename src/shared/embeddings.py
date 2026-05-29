# ============================================================
# embeddings.py — Converts text into numbers (vectors)
# ============================================================
# WHY THIS EXISTS:
# To find "similar" things, computers need numbers, not text.
# This file converts text/code into a list of 384 numbers (a "vector").
#
# EXAMPLE:
#   "SQL injection attack" → [0.12, -0.45, 0.78, ..., 0.33]  (384 numbers)
#   "database query hack"  → [0.11, -0.44, 0.77, ..., 0.31]  (384 numbers)
#   "hello world python"   → [0.89, 0.23, -0.56, ..., -0.12] (384 numbers)
#
# Notice: the first two are SIMILAR (close numbers) because they
# mean similar things. The third is DIFFERENT (far numbers).
# This is how your security scanner finds matching vulnerabilities.
#
# HOW: We use a pre-trained model (BGE-small) that already knows
# what words/code mean. You just call model.encode("text").
# ============================================================

from sentence_transformers import SentenceTransformer
from src.config import get_settings


class EmbeddingService:
    """
    Generates embedding vectors from text/code.
    
    Uses Singleton pattern: the model loads only ONCE, no matter
    how many times you create EmbeddingService(). Loading a model
    takes ~2 seconds — you don't want to do that every time.
    
    USAGE:
        emb = EmbeddingService()
        
        # Single text:
        vector = emb.embed("SELECT * FROM users")
        print(len(vector))  # 384
        
        # Multiple texts at once (faster):
        vectors = emb.embed_batch(["text1", "text2", "text3"])
        print(len(vectors))  # 3, each is a list of 384 numbers
    """
    
    # Class-level variable — shared across all instances
    _instance = None
    
    def __new__(cls):
        # Singleton pattern:
        # First call: create instance, load model
        # Every call after: return the SAME instance (model already loaded)
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = get_settings()
            print(f"[*] Loading embedding model: {settings.embedding_model}...")
            cls._instance.model = SentenceTransformer(settings.embedding_model)
            cls._instance.dimension = settings.embedding_dimension
            print(f"[OK] Embedding model loaded (dimension: {settings.embedding_dimension})")
        return cls._instance
    
    def embed(self, text: str) -> list[float]:
        """
        Convert a single text string into a vector.
        Returns: list of 384 floats
        """
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        Convert multiple texts into vectors at once.
        Much faster than calling embed() in a loop.
        
        batch_size: How many to process at once (32 is a good default).
        Returns: list of vectors, each is a list of 384 floats
        """
        return self.model.encode(texts, batch_size=batch_size).tolist()
