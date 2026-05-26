"""
Client for ts-analysis-service (Angular/TypeScript AST analysis).

Mirrors the interface of java_analysis_client.py so both can be
used interchangeably in ingestion pipelines.
"""

import os
import requests

_BASE = os.getenv("TS_ANALYSIS_URL", "http://localhost:8082")


def analyse_file(file_path: str) -> dict:
    resp = requests.post(f"{_BASE}/analyze", json={"file_path": file_path}, timeout=30)
    resp.raise_for_status()
    results = resp.json()
    return results[0] if results else {}


def analyse_files(file_paths: list[str]) -> list[dict]:
    resp = requests.post(f"{_BASE}/analyze", json={"file_paths": file_paths}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def is_service_healthy() -> bool:
    try:
        resp = requests.get(f"{_BASE}/health", timeout=5)
        return resp.status_code == 200 and resp.json().get("status") == "ok"
    except Exception:
        return False
