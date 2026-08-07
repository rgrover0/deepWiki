"""Pipeline-layer smoke: shared graph/embedding entrypoints import.

A full PetClinic ingest is the live green check (issue #11). This test only
proves the package surface the API currently couples to still imports.
"""

from __future__ import annotations

import pytest

pytest.importorskip("neo4j")


def test_pipeline_graph_schema_imports():
    from pipeline.graph.schema import get_driver, setup_schema

    assert callable(get_driver)
    assert callable(setup_schema)


def test_pipeline_embeddings_imports():
    pytest.importorskip("qdrant_client")
    from pipeline.embeddings.vector_store import get_client, setup_all_collections
    from pipeline.embeddings.embedder import embed_text

    assert callable(get_client)
    assert callable(setup_all_collections)
    assert callable(embed_text)


def test_pipeline_bootstrap_entrypoint_imports():
    from pipeline.project_bootstrap import start_project_bootstrap

    assert callable(start_project_bootstrap)
