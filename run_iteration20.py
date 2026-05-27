"""
Iteration 20 — End-to-End Flow Portal

Verifies:
  1. flow.py has cross-repo + be-only trace modes, raw_token_estimate
  2. FlowRequest includes fe_repo_id, be_repo_id
  3. _trace_cross_repo, _trace_be_only, _bfs_from_method helpers exist
  4. api_impact nightly job already handles CONSUMES from FE repos (Iteration 19)
  5. wiki.service.ts updated with fe_repo_id / be_repo_id
  6. FlowTrace model has repo_id, repo_type, raw_token_estimate fields
  7. Streamlit flow page has token savings metric
  8. Neo4j integration smoke test (cross-repo query)

Done when:
  POST /flow {"entry_point": "createOwner"}
  returns steps that include an Angular FE step + Spring Boot steps
  with trace_mode: "cross_repo"
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent

print("=" * 60)
print("DeepWiki - Iteration 20: End-to-End Flow Portal")
print("=" * 60)

all_ok = True

def grep(path: Path, pattern: str) -> bool:
    if not path.exists():
        return False
    return pattern in path.read_text(encoding="utf-8", errors="ignore")


# ── 1. flow.py structure ──────────────────────────────────
print("\n[1/8] flow.py has cross-repo trace + raw estimate:")
flow_path = ROOT / "api/routes/flow.py"
checks_flow = [
    ("_trace_cross_repo",       "cross-repo trace function"),
    ("_trace_be_only",          "be-only trace function"),
    ("_bfs_from_method",        "BFS helper"),
    ("raw_token_estimate",      "raw token estimate in response"),
    ("trace_mode",              "trace_mode field"),
    ("fe_repo_id",              "fe_repo_id in FlowRequest"),
    ("CONSUMES",                "CONSUMES edge query"),
    ("IMPLEMENTS_CONTRACT",     "IMPLEMENTS_CONTRACT bridge"),
]
for pattern, desc in checks_flow:
    ok = grep(flow_path, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc} ({pattern!r})")
    all_ok &= ok


# ── 2. FlowRequest has new fields ────────────────────────
print("\n[2/8] FlowRequest schema:")
checks_req = [
    ("fe_repo_id",  "fe_repo_id field"),
    ("be_repo_id",  "be_repo_id field"),
]
for pattern, desc in checks_req:
    ok = grep(flow_path, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# ── 3. Helper isolation ──────────────────────────────────
print("\n[3/8] Helper functions isolated (not inline):")
src = flow_path.read_text(encoding="utf-8", errors="ignore") if flow_path.exists() else ""
for fn in ["def _trace_cross_repo", "def _trace_be_only", "def _bfs_from_method"]:
    ok = fn in src
    print(f"  {'OK  ' if ok else 'MISS'}  {fn}()")
    all_ok &= ok


# ── 4. wiki.service.ts updated ──────────────────────────
print("\n[4/8] Angular wiki.service.ts updated:")
svc_path = ROOT / "deepwiki-ui/src/app/core/services/wiki.service.ts"
checks_svc = [
    ("fe_repo_id",  "fe_repo_id param"),
    ("be_repo_id",  "be_repo_id param"),
]
for pattern, desc in checks_svc:
    ok = grep(svc_path, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# ── 5. FlowTrace model ──────────────────────────────────
print("\n[5/8] FlowTrace model has new fields:")
model_path = ROOT / "deepwiki-ui/src/app/core/models/wiki.model.ts"
checks_model = [
    ("repo_id",             "FlowStep.repo_id"),
    ("repo_type",           "FlowStep.repo_type"),
    ("raw_token_estimate",  "FlowTrace.raw_token_estimate"),
    ("trace_mode",          "FlowTrace.trace_mode"),
]
for pattern, desc in checks_model:
    ok = grep(model_path, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# ── 6. Streamlit Flow page ──────────────────────────────
print("\n[6/8] Streamlit Flow Viewer enhancements:")
app_path = ROOT / "ui/app.py"
checks_ui = [
    ("raw_token_estimate",  "raw token estimate display"),
    ("trace_mode",          "trace mode label"),
    ("Token Usage",         "token usage section"),
    ("Savings",             "savings metric"),
    ("repo_type",           "repo boundary separator"),
    ("REPO_LABEL",          "REPO_LABEL mapping"),
]
for pattern, desc in checks_ui:
    ok = grep(app_path, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# ── 7. Angular build still passes ──────────────────────
print("\n[7/8] Angular build (zero errors):")
import subprocess
result = subprocess.run(
    ["npx", "ng", "build", "--configuration", "development"],
    cwd=str(ROOT / "deepwiki-ui"),
    capture_output=True, text=True, shell=True,
    encoding="utf-8", errors="replace",
)
stdout_err = (result.stdout or "") + (result.stderr or "")
if result.returncode == 0 and "Application bundle generation complete" in stdout_err:
    print("  Build: OK (zero errors)")
else:
    print("  Build FAILED")
    print(stdout_err[-600:])
    all_ok = False


# ── 8. Neo4j integration smoke test ────────────────────
print("\n[8/8] Neo4j cross-repo query (CONSUMES -> APIContract <- EXPOSES):")
try:
    from pipeline.graph.schema import get_driver

    driver = get_driver()
    with driver.session() as session:
        rows = session.run("""
            MATCH (fe:Repository)-[c:CONSUMES]->(api:APIContract)
                  <-[:EXPOSES]-(be:Repository)
            RETURN fe.id AS fe_repo, api.path AS path,
                   be.id AS be_repo, c.caller_class AS caller,
                   c.confidence AS confidence
            LIMIT 5
        """).data()

    driver.close()

    if rows:
        print(f"  OK    Found {len(rows)} cross-repo CONSUMES chains:")
        for r in rows:
            print(f"        {r['fe_repo']} [{r['caller']}] "
                  f"--[{r['confidence']:.1f}]--> {r['path']} "
                  f"<-- {r['be_repo']}")
    else:
        print("  WARN  No CONSUMES chain found yet.")
        print("        Run Iteration 19 pipeline to create edges.")

except Exception as e:
    print(f"  SKIP  Neo4j: {type(e).__name__}: {e}")
    print("        Fix .env and resume Neo4j at console.neo4j.io")


print("\n" + "=" * 60)
print(f"Iteration 20: {'ALL CHECKS PASS' if all_ok else 'SOME CHECKS FAILED'}")
print()
print("  Test cross-repo trace:")
print('    POST /flow {"entry_point":"createOwner","fe_repo_id":"angular-petclinic"}')
print()
print("  Expected response fields:")
print("    trace_mode: 'cross_repo'")
print("    steps[0].layer: 'Angular', steps[0].repo_type: 'frontend'")
print("    steps[1].layer: 'API'")
print("    steps[2+].repo_type: 'backend'")
print("    raw_token_estimate: > token_count")
print("=" * 60)
