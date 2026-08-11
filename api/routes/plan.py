from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.pipeline_gateway import PipelineGatewayError, run_cli

router = APIRouter()


class PlanRequest(BaseModel):
    requirement: str
    top_k: int = 5
    generate_tests: bool = True
    test_types: list[str] = ["unit", "integration"]


@router.post("")
def create_plan(req: PlanRequest):
    try:
        return run_cli(
            "plan",
            payload=req.model_dump(),
            timeout=600,
        )
    except PipelineGatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
