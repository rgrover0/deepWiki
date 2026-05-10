import time
from fastapi import APIRouter
from pydantic import BaseModel
from pipeline.embeddings.embedder import embed_text
from pipeline.embeddings.vector_store import get_client, semantic_search
from pipeline.graph.schema import get_driver
from pipeline.planner.plan_generator import generate_plan
from pipeline.planner.test_generator import generate_tests
from pipeline.metrics.token_tracker import log_token_usage

router = APIRouter()


class PlanRequest(BaseModel):
    requirement: str
    top_k: int = 5
    generate_tests: bool = True
    test_types: list[str] = ["unit", "integration"]


def build_context(classes: list[dict]) -> str:
    parts = []
    for cls in classes:
        methods = ", ".join(
            m.get("name", "") for m in cls.get("methods", [])[:8]
        )
        fields = ", ".join(
            f"{f.get('name','')}:{f.get('type','')}"
            for f in cls.get("fields", [])[:6]
        )
        parts.append(
            f"[{cls['component_type']}] {cls['name']}\n"
            f"Package: {cls.get('package','')}\n"
            f"Summary: {cls.get('wiki_summary','')}\n"
            f"Methods: {methods}\n"
            f"Fields: {fields}"
        )
    return "\n\n---\n\n".join(parts)


@router.post("/")
def create_plan(req: PlanRequest):
    # 1. Semantic search for relevant classes
    query_vector = embed_text(req.requirement)
    qdrant = get_client()
    search_results = semantic_search(qdrant, query_vector, top_k=req.top_k)

    if not search_results:
        return {"error": "No relevant classes found in wiki."}

    # 2. Fetch full class details from Neo4j
    driver = get_driver()
    classes = []

    with driver.session() as session:
        for r in search_results:
            row = session.run("""
                MATCH (c:Class {name: $name})
                OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
                OPTIONAL MATCH (c)-[:HAS_FIELD]->(f:Field)
                RETURN
                    c.name           AS name,
                    c.component_type AS component_type,
                    c.package        AS package,
                    c.wiki_summary   AS wiki_summary,
                    collect(DISTINCT {name: m.name, return_type: m.return_type}) AS methods,
                    collect(DISTINCT {name: f.name, type: f.type}) AS fields
            """, name=r["name"]).single()

            if row:
                data = dict(row)
                data["methods"] = [m for m in data["methods"] if m["name"]]
                data["fields"]  = [f for f in data["fields"]  if f["name"]]
                data["score"]   = r["score"]
                classes.append(data)

    driver.close()

    # 3. Build context
    context = build_context(classes)

    # 4. Generate implementation plan
    plan_result = generate_plan(req.requirement, context)
    time.sleep(2)  # rate limit buffer

    response = {
        "requirement": req.requirement,
        "relevant_classes": [
            {"name": c["name"], "type": c["component_type"], "score": c["score"]}
            for c in classes
        ],
        "plan": plan_result["plan"],
        "token_usage": {
            "plan": {
                "prompt":  plan_result["prompt_tokens"],
                "output":  plan_result["output_tokens"],
                "total":   plan_result["total_tokens"]
            }
        }
    }

    # 5. Generate test cases
    if req.generate_tests:
        test_result = generate_tests(
            req.requirement,
            plan_result["plan"],
            context
        )
        response["tests"] = test_result["tests"]
        response["token_usage"]["tests"] = {
            "prompt": test_result["prompt_tokens"],
            "output": test_result["output_tokens"],
            "total":  test_result["total_tokens"]
        }

    # 6. Log token usage for metrics
    total = (
        plan_result["total_tokens"] +
        (test_result["total_tokens"] if req.generate_tests else 0)
    )
    log_token_usage(
        query=req.requirement,
        wiki_tokens=total,
        source_files=[c.get("file", "") for c in classes]
    )

    return response