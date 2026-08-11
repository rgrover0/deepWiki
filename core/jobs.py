"""File-backed job store shared by API (poll) and pipeline CLI (update).

Keeps api and pipeline decoupled: neither package imports the other.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

_lock = threading.Lock()


def _job_dir() -> Path:
    configured = os.getenv("DEEPWIKI_JOB_DIR")
    if configured:
        path = Path(configured)
    else:
        path = Path(tempfile.gettempdir()) / "deepwiki-jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path(repo_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in repo_id)
    return _job_dir() / f"{safe}.json"


def save_job(repo_id: str, job: dict[str, Any]) -> None:
    path = _path(repo_id)
    payload = {"repo_id": repo_id, **job}
    with _lock:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_job(repo_id: str) -> dict[str, Any] | None:
    path = _path(repo_id)
    if not path.exists():
        return None
    with _lock:
        return json.loads(path.read_text(encoding="utf-8"))


def list_jobs() -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    with _lock:
        for path in _job_dir().glob("*.json"):
            try:
                jobs.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
    return jobs


PIPELINE_STEPS = [
    "Cloning repository",
    "Parsing source files",
    "Writing knowledge graph",
    "Generating wiki summaries",
    "Extracting API contracts",
    "Embedding to Qdrant",
    "Matching API contracts",
    "Registering project",
]


def make_job() -> dict[str, Any]:
    return {
        "status": "running",
        "progress": 0,
        "current_step": PIPELINE_STEPS[0],
        "error": None,
        "logs": [],
        "stats": {},
        "steps": [
            {"label": name, "status": "pending", "detail": ""}
            for name in PIPELINE_STEPS
        ],
    }
