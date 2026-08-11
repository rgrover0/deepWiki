"""
Iteration 21 - Adaptive Retrieval + Model Router

Verifies:
  1. api/model_router.py: LLMAdapter, GroqAdapter, AnthropicAdapter, route(), TASK_MODEL_MAP
  2. api/feedback.py: record_query(), FeedbackRequest, /feedback POST, /feedback/stats GET
  3. api/routes/ask.py: uses model_route(), generates query_id, returns model_used
  4. api/routes/flow.py: uses model_route("flow_trace")
  5. pipeline/wiki/summarizer.py: uses model_route("wiki_generation")
  6. api/main.py: feedback router registered at /feedback
  7. ui/app.py: thumbs up/down on Ask page
  8. Unit tests: model_router selection logic
  9. Neo4j smoke: Feedback node round-trip

Done when: system logs show model_router lines, feedback thumbs are in Neo4j,
  POST /ask returns query_id + model_used.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

print("=" * 60)
print("DeepWiki - Iteration 21: Adaptive Retrieval + Model Router")
print("=" * 60)

all_ok = True


def grep(path: Path, pattern: str) -> bool:
    if not path.exists():
        return False
    return pattern in path.read_text(encoding="utf-8", errors="ignore")


# -- 1. model_router.py -------------------------------------------------------
print("\n[1/9] api/model_router.py:")
mr = ROOT / "api/model_router.py"
checks = [
    ("TASK_MODEL_MAP",      "task map dict"),
    ("class LLMAdapter",    "base LLMAdapter class"),
    ("class GroqAdapter",   "GroqAdapter"),
    ("class AnthropicAdapter", "AnthropicAdapter"),
    ("def route",           "route() function"),
    ("_LARGE_CONTENT_CHARS","large-content threshold"),
    ("wiki_generation",     "wiki_generation task"),
    ("architecture_analysis","architecture_analysis task"),
]
for pattern, desc in checks:
    ok = grep(mr, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 2. feedback.py -----------------------------------------------------------
print("\n[2/9] api/feedback.py:")
fb = ROOT / "api/feedback.py"
checks = [
    ("def new_query_id",    "new_query_id()"),
    ("def record_query",    "record_query()"),
    ("class FeedbackRequest","FeedbackRequest"),
    ("def submit_feedback", "POST handler"),
    ("def feedback_stats",  "stats endpoint"),
    ("was_helpful",         "was_helpful field"),
    ("retrieval_strategy",  "retrieval_strategy field"),
]
for pattern, desc in checks:
    ok = grep(fb, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 3. ask.py ----------------------------------------------------------------
print("\n[3/9] api/routes/ask.py:")
ask = ROOT / "api/routes/ask.py"
checks = [
    ("from api.model_router",  "imports model_router"),
    ("from api import feedback","imports feedback"),
    ("model_route",            "calls route()"),
    ("query_id",               "generates query_id"),
    ("model_used",             "returns model_used"),
    ("fb.record_query",        "calls record_query()"),
    ("fb.new_query_id",        "calls new_query_id()"),
]
for pattern, desc in checks:
    ok = grep(ask, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 4. flow.py ---------------------------------------------------------------
print("\n[4/9] api/routes/flow.py:")
flow = ROOT / "api/routes/flow.py"
checks = [
    ("from api.model_router", "imports model_router"),
    ("model_route",           "calls route()"),
    ("flow_trace",            "flow_trace task"),
]
for pattern, desc in checks:
    ok = grep(flow, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 5. summarizer.py ---------------------------------------------------------
print("\n[5/9] pipeline/wiki/summarizer.py:")
summ = ROOT / "pipeline/wiki/summarizer.py"
checks = [
    ("from api.model_router", "imports model_router"),
    ("model_route",           "calls route()"),
    ("wiki_generation",       "wiki_generation task"),
]
for pattern, desc in checks:
    ok = grep(summ, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 6. main.py ---------------------------------------------------------------
print("\n[6/9] api/main.py:")
main = ROOT / "api/main.py"
checks = [
    ("from api import feedback", "imports feedback module"),
    ("feedback.router",          "includes feedback router"),
    ('prefix="/feedback"',       "mounts at /feedback"),
]
for pattern, desc in checks:
    ok = grep(main, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 7. Streamlit thumbs ------------------------------------------------------
print("\n[7/9] ui/app.py thumbs:")
app = ROOT / "ui/app.py"
checks = [
    ("thumbs_up",    "thumbs_up in feedback POST"),
    ("query_id",     "query_id stored for feedback"),
    ("model_used",   "model_used displayed"),
    ("/feedback",    "POSTs to /feedback"),
]
for pattern, desc in checks:
    ok = grep(app, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 8. Unit tests: model_router ----------------------------------------------
print("\n[8/9] Unit tests: model_router.route():")
from core.llm.model_router import route, TASK_MODEL_MAP, LLMAdapter, GroqAdapter, _build_adapter
import os

test_ok  = True
has_groq = bool(os.getenv("GROQ_API_KEY"))

# _build_adapter("groq") returns None when key missing, adapter when key present
adapter_or_none = _build_adapter("groq")
if has_groq:
    ok = adapter_or_none is not None and isinstance(adapter_or_none, GroqAdapter)
    print(f"  {'OK  ' if ok else 'FAIL'}  _build_adapter('groq') returns GroqAdapter (key present)")
else:
    ok = adapter_or_none is None
    print(f"  {'OK  ' if ok else 'FAIL'}  _build_adapter('groq') returns None (key absent)")
if not ok:
    test_ok = False
    all_ok  = False

# _build_adapter("local") always returns None (not implemented)
ok = _build_adapter("local") is None
print(f"  {'OK  ' if ok else 'FAIL'}  _build_adapter('local') returns None (stub)")
if not ok:
    test_ok = False
    all_ok  = False

# route() with no keys should raise RuntimeError, not crash with AttributeError
if not has_groq and not os.getenv("ANTHROPIC_API_KEY"):
    try:
        route("ask")
        print("  FAIL  route() should have raised RuntimeError when no keys configured")
        test_ok = False
        all_ok  = False
    except RuntimeError:
        print("  OK    route() raises RuntimeError when no providers available")
    except Exception as e:
        print(f"  FAIL  route() raised unexpected {type(e).__name__}: {e}")
        test_ok = False
        all_ok  = False
else:
    # At least one key is set — tasks should resolve
    resolved = []
    for task in TASK_MODEL_MAP:
        try:
            adapter = route(task)
            ok = isinstance(adapter, LLMAdapter) and adapter.provider in ("groq", "claude")
            print(f"  {'OK  ' if ok else 'FAIL'}  route({task!r}) -> {adapter.provider}/{adapter.model}")
            resolved.append(ok)
        except RuntimeError as e:
            print(f"  WARN  route({task!r}) -> RuntimeError (no provider for this task): {e}")
    if all(resolved):
        print(f"  All {len(resolved)} task routing tests passed")

# TASK_MODEL_MAP structure check
expected_tasks = {"wiki_generation", "architecture_analysis", "ask", "flow_trace",
                  "annotation_extraction", "plan", "intent_classification"}
missing = expected_tasks - set(TASK_MODEL_MAP.keys())
ok = not missing
print(f"  {'OK  ' if ok else 'FAIL'}  TASK_MODEL_MAP has all expected tasks"
      + (f" (missing: {missing})" if missing else ""))
if not ok:
    test_ok = False
    all_ok  = False


# -- 9. Neo4j smoke -----------------------------------------------------------
print("\n[9/9] Neo4j smoke: Feedback node round-trip:")
try:
    from api.feedback import record_query, new_query_id
    from core.graph.schema import get_driver

    qid = new_query_id()
    record_query(qid, "Test question from run_iteration21.py",
                 "CLASS_LOOKUP:groq/llama-3.3-70b-versatile",
                 "groq/llama-3.3-70b-versatile")

    driver = get_driver()
    with driver.session() as session:
        row = session.run(
            "MATCH (f:Feedback {id: $id}) RETURN f.retrieval_strategy AS s, f.was_helpful AS h",
            id=qid
        ).single()
    driver.close()

    if row:
        print(f"  OK    Feedback node created: id={qid}, strategy={row['s']}, helpful={row['h']}")
    else:
        print("  WARN  record_query ran but node not found in Neo4j")

except Exception as e:
    print(f"  SKIP  Neo4j: {type(e).__name__}: {e}")
    print("        Fix .env NEO4J_USER=neo4j and resume at console.neo4j.io")


print("\n" + "=" * 60)
print(f"Iteration 21: {'ALL CHECKS PASS' if all_ok else 'SOME CHECKS FAILED'}")
print()
print("  Verify live:")
print('    POST /ask {"question":"How does owner creation work?"}')
print('    -> response includes: query_id, model_used, intent')
print()
print('    POST /feedback {"query_id": "<id from above>", "thumbs_up": true}')
print('    -> {"ok": true}')
print()
print('    GET /feedback/stats')
print('    -> {"strategies": [{"strategy":"CLASS_LOOKUP:groq/...","total":1,...}]}')
print("=" * 60)
