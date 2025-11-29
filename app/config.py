"""Configuration management for Energy Coach application."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "500"))
    
    # Graph Mode
    USE_MOCK_NEO4J: bool = os.getenv("USE_MOCK_NEO4J", "true").lower() == "true"
    
    # Neo4j (optional)
    NEO4J_URI: Optional[str] = os.getenv("NEO4J_URI")
    NEO4J_USER: Optional[str] = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: Optional[str] = os.getenv("NEO4J_PASSWORD")
    
    # API Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "30"))
    
    # Model Configuration (using OpenAI embeddings, so this is just for reference)
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # GraphRAG Configuration
    VECTOR_SIMILARITY_TOP_K: int = int(os.getenv("VECTOR_SIMILARITY_TOP_K", "10"))
    SUBGRAPH_HOPS: int = int(os.getenv("SUBGRAPH_HOPS", "2"))
    MIN_SIMILARITY_SCORE: float = float(os.getenv("MIN_SIMILARITY_SCORE", "0.3"))


config = Config()

