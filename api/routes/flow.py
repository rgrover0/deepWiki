"""
Flow tracer route — Iteration 16.

POST /flow  {entry_point, repo_id, max_hops}
  → BFS follows CALLS edges from entry method
  → Stops at REPOSITORY boundary or max_hops
  → Returns ordered steps + LLM explanation under 600 tokens
"""

import os
from fastapi import APIRouter
from pydantic import BaseModel
from groq import Groq
from pipeline.graph.schema import get_driver
from dotenv import load_dotenv

load_dotenv()

router     = APIRouter()
_groq      = Groq(api_key=os.getenv("GROQ_API_KEY"))
MAX_CHARS  = 2000   # ~500 tokens, leaving room for prompt overhead

FLOW_PROMPT = """Given these execution flow steps traced from actual code:

{steps}

Explain the flow step by step in plain English.
Reference actual class and method names at each step.
Describe what each step does and how control passes to the next.
Under 300 words."""

_LAYER = {
    "REST_CONTROLLER": "HTTP",
    "CONTROLLER":      "HTTP",
    "SERVICE":         "Service",
    "REPOSITORY":      "Data",
    "ENTITY":          "Data",
    "COMPONENT":       "Component",
    "CONFIGURATION":   "Config",
}


class FlowRequest(BaseModel):
    entry_point: str
    repo_id: str = "spring-petclinic"
    max_hops: int = 6


@router.post("")
def trace_flow(req: FlowRequest):
    driver = get_driver()

    with driver.session() as session:
        # ── find starting methods ─────────────────────────────
        candidates = session.run("""
            MATCH (m:Method)
            WHERE m.name CONTAINS $entry OR m.id CONTAINS $entry
            WITH m
            OPTIONAL MATCH (c:Class)-[:HAS_METHOD]->(m)
            RETURN m.id AS mid, m.name AS mname,
                   c.name AS class_name, c.component_type AS comp_type
            LIMIT 8
        """, entry=req.entry_point).data()

        if not candidates:
            driver.close()
            return {
                "entry_point": req.entry_point,
                "steps":       [],
                "explanation": f"No method found matching '{req.entry_point}'.",
                "token_count": 0,
            }

        # Prefer HTTP-layer entry points
        start = next(
            (m for m in candidates
             if m["comp_type"] in ("CONTROLLER", "REST_CONTROLLER")),
            candidates[0]
        )

        # ── BFS along CALLS edges ─────────────────────────────
        steps:   list[dict] = []
        visited: set        = set()
        queue               = [(start["mid"], 0)]

        while queue:
            mid, depth = queue.pop(0)
            if mid in visited or depth > req.max_hops:
                continue
            visited.add(mid)

            row = session.run("""
                MATCH (m:Method {id: $mid})
                OPTIONAL MATCH (c:Class)-[:HAS_METHOD]->(m)
                RETURN m.name AS name, m.logic_summary AS logic,
                       c.name AS class_name, c.component_type AS comp_type
            """, mid=mid).single()

            if row:
                steps.append({
                    "step":           len(steps) + 1,
                    "depth":          depth,
                    "method_id":      mid,
                    "method_name":    row["name"] or "",
                    "class_name":     row["class_name"] or "",
                    "component_type": row["comp_type"] or "",
                    "layer":          _LAYER.get(row["comp_type"] or "", "Code"),
                    "logic_summary":  row["logic"] or "",
                })
                # Stop at data boundary — don't traverse into DB internals
                if row["comp_type"] == "REPOSITORY":
                    break

            nexts = session.run("""
                MATCH (m:Method {id: $mid})-[r:CALLS]->(called:Method)
                WHERE r.confidence >= 0.9
                RETURN called.id AS nid
                ORDER BY r.line
            """, mid=mid).data()

            for n in nexts:
                if n["nid"] not in visited:
                    queue.append((n["nid"], depth + 1))

    driver.close()

    if not steps:
        return {
            "entry_point": req.entry_point,
            "steps":       [],
            "explanation": "No executable flow found from this entry point. "
                           "CALLS edges may not yet be populated — run Iteration 14.",
            "token_count": 0,
        }

    # ── build context, enforce 600-token ceiling ──────────────
    def _format(ss: list[dict]) -> str:
        return "\n".join(
            f"Step {s['step']} [{s['layer']} · {s['class_name']}.{s['method_name']}()]: "
            f"{s['logic_summary'] or '(no summary)'}"
            for s in ss
        )

    context = _format(steps)
    while len(context) > MAX_CHARS and len(steps) > 1:
        steps   = steps[:-1]
        context = _format(steps)

    # ── LLM explanation ───────────────────────────────────────
    try:
        resp = _groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user",
                       "content": FLOW_PROMPT.format(steps=context)}],
            max_tokens=350,
            temperature=0.2,
        )
        explanation  = resp.choices[0].message.content.strip()
        token_count  = (resp.usage.prompt_tokens or 0) + (resp.usage.completion_tokens or 0)
    except Exception as e:
        explanation = f"LLM error: {e}"
        token_count = 0

    return {
        "entry_point": req.entry_point,
        "steps":       steps,
        "explanation": explanation,
        "token_count": token_count,
    }


@router.get("")
def trace_flow_get(entry_point: str, repo_id: str = "spring-petclinic", max_hops: int = 6):
    """GET variant for quick testing."""
    return trace_flow(FlowRequest(
        entry_point=entry_point, repo_id=repo_id, max_hops=max_hops
    ))
