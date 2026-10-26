"""
Core configuration and environment settings.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    # Must match the auth gateway's JWT_SECRET.
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")

    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "adaptive_rag")

    # Qdrant server to use; when unset, Qdrant runs embedded and stores data in QDRANT_PATH.
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "") or None
    QDRANT_PATH: str = os.getenv("QDRANT_PATH", "qdrant_data")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "user_documents")

    # Chunks retrieved per question
    RETRIEVAL_K: int = int(os.getenv("RETRIEVAL_K", "4"))
    # Most recent chat messages sent to the model with each question
    MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "10"))


settings = Settings()

if not settings.JWT_SECRET:
    raise RuntimeError("JWT_SECRET must be set (it must match the auth gateway's)")
