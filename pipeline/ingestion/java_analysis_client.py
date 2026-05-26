import os
import httpx
from pathlib import Path

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
    results = []
    for path in file_paths:
        try:
            result = analyze_file(path)
            if result.get("classes"):
                results.append(result)
        except Exception as e:
            print(f"⚠️  Skipped {path}: {e}")
    return results


def is_service_healthy() -> bool:
    try:
        r = httpx.get(f"{CODE_ANALYSIS_URL}/health", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False
