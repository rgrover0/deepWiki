"""API-layer smoke: app boots and /health responds.

Live /ask check (Phase 0 green checklist) requires NEO4J_* + Qdrant and is
documented on GitHub issue #11 when run against a deployed or local stack.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")


def test_api_app_imports():
    from api.main import app

    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/health" in paths
    assert any(p and p.startswith("/ask") for p in paths)
    assert any(p and p.startswith("/admin") for p in paths)


def test_api_health_endpoint():
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
