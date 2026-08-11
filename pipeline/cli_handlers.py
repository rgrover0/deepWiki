"""CLI handlers for synchronous pipeline commands invoked via subprocess."""

from __future__ import annotations

import json
import os
import time
from typing import Any


def run_plan(payload: dict[str, Any]) -> dict[str, Any]:
    from core.embeddings.embedder import embed_text
    from core.embeddings.vector_store import get_client, semantic_search
    from core.graph.schema import get_driver
    from pipeline.metrics.token_tracker import log_token_usage
    from pipeline.planner.plan_generator import generate_plan
    from pipeline.planner.test_generator import generate_tests

    requirement = payload["requirement"]
    top_k = int(payload.get("top_k", 5))
    do_tests = bool(payload.get("generate_tests", True))

    query_vector = embed_text(requirement)
    qdrant = get_client()
    search_results = semantic_search(qdrant, query_vector, top_k=top_k)
    if not search_results:
        return {"error": "No relevant classes found in wiki."}

    driver = get_driver()
    classes: list[dict] = []
    try:
        with driver.session() as session:
            for r in search_results:
                if r.get("repo_id"):
                    row = session.run(
                        """
                        MATCH (c:Class {repo_id: $repo_id, name: $name})
                        OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
                        OPTIONAL MATCH (c)-[:HAS_FIELD]->(f:Field)
                        RETURN
                            c.name           AS name,
                            c.component_type AS component_type,
                            c.package        AS package,
                            c.wiki_summary   AS wiki_summary,
                            collect(DISTINCT {name: m.name, return_type: m.return_type}) AS methods,
                            collect(DISTINCT {name: f.name, type: f.type}) AS fields
                        """,
                        repo_id=r["repo_id"],
                        name=r["name"],
                    ).single()
                else:
                    row = session.run(
                        """
                        MATCH (c:Class {name: $name})
                        WITH c ORDER BY c.repo_id
                        LIMIT 1
                        OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
                        OPTIONAL MATCH (c)-[:HAS_FIELD]->(f:Field)
                        RETURN
                            c.name           AS name,
                            c.component_type AS component_type,
                            c.package        AS package,
                            c.wiki_summary   AS wiki_summary,
                            collect(DISTINCT {name: m.name, return_type: m.return_type}) AS methods,
                            collect(DISTINCT {name: f.name, type: f.type}) AS fields
                        """,
                        name=r["name"],
                    ).single()
                if row:
                    data = dict(row)
                    data["methods"] = [m for m in data["methods"] if m["name"]]
                    data["fields"] = [f for f in data["fields"] if f["name"]]
                    data["score"] = r["score"]
                    classes.append(data)
    finally:
        driver.close()

    parts = []
    for cls in classes:
        methods = ", ".join(m.get("name", "") for m in cls.get("methods", [])[:8])
        fields = ", ".join(
            f"{f.get('name','')}:{f.get('type','')}" for f in cls.get("fields", [])[:6]
        )
        parts.append(
            f"[{cls['component_type']}] {cls['name']}\n"
            f"Package: {cls.get('package','')}\n"
            f"Summary: {cls.get('wiki_summary','')}\n"
            f"Methods: {methods}\n"
            f"Fields: {fields}"
        )
    context = "\n\n---\n\n".join(parts)

    plan_result = generate_plan(requirement, context)
    time.sleep(2)

    response: dict[str, Any] = {
        "requirement": requirement,
        "relevant_classes": [
            {"name": c["name"], "type": c["component_type"], "score": c["score"]}
            for c in classes
        ],
        "plan": plan_result["plan"],
        "token_usage": {
            "plan": {
                "prompt": plan_result["prompt_tokens"],
                "output": plan_result["output_tokens"],
                "total": plan_result["total_tokens"],
            }
        },
    }

    test_tokens = 0
    if do_tests:
        test_result = generate_tests(requirement, plan_result["plan"], context)
        response["tests"] = test_result["tests"]
        response["token_usage"]["tests"] = {
            "prompt": test_result["prompt_tokens"],
            "output": test_result["output_tokens"],
            "total": test_result["total_tokens"],
        }
        test_tokens = test_result["total_tokens"]

    log_token_usage(
        query=requirement,
        wiki_tokens=plan_result["total_tokens"] + test_tokens,
        source_files=[c.get("file", "") for c in classes],
    )
    return response


def run_compare(payload: dict[str, Any]) -> dict[str, Any]:
    from pipeline.comparison.runner import compare as groq_compare

    query = payload["query"]
    top_k = int(payload.get("top_k", 4))
    mode = payload.get("mode", "groq")
    model = payload.get("model", "claude-sonnet-4-6")

    if mode == "groq":
        result = groq_compare(query, top_k)
    else:
        try:
            from pipeline.comparison.claude_runner import MODELS, run_full_comparison
        except Exception as exc:
            return {"error": f"Claude runner not available: {exc}"}
        if mode == "claude":
            result = run_full_comparison(query, top_k=top_k, models=[model])
        else:
            result = run_full_comparison(query, top_k=top_k, models=list(MODELS.keys()))

    log_file = "output/metrics/comparison_log.json"
    os.makedirs("output/metrics", exist_ok=True)
    log = []
    if os.path.exists(log_file):
        with open(log_file, encoding="utf-8") as f:
            log = json.load(f)
    log.append({"query": query, "mode": mode, "result": result, "ts": time.time()})
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    return result if isinstance(result, dict) else {"result": result}
