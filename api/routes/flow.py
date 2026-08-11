"""
Flow tracer route — updated Iteration 20.

Supports two trace modes:
  1. BE-only  — BFS along CALLS edges starting from a Spring Boot method
  2. Cross-repo — Angular FE → APIContract → Spring Boot → Repository

POST /flow  {entry_point, fe_repo_id, be_repo_id, max_hops}

Cross-repo trace:
  (FE Service method)
      -[:CONSUMES]-> (APIContract)
      <-[:IMPLEMENTS_CONTRACT]- (Controller)
      -[:CALLS]->* (Service → Repository)

Each step carries repo_id and repo_type so the UI can color-code layers.
Token ceiling: 600 tokens (2000 chars).  Raw estimate added to response.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from core.graph.schema import get_driver
from core.llm.model_router import route as model_route
from dotenv import load_dotenv

load_dotenv()

router    = APIRouter()
MAX_CHARS = 2000   # ~500 tokens; leaves headroom for the prompt wrapper

# Tokens-per-file baseline used to estimate raw retrieval cost
_TOKENS_PER_FILE = 1_800

_LAYER = {
    "REST_CONTROLLER": "HTTP",
    "CONTROLLER":      "HTTP",
    "SERVICE":         "Service",
    "REPOSITORY":      "Data",
    "ENTITY":          "Data",
    "COMPONENT":       "Angular",
    "SERVICE_TS":      "Angular",
    "CONFIGURATION":   "Config",
}

FLOW_PROMPT = """Given these execution flow steps traced from actual code (spanning Angular frontend through Spring Boot backend):

{steps}

