"""
Redis caching layer for expensive LLM calls.
Uses MD5 hashing for cache keys with configurable TTL.
"""

import json
import hashlib
import redis
from src.config import get_settings


class CacheService:
    """Redis-backed cache for LLM responses and query results."""
    
    def __init__(self):
        settings = get_settings()
        self.client = redis.from_url(settings.redis_url, decode_responses=True)
        self.default_ttl = 3600
    
    def _make_key(self, prefix: str, data: str) -> str:
        """Create a unique cache key from prefix + MD5 hash of input data."""
        hash_val = hashlib.md5(data.encode()).hexdigest()
        return f"codesentinel:{prefix}:{hash_val}"
    
    def get(self, prefix: str, data: str) -> dict | None:
        """Retrieve cached result. Returns None if not found or expired."""
        key = self._make_key(prefix, data)
        result = self.client.get(key)
        if result:
            return json.loads(result)
        return None
    
    def set(self, prefix: str, data: str, value: dict, ttl: int | None = None):
        """Store a result in cache with TTL (default: 1 hour)."""
        key = self._make_key(prefix, data)
        self.client.setex(key, ttl or self.default_ttl, json.dumps(value))
    
    def clear_prefix(self, prefix: str):
        """Delete all cache entries matching a prefix."""
        pattern = f"codesentinel:{prefix}:*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)
            print(f"[OK] Cleared {len(keys)} cached entries for '{prefix}'")
