"""
Client for ts-analysis-service (Angular/TypeScript AST analysis).

Mirrors the interface of java_analysis_client.py so both can be
used interchangeably in ingestion pipelines.
"""

import os
import requests
import logging

logger = logging.getLogger(__name__)

_BASE = os.getenv("TS_ANALYSIS_URL", "http://localhost:8082")


def analyse_file(file_path: str) -> dict:
    resp = requests.post(f"{_BASE}/analyze", json={"file_path": file_path}, timeout=30)
    resp.raise_for_status()
    results = resp.json()
    return results[0] if results else {}


def analyse_files(file_paths: list[str]) -> list[dict]:
    results, _ = analyse_files_detailed(file_paths)
    return results


def analyse_files_detailed(file_paths: list[str]) -> tuple[list[dict], list[dict]]:
    """Analyze TS files and return (results, errors) for richer pipeline diagnostics."""
    errors: list[dict] = []
    try:
        resp = requests.post(f"{_BASE}/analyze", json={"file_paths": file_paths}, timeout=60)
        resp.raise_for_status()
        results = resp.json() or []
        if not results:
            errors.append({"file": "<batch>", "error": "TypeScript parser returned empty result set"})
            logger.warning("TypeScript parser returned empty result set for %d files", len(file_paths))
        return results, errors
    except requests.HTTPError as exc:
        body = ""
        try:
            body = (exc.response.text or "")[:400] if exc.response is not None else ""
        except Exception:
            body = ""
        msg = f"HTTP {exc.response.status_code}: {body}" if getattr(exc, "response", None) is not None else str(exc)
        errors.append({"file": "<batch>", "error": msg})
        logger.exception("TypeScript parser HTTP error")
        return [], errors
    except Exception as exc:
        errors.append({"file": "<batch>", "error": str(exc)[:400]})
        logger.exception("TypeScript parser failed")
        return [], errors


def is_service_healthy() -> bool:
    try:
        resp = requests.get(f"{_BASE}/health", timeout=5)
        return resp.status_code == 200 and resp.json().get("status") == "ok"
    except Exception:
        return False
