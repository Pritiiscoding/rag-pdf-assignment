"""Centralized configuration, loaded from environment variables / .env file."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    # OpenRouter
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Qdrant
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "") or None
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "pdf_docs")

    # Embeddings
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    use_api_embeddings: bool = os.getenv("USE_API_EMBEDDINGS", "false").lower() == "true"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Chunking / retrieval
    chunk_size: int = _get_int("CHUNK_SIZE", 800)
    chunk_overlap: int = _get_int("CHUNK_OVERLAP", 150)
    top_k: int = _get_int("TOP_K", 5)

    # Data
    pdf_dir: str = os.getenv("PDF_DIR", "data/pdfs")
    
    # Storage cleanup
    auto_cleanup_files: bool = os.getenv("AUTO_CLEANUP_FILES", "true").lower() == "true"
    max_file_age_hours: int = _get_int("MAX_FILE_AGE_HOURS", 24)


settings = Settings()