Explain the end-to-end flow step by step in plain English.
Reference actual class and method names at each step.
Describe what each step does, which layer it belongs to, and how control passes to the next.
Under 300 words."""


class FlowRequest(BaseModel):
    entry_point: str
    fe_repo_id:  str = "angular-petclinic"
    be_repo_id:  str = "spring-petclinic"
    max_hops:    int = 8


# ── BFS helper ─────────────────────────────────────────────────────────────────

def _bfs_from_method(session, start_mid: str, max_hops: int,
                     step_offset: int, repo_id: str) -> list[dict]:
    """
    BFS along CALLS edges from start_mid.
    Returns ordered list of step dicts with repo_id attached.
    Stops at REPOSITORY boundary.
    """
    steps: list[dict] = []
    visited: set      = set()
    queue             = [(start_mid, 0)]

    while queue:
        mid, depth = queue.pop(0)
        if mid in visited or depth > max_hops:
            continue
        visited.add(mid)

        row = session.run("""
            MATCH (m:Method {id: $mid})
            OPTIONAL MATCH (c:Class)-[:HAS_METHOD]->(m)
            RETURN m.name AS name, m.logic_summary AS logic,
                   c.name AS class_name, c.component_type AS comp_type
        """, mid=mid).single()

        if row:
            comp_type = row["comp_type"] or ""
            steps.append({
                "step":           step_offset + len(steps) + 1,
                "layer":          _LAYER.get(comp_type, "Code"),
                "method_id":      mid,
                "method_name":    row["name"] or "",
                "class_name":     row["class_name"] or "",
                "component_type": comp_type,
                "logic_summary":  row["logic"] or "",
                "repo_id":        repo_id,
                "repo_type":      "backend",
            })
            if comp_type == "REPOSITORY":
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

    return steps


def _format_steps(steps: list[dict]) -> str:
    return "\n".join(
        f"Step {s['step']} [{s['layer']} · {s['class_name']}.{s['method_name']}()] "
        f"({s.get('repo_id', '')}): {s['logic_summary'] or '(no summary)'}"
        for s in steps
    )


def _raw_token_estimate(steps: list[dict]) -> int:
    """
    Rough estimate of tokens if raw source files were loaded instead.
    Counts distinct (repo, class) pairs × tokens-per-file.
    """
    unique_files = {(s.get("repo_id", ""), s["class_name"]) for s in steps}
    # Add overhead for Angular files bridged via CONSUMES
    fe_steps = [s for s in steps if s.get("repo_type") == "frontend"]
    unique_files |= {("angular", s["class_name"]) for s in fe_steps}
    return max(3_000, len(unique_files) * _TOKENS_PER_FILE)


# ── Cross-repo trace ────────────────────────────────────────────────────────────

def _trace_cross_repo(session, entry: str, fe_repo_id: str,
                      be_repo_id: str, max_hops: int) -> list[dict]:
    """
    Attempt a full FE→BE trace.
    Returns [] if no CONSUMES edge matches.
    """
    # Match by caller_class or caller_method containing entry keyword
    fe_rows = session.run("""
        MATCH (fe:Repository {id: $fe_repo_id})-[c:CONSUMES]->(a:APIContract)
        WHERE toLower(c.caller_class)  CONTAINS toLower($entry)
           OR toLower(c.caller_method) CONTAINS toLower($entry)
        RETURN c.caller_class    AS fe_class,
               c.caller_method   AS fe_method,
               a.id              AS contract_id,
               a.http_method     AS http_method,
               a.path            AS path,
               a.controller_class AS be_class
        ORDER BY c.confidence DESC
        LIMIT 1
    """, fe_repo_id=fe_repo_id, entry=entry).data()

    if not fe_rows:
        return []

    m    = fe_rows[0]
    steps: list[dict] = []

    # ── Step 1: Angular FE method ───────────────────────────
    steps.append({
        "step":           1,
        "layer":          "Angular",
        "class_name":     m["fe_class"] or "AngularService",
        "method_name":    m["fe_method"] or "call",
        "component_type": "SERVICE",
        "logic_summary":  f"Calls {m['http_method']} {m['path']} on the backend API",
        "repo_id":        fe_repo_id,
        "repo_type":      "frontend",
    })

    # ── Step 2: API Contract boundary ──────────────────────
    steps.append({
        "step":           2,
        "layer":          "API",
        "class_name":     "APIContract",
        "method_name":    f"{m['http_method']} {m['path']}",
        "component_type": "CONTRACT",
        "logic_summary":  f"REST boundary — {m['http_method']} {m['path']}",
        "repo_id":        None,
        "repo_type":      "contract",
    })

    # ── Step 3+: BE controller via IMPLEMENTS_CONTRACT ─────
    be_start = session.run("""
        MATCH (cls:Class)-[:IMPLEMENTS_CONTRACT]->(a:APIContract {id: $contract_id})
        WITH cls
        MATCH (cls)-[:HAS_METHOD]->(m:Method)
        RETURN m.id AS mid
        LIMIT 1
    """, contract_id=m["contract_id"]).single()

    if be_start:
        be_steps = _bfs_from_method(
            session,
            start_mid   = be_start["mid"],
            max_hops    = max_hops - 2,
            step_offset = 2,
            repo_id     = be_repo_id,
        )
        steps.extend(be_steps)

    return steps


# ── BE-only trace ────────────────────────────────────────────────────────────

def _trace_be_only(session, entry: str, be_repo_id: str,
                   max_hops: int) -> list[dict]:
    """
    Original BFS from a Spring Boot method entry point.
    Prefers HTTP-layer candidates.
    """
    candidates = session.run("""
        MATCH (m:Method)
        WHERE m.name CONTAINS $entry OR m.id CONTAINS $entry
        WITH m
        OPTIONAL MATCH (c:Class)-[:HAS_METHOD]->(m)
        RETURN m.id AS mid, c.component_type AS comp_type
        LIMIT 8
    """, entry=entry).data()

    if not candidates:
        return []

    start = next(
        (c for c in candidates if c["comp_type"] in ("CONTROLLER", "REST_CONTROLLER")),
        candidates[0],
    )

    return _bfs_from_method(
        session,
        start_mid   = start["mid"],
        max_hops    = max_hops,
        step_offset = 0,
        repo_id     = be_repo_id,
    )


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("")
def trace_flow(req: FlowRequest):
    driver = get_driver()
    steps: list[dict] = []

    with driver.session() as session:
        # Try cross-repo first (FE → BE)
        steps = _trace_cross_repo(
            session, req.entry_point, req.fe_repo_id, req.be_repo_id, req.max_hops
        )
        # Fall back to BE-only BFS
        if not steps:
            steps = _trace_be_only(session, req.entry_point, req.be_repo_id, req.max_hops)

    driver.close()

    if not steps:
        return {
            "entry_point": req.entry_point,
            "steps":       [],
            "explanation": (
                f"No flow found for '{req.entry_point}'. "
                "Run Iteration 14 to populate CALLS edges; "
                "run Iteration 19 to populate CONSUMES edges."
            ),
            "token_count":     0,
            "raw_token_estimate": 0,
            "trace_mode":     "none",
        }

    trace_mode = (
        "cross_repo"
        if any(s.get("repo_type") == "frontend" for s in steps)
        else "be_only"
    )

    # ── Enforce 600-token ceiling on context ──────────────────
    context = _format_steps(steps)
    while len(context) > MAX_CHARS and len(steps) > 1:
        steps   = steps[:-1]
        context = _format_steps(steps)

    raw_estimate = _raw_token_estimate(steps)

    # ── LLM explanation ───────────────────────────────────────
    prompt  = FLOW_PROMPT.format(steps=context)
    adapter = model_route("flow_trace", content_size=len(prompt))
    try:
        explanation, token_count = adapter.complete(prompt, max_tokens=350, temperature=0.2)
    except Exception as e:
        explanation = f"LLM error: {e}"
        token_count = 0

    return {
        "entry_point":        req.entry_point,
        "steps":              steps,
        "explanation":        explanation,
        "token_count":        token_count,
        "raw_token_estimate": raw_estimate,
        "trace_mode":         trace_mode,
    }


@router.get("")
def trace_flow_get(entry_point: str, fe_repo_id: str = "angular-petclinic",
                   be_repo_id: str = "spring-petclinic", max_hops: int = 8):
    """GET variant for quick testing."""
    return trace_flow(FlowRequest(
        entry_point=entry_point,
        fe_repo_id=fe_repo_id,
        be_repo_id=be_repo_id,
        max_hops=max_hops,
    ))
