"""Compatibility shim — prefer ``from core.graph.schema import …``."""

from core.graph.schema import get_driver, setup_schema

__all__ = ["get_driver", "setup_schema"]
