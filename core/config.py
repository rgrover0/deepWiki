"""Shared configuration — single source for env loading."""

from __future__ import annotations

import os
from functools import lru_cache

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass


@lru_cache(maxsize=1)
def get_settings() -> dict[str, str]:
    """Return commonly used settings (cached after first read)."""
    return {
        "neo4j_uri": os.getenv("NEO4J_URI", ""),
        "neo4j_user": os.getenv("NEO4J_USER", "neo4j"),
        "neo4j_password": os.getenv("NEO4J_PASSWORD", ""),
        "qdrant_host": os.getenv("QDRANT_HOST", "localhost"),
        "qdrant_port": os.getenv("QDRANT_PORT", "6333"),
        "qdrant_api_key": os.getenv("QDRANT_API_KEY", ""),
        "groq_api_key": os.getenv("GROQ_API_KEY", ""),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "repo_clone_dir": os.getenv("REPO_CLONE_DIR", "repos"),
        "job_dir": os.getenv("DEEPWIKI_JOB_DIR", ""),
    }


def getenv(key: str, default: str | None = None) -> str | None:
    """Thin wrapper so callers do not re-implement dotenv loading."""
    return os.getenv(key, default)
