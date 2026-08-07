"""Shared pytest fixtures for DeepWiki smoke baselines."""

from __future__ import annotations

import os

import pytest


def _env_ready() -> bool:
    required = ("NEO4J_URI", "NEO4J_PASSWORD")
    return all(os.getenv(k) for k in required)


requires_live_env = pytest.mark.skipif(
    not _env_ready(),
    reason="NEO4J_URI / NEO4J_PASSWORD not set — record live /ask + admin status manually",
)
