import json
import os
from datetime import datetime
from pathlib import Path

METRICS_FILE = "output/metrics/token_log.json"
os.makedirs("output/metrics", exist_ok=True)


def count_file_tokens(file_path: str) -> int:
    """Approximate token count for a file (chars / 4)."""
    try:
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")
        return len(text) // 4
    except Exception:
        return 0


def log_token_usage(
    query: str,
    wiki_tokens: int,
    source_files: list[str]
):
    """Log a query's token usage — wiki vs raw source."""
    # Calculate what raw file reading would cost
    raw_tokens = sum(
        count_file_tokens(f) for f in source_files if f
    )

    entry = {
        "timestamp":    datetime.now().isoformat(),
        "query":        query[:80],
        "wiki_tokens":  wiki_tokens,
        "raw_tokens":   raw_tokens,
        "saved_tokens": max(0, raw_tokens - wiki_tokens),
        "source_files": len(source_files)
    }

    # Load existing log
    log = []
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE) as f:
            log = json.load(f)

    log.append(entry)

    with open(METRICS_FILE, "w") as f:
        json.dump(log, f, indent=2)

    return entry


def load_metrics() -> list[dict]:
    if not os.path.exists(METRICS_FILE):
        return []
    with open(METRICS_FILE) as f:
        return json.load(f)