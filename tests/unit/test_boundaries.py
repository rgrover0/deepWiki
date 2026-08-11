"""Architectural boundary tests (import-linter contracts as unit assertions)."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _imports_of(package_dir: Path) -> set[str]:
    found: set[str] = set()
    for path in package_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module.split(".")[0])
    return found


def test_core_does_not_import_api_or_pipeline():
    imports = _imports_of(ROOT / "core")
    assert "api" not in imports
    assert "pipeline" not in imports


def test_api_does_not_import_pipeline():
    imports = _imports_of(ROOT / "api")
    assert "pipeline" not in imports


def test_pipeline_does_not_import_api():
    imports = _imports_of(ROOT / "pipeline")
    assert "api" not in imports
