import json
import os
import time
from fastapi import APIRouter
from pydantic import BaseModel
from pipeline.comparison.runner import compare as groq_compare

# Optional — only loads if claude_runner.py exists and keys are set
try:
    from pipeline.comparison.claude_runner import (
        run_full_comparison,
        MODELS
    )
    CLAUDE_AVAILABLE = True
except Exception as e:
    CLAUDE_AVAILABLE = False
    MODELS = {}
    print(f"⚠️  Claude runner not available: {e}")

router   = APIRouter()
LOG_FILE = "output/metrics/comparison_log.json"
os.makedirs("output/metrics", exist_ok=True)


class CompareRequest(BaseModel):
    query:  str
    top_k:  int = 4
    model:  str = "claude-sonnet-4-6"
    mode:   str = "groq"


def _save_log(entry: dict):
    log = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            log = json.load(f)
    log.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


@router.post("/")
def run_comparison(req: CompareRequest):
    if req.mode == "groq":
        result = groq_compare(req.query, req.top_k)

    elif req.mode in ("claude", "all"):
        if not CLAUDE_AVAILABLE:
            return {
                "error": "Claude runner not available. "
                         "Check ANTHROPIC_RAW_KEY, "
                         "ANTHROPIC_WIKI_KEY, "
                         "ANTHROPIC_CACHE_KEY in .env"
            }
        if req.mode == "claude":
            result = run_full_comparison(req.query, req.top_k, req.model)
        else:
            groq_result   = groq_compare(req.query, req.top_k)
            time.sleep(3)
            claude_result = run_full_comparison(req.query, req.top_k, req.model)
            result = {
                "query":  req.query,
                "model":  req.model,
                "groq":   groq_result,
                "claude": claude_result
            }
    else:
        return {"error": f"Unknown mode: {req.mode}"}

    _save_log(result)
    return result


@router.get("/models")
def get_models():
    return MODELS


@router.get("/health")
def compare_health():
    return {
        "groq_available":   True,
        "claude_available": CLAUDE_AVAILABLE
    }


@router.get("/history")
def get_history():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE) as f:
        return json.load(f)


@router.delete("/history")
def clear_history():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    return {"cleared": True}