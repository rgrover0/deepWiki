"""Unit tests for shared config."""

from __future__ import annotations

from core import config


def test_get_settings_reads_env(monkeypatch):
    config.get_settings.cache_clear()
    monkeypatch.setenv("NEO4J_URI", "bolt://example:7687")
    monkeypatch.setenv("NEO4J_USER", "neo")
    monkeypatch.setenv("REPO_CLONE_DIR", "/tmp/repos")
    settings = config.get_settings()
    assert settings["neo4j_uri"] == "bolt://example:7687"
    assert settings["neo4j_user"] == "neo"
    assert settings["repo_clone_dir"] == "/tmp/repos"
    config.get_settings.cache_clear()
