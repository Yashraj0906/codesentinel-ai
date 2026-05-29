"""
Central configuration module.
Reads all settings from .env file using pydantic-settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    
    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_cve: str = "cve_vulnerabilities"
    qdrant_collection_code: str = "codebase_chunks"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # PostgreSQL
    database_url: str = "postgresql+asyncpg://codesentinel:password@localhost:5432/codesentinel"
    
    # Authentication
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    
    # Code Review
    max_self_heal_attempts: int = 3
    test_timeout_seconds: int = 30
    top_k_security_results: int = 5
    
    # Codebase Onboarding
    max_chunk_tokens: int = 512
    top_k_code_results: int = 10
    
    # GitHub
    github_token: str = ""
    
    # LangSmith (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "codesentinel-ai"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
