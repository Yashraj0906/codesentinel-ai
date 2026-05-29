# ============================================================
# cache.py — Redis caching wrapper
# ============================================================
# WHY THIS EXISTS:
# Imagine someone asks your onboarding agent:
#   "How does authentication work in this codebase?"
# The first time: LLM processes it → takes 3 seconds, costs $0.002
# The second time (same question): Why process again?
#
# Redis stores the answer so the second time is INSTANT and FREE.
#
# WHAT IS REDIS:
# Redis is a dictionary that lives OUTSIDE your Python program.
# - Python dict: dies when your program restarts
# - Redis: survives restarts, can be shared across services
# - It's blazing fast: stores everything in RAM (memory)
#
# Run Redis via Docker:
#   docker run -p 6379:6379 redis:7-alpine
# ============================================================

import json
import hashlib
import redis
from src.config import get_settings


class CacheService:
    """
    Simple cache using Redis.
    
    HOW IT WORKS:
    1. You give it a key (prefix + data)
    2. It hashes the data to create a unique cache key
    3. On set(): stores the value with a TTL (time-to-live)
    4. On get(): returns the value if it exists and hasn't expired
    
    USAGE:
        cache = CacheService()
        
        # Check if we have a cached answer:
        cached = cache.get("onboard_qa", "How does auth work?")
        if cached:
            return cached  # Instant! No LLM call needed
        
        # If not cached, do the expensive work:
        answer = llm.chat(...)  # Takes 3 seconds
        
        # Cache it for next time:
        cache.set("onboard_qa", "How does auth work?", answer)
    """
    
    def __init__(self):
        settings = get_settings()
        # Connect to Redis
        # decode_responses=True means Redis returns strings, not bytes
        self.client = redis.from_url(settings.redis_url, decode_responses=True)
        self.default_ttl = 3600  # Default: cache expires after 1 hour (3600 seconds)
    
    def _make_key(self, prefix: str, data: str) -> str:
        """
        Create a unique cache key from prefix + hash of data.
        
        WHY HASH: The question might be very long. Hashing it gives
        a fixed-length key. Same question always = same hash.
        
        Example:
            prefix = "onboard_qa"
            data = "How does authentication work?"
            key = "codesentinel:onboard_qa:a3f2b8c1d4e5..."
        """
        hash_val = hashlib.md5(data.encode()).hexdigest()
        return f"codesentinel:{prefix}:{hash_val}"
    
    def get(self, prefix: str, data: str) -> dict | None:
        """
        Get a cached result.
        Returns the cached dict if found, None if not found or expired.
        """
        key = self._make_key(prefix, data)
        result = self.client.get(key)
        if result:
            return json.loads(result)  # Convert JSON string back to Python dict
        return None
    
    def set(self, prefix: str, data: str, value: dict, ttl: int | None = None):
        """
        Cache a result.
        
        Parameters:
            prefix: Category name (e.g., "onboard_qa", "security_scan")
            data: The input that produces this result (e.g., the question)
            value: The result to cache (must be a dict)
            ttl: Time-to-live in seconds (after this, cache auto-deletes)
        """
        key = self._make_key(prefix, data)
        self.client.setex(
            key,                                    # The cache key
            ttl or self.default_ttl,                # How long to keep it
            json.dumps(value),                      # Convert dict to JSON string for storage
        )
    
    def clear_prefix(self, prefix: str):
        """
        Clear all cache entries with a given prefix.
        Useful when you re-index a codebase (old answers are stale).
        """
        pattern = f"codesentinel:{prefix}:*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)
            print(f"[OK] Cleared {len(keys)} cached entries for '{prefix}'")
