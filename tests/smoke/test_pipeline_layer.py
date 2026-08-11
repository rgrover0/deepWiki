"""Pipeline-layer smoke: shared graph/embedding entrypoints import.

A full PetClinic ingest is the live green check (issue #11). This test only
proves the package surface the API currently couples to still imports.
"""

from __future__ import annotations

import pytest

pytest.importorskip("neo4j")


def test_pipeline_graph_schema_imports():
    from core.graph.schema import get_driver, setup_schema

    assert callable(get_driver)
    assert callable(setup_schema)


def test_pipeline_embeddings_imports():
    pytest.importorskip("qdrant_client")
    from core.embeddings.vector_store import get_client, setup_all_collections
    from core.embeddings.embedder import embed_text

    assert callable(get_client)
    assert callable(setup_all_collections)
    assert callable(embed_text)


def test_pipeline_admin_cli_entrypoint_imports():
    from pipeline.admin_cli import build_parser, main
    from pipeline.project_bootstrap import start_project_bootstrap

    assert callable(start_project_bootstrap)
    assert callable(main)
    parser = build_parser()
    assert parser.parse_args(["suite-bootstrap"]).command == "suite-bootstrap"
