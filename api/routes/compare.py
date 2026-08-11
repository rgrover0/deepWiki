import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.pipeline_gateway import PipelineGatewayError, run_cli

router = APIRouter()
LOG_FILE = "output/metrics/comparison_log.json"
os.makedirs("output/metrics", exist_ok=True)


class CompareRequest(BaseModel):
    query: str
    top_k: int = 4
    model: str = "claude-sonnet-4-6"
    mode: str = "groq"


@router.post("")
def run_comparison(req: CompareRequest):
    try:
        return run_cli(
            "compare",
            payload=req.model_dump(),
            timeout=600,
        )
    except PipelineGatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/models")
def list_models():
    return {"models": ["groq", "claude-sonnet-4-6"]}


@router.get("/health")
def compare_health():
    return {"status": "ok"}


@router.get("/history")
def comparison_history():
    import json

    if not os.path.exists(LOG_FILE):
        return {"entries": []}
    with open(LOG_FILE, encoding="utf-8") as f:
        return {"entries": json.load(f)}
