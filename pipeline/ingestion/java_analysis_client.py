import os
import httpx
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

CODE_ANALYSIS_URL = os.getenv("CODE_ANALYSIS_URL", "http://localhost:8081")


def analyze_file(file_path: str) -> dict:
    """Send a Java file to the code-analysis-service and return parsed structure."""
    content = Path(file_path).read_text(encoding="utf-8", errors="replace")
    filename = Path(file_path).name

    response = httpx.post(
        f"{CODE_ANALYSIS_URL}/analyze",
        json={"file_content": content, "filename": filename},
        timeout=30.0
    )
    response.raise_for_status()
    result = response.json()
    # Attach the original path so downstream writers have it
    result["file"] = file_path
    return result


def analyze_files(file_paths: list[str]) -> list[dict]:
    """Analyze multiple Java files via the service. Skips files that fail."""
    results, _ = analyze_files_detailed(file_paths)
    return results


def analyze_files_detailed(file_paths: list[str]) -> tuple[list[dict], list[dict]]:
    """Analyze Java files and return (results, errors) for richer pipeline diagnostics."""
    results: list[dict] = []
    errors: list[dict] = []

    for path in file_paths:
        try:
            result = analyze_file(path)
            if result.get("classes"):
                results.append(result)
            else:
                errors.append({"file": path, "error": "No classes returned by parser"})
                logger.warning("Java parser returned no classes for file: %s", path)
        except httpx.HTTPStatusError as exc:
            body = (exc.response.text or "")[:400]
            msg = f"HTTP {exc.response.status_code}: {body}" if body else str(exc)
            errors.append({"file": path, "error": msg})
            logger.exception("Java parser HTTP error for %s", path)
        except Exception as exc:
            errors.append({"file": path, "error": str(exc)[:400]})
            logger.exception("Java parser failed for %s", path)

    return results, errors


def is_service_healthy() -> bool:
    try:
        r = httpx.get(f"{CODE_ANALYSIS_URL}/health", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False
