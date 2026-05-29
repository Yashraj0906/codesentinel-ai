# ============================================================
# config.py — The brain of your project settings
# ============================================================
# WHY THIS FILE EXISTS:
# Instead of writing api_key = "sk-..." in 10 different files,
# you write it ONCE here. Every other file reads from this.
# It also reads from .env file automatically — so secrets
# never appear in your actual code.
# ============================================================

# IMPORT 1: BaseSettings from pydantic_settings
# This is like a regular Python class, but it automatically:
#   - Reads values from your .env file
#   - Validates types (if you say int, it must be int)
#   - Gives clear errors if something is wrong
from pydantic_settings import BaseSettings

# IMPORT 2: lru_cache from functools
# This makes get_settings() return the SAME object every time
# instead of creating a new one. Why? Loading .env file 100 times
# is wasteful — load once, reuse everywhere.
from functools import lru_cache


class Settings(BaseSettings):
    """
    All project settings in one place.
    
    HOW IT WORKS:
    - Each field below is a setting
    - If the setting exists in .env file, it uses that value
    - If not, it uses the default value written here
    - Field names are CASE-INSENSITIVE when matching .env keys
      (groq_api_key matches GROQ_API_KEY in .env)
    """
    
    # ── LLM Settings ──
    # These control how you talk to the Groq API
    groq_api_key: str = ""                          # Your Groq API key (loaded from .env)
    llm_model: str = "llama-3.3-70b-versatile"      # Which model to use on Groq
    llm_temperature: float = 0.1                     # 0.0 = very deterministic, 1.0 = very creative
                                                     # We use 0.1 because code analysis needs consistency
    llm_max_tokens: int = 4096                       # Maximum response length from the LLM
    
    # ── Embedding Settings ──
    # Embeddings convert text/code into numbers (vectors) so we can
    # find "similar" things. Like converting words into coordinates
    # on a map — similar words are close together.
    embedding_model: str = "BAAI/bge-small-en-v1.5"  # The model that creates embeddings
    embedding_dimension: int = 384                     # Each embedding is a list of 384 numbers
    
    # ── Qdrant (Vector Database) ──
    # Qdrant stores embeddings and lets you search for similar ones.
    # Think of it as: "I have this code, find me similar vulnerability patterns"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_cve: str = "cve_vulnerabilities"   # Collection for security vulnerability data
    qdrant_collection_code: str = "codebase_chunks"      # Collection for codebase code chunks
    
    # ── Redis (Cache) ──
    # Redis is like a Python dictionary, but it lives OUTSIDE your program.
    # If you restart your app, the cache is still there.
    # We use it to: avoid re-running expensive LLM calls for the same question
    redis_url: str = "redis://localhost:6379"
    
    # ── PostgreSQL (Database) ──
    # This stores permanent data: users, reviews, chat history.
    # Unlike Redis (temporary cache), this is your permanent storage.
    database_url: str = "postgresql+asyncpg://codesentinel:password@localhost:5432/codesentinel"
    
    # ── Authentication ──
    # JWT = JSON Web Token. It's like a temporary ID card.
    # When a user logs in, they get a token. They send this token
    # with every request to prove who they are.
    jwt_secret_key: str = "change-this-in-production"   # Secret used to sign tokens
    jwt_algorithm: str = "HS256"                         # Algorithm for signing
    jwt_expiry_minutes: int = 60                         # Token expires after 1 hour
    
    # ── Code Review Settings ──
    max_self_heal_attempts: int = 3       # If a fix fails tests, retry up to 3 times
    test_timeout_seconds: int = 30        # Kill test if it runs longer than 30 seconds
    top_k_security_results: int = 5       # Retrieve top 5 similar CVE entries when scanning
    
    # ── Codebase Onboarding Settings ──
    max_chunk_tokens: int = 512           # Max size of each code chunk
    top_k_code_results: int = 10          # Retrieve top 10 code chunks when answering questions
    
    # ── GitHub ──
    github_token: str = ""                # Optional: needed only for private repos
    
    # ── LangSmith (Optional Monitoring) ──
    # LangSmith traces every LLM call so you can debug your pipeline.
    # Optional — leave empty if you don't want tracing.
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "codesentinel-ai"
    
    # This inner class tells Pydantic WHERE to find the .env file
    class Config:
        env_file = ".env"              # Read from this file
        env_file_encoding = "utf-8"    # Handle special characters


# This function returns the Settings object.
# @lru_cache means: first call creates Settings, every call after that
# returns the SAME object. No wasted work.
@lru_cache()
def get_settings() -> Settings:
    return Settings()


# ============================================================
# HOW OTHER FILES WILL USE THIS:
#
#   from src.config import get_settings
#
#   settings = get_settings()
#   print(settings.groq_api_key)       # Your API key from .env
#   print(settings.llm_model)          # "llama-3.3-70b-versatile"
#   print(settings.max_self_heal_attempts)  # 3
#
# That's it. One import, one call, access any setting.
# ============================================================
