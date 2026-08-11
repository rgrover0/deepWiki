"""Compatibility shim — prefer ``from core.embeddings import …``."""

from core.embeddings.embedder import *  # noqa: F401,F403
from core.embeddings.vector_store import *  # noqa: F401,F403
