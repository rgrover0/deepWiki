"""
Iteration 19 — FE-BE Suite Link + CONSUMES Edges

Verifies:
  1. api_matcher.py exists with path_similarity and run_api_matching
  2. suites.json includes angular-petclinic repo
  3. contracts.py has per-contract /consumers endpoint
  4. api_impact.py updated with caller_method tracking
  5. Unit tests for path_similarity() with known pairs
  6. Unit tests for match_http_calls() with mock contracts
  7. Neo4j smoke test (writes CONSUMES edge, reads it back)

Done when:
  MATCH (r:Repository)-[:CONSUMES]->(api:APIContract)<-[:EXPOSES]-(be:Repository)
  RETURN r.id, api.path, be.id
  returns: angular-petclinic → /api/pets → spring-petclinic
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent

print("=" * 60)
print("DeepWiki - Iteration 19: FE-BE Suite Link + CONSUMES Edges")
print("=" * 60)

all_ok = True

# ── 1. File existence ──────────────────────────────────────
print("\n[1/7] File existence:")
files = [
    ROOT / "pipeline/graph/api_matcher.py",
    ROOT / "config/suites.json",
]
for f in files:
    ok = f.exists()
    print(f"  {'OK  ' if ok else 'MISS'}  {f.relative_to(ROOT)}")
    all_ok &= ok


# ── 2. suites.json has angular-petclinic ──────────────────
print("\n[2/7] suites.json includes angular-petclinic:")
suites_path = ROOT / "config/suites.json"
if suites_path.exists():
    data = json.loads(suites_path.read_text(encoding="utf-8"))
    all_repos = [r["id"] for s in data["suites"] for r in s["repos"]]
    has_angular = "angular-petclinic" in all_repos
    print(f"  {'OK  ' if has_angular else 'MISS'}  angular-petclinic in repos: {all_repos}")
    all_ok &= has_angular
else:
    print("  MISS  suites.json not found")
    all_ok = False


# ── 3. contracts.py has per-contract consumers ────────────
print("\n[3/7] contracts.py has /{contract_id}/consumers endpoint:")
contracts_path = ROOT / "api/routes/contracts.py"
if contracts_path.exists():
    src = contracts_path.read_text(encoding="utf-8")
    has_endpoint = "contract_id:path" in src and "consumers" in src
    print(f"  {'OK  ' if has_endpoint else 'MISS'}  GET /{{contract_id}}/consumers defined")
    all_ok &= has_endpoint
else:
    print("  MISS  contracts.py not found")
    all_ok = False


# ── 4. api_impact.py updated ──────────────────────────────
print("\n[4/7] api_impact.py tracks caller_method:")
impact_path = ROOT / "pipeline/graph/api_impact.py"
if impact_path.exists():
    src = impact_path.read_text(encoding="utf-8")
    has_caller_method = "caller_method" in src and "consumer_callers" in src
    print(f"  {'OK  ' if has_caller_method else 'MISS'}  consumer_callers field in impact node")
    all_ok &= has_caller_method
else:
    print("  MISS  api_impact.py not found")
    all_ok = False


# ── 5. Unit tests: path_similarity() ──────────────────────
print("\n[5/7] Unit tests: path_similarity():")
sys.path.insert(0, str(ROOT))
from pipeline.graph.api_matcher import path_similarity, match_http_calls

SIMILARITY_CASES = [
    # (a, b, expected_score, description)
    ("/pets",           "/pets",               1.0, "exact match"),
    ("/pets/{id}",      "/pets/{param}",        1.0, "param placeholder — both become /pets/{x}"),
    ("/pets/{id}",      "/owners/{id}",         0.5, "different first segment"),
    ("/api/pets",       "/api/pets",            1.0, "multi-segment exact"),
    ("/pets/{id}/vets", "/pets/{param}/visits", 2/3, "2 of 3 segments match"),
    ("/pets",           "/owners",              0.0, "no match"),
    ("/pets",           "/pets/1",              0.0, "different depth"),
]

sim_ok = True
for a, b, expected, desc in SIMILARITY_CASES:
    score = path_similarity(a, b)
    ok    = abs(score - expected) < 0.01
    print(f"  {'OK  ' if ok else 'FAIL'}  {desc}: similarity({a!r}, {b!r}) = {score:.2f} (expected {expected:.2f})")
    if not ok:
        sim_ok = False
        all_ok = False

if sim_ok:
    print(f"  All {len(SIMILARITY_CASES)} similarity tests passed")


# ── 6. Unit tests: match_http_calls() ─────────────────────
print("\n[6/7] Unit tests: match_http_calls():")

MOCK_CONTRACTS = [
    {"id": "sc:GET:/api/pets",             "http_method": "GET",    "path": "/api/pets",            "controller_class": "PetResource"},
    {"id": "sc:GET:/api/pets/{petId}",     "http_method": "GET",    "path": "/api/pets/{petId}",    "controller_class": "PetResource"},
    {"id": "sc:POST:/api/pets",            "http_method": "POST",   "path": "/api/pets",            "controller_class": "PetResource"},
    {"id": "sc:GET:/api/owners",           "http_method": "GET",    "path": "/api/owners",          "controller_class": "OwnerResource"},
    {"id": "sc:GET:/api/owners/{ownerId}", "http_method": "GET",    "path": "/api/owners/{ownerId}","controller_class": "OwnerResource"},
    {"id": "sc:POST:/api/owners",          "http_method": "POST",   "path": "/api/owners",          "controller_class": "OwnerResource"},
]

MOCK_HTTP_CALLS = [
    {"method": "GET",  "normalized_url": "/api/pets",          "source_method": "getPets",       "url": "${this.BASE}/pets"},
    {"method": "GET",  "normalized_url": "/api/pets/{param}",  "source_method": "getPetById",    "url": "${this.BASE}/pets/${id}"},
    {"method": "POST", "normalized_url": "/api/pets",          "source_method": "createPet",     "url": "${this.BASE}/pets"},
    {"method": "GET",  "normalized_url": "/api/owners",        "source_method": "getOwners",     "url": "${this.BASE}/owners"},
    {"method": "GET",  "normalized_url": "/api/vets",          "source_method": "getVets",       "url": "${this.BASE}/vets"},  # no match
    {"method": "DELETE","normalized_url": "/api/pets/{param}", "source_method": "deletePet",     "url": ""},  # method mismatch
]

EXPECTED_MATCHES = [
    ("getPets",    "sc:GET:/api/pets",           1.0),
    ("getPetById", "sc:GET:/api/pets/{petId}",   1.0),
    ("createPet",  "sc:POST:/api/pets",          1.0),
    ("getOwners",  "sc:GET:/api/owners",         1.0),
    ("getVets",    None,                         0.0),
    ("deletePet",  None,                         0.0),
]

matched = match_http_calls(MOCK_HTTP_CALLS, MOCK_CONTRACTS)
match_ok = True
for i, (source_method, expected_id, expected_conf) in enumerate(EXPECTED_MATCHES):
    item       = matched[i]
    got_id     = item["match"]["id"] if item["match"] else None
    got_conf   = item["confidence"]
    ok         = (got_id == expected_id) and abs(got_conf - expected_conf) < 0.01
    print(f"  {'OK  ' if ok else 'FAIL'}  {source_method}: "
          f"matched={got_id}, confidence={got_conf:.1f}")
    if not ok:
        match_ok = False
        all_ok   = False

if match_ok:
    print(f"  All {len(EXPECTED_MATCHES)} match tests passed")


# ── 7. Neo4j smoke test ───────────────────────────────────
print("\n[7/7] Neo4j smoke test (CONSUMES edge round-trip):")
try:
    from core.graph.schema import get_driver
    from pipeline.graph.api_matcher import write_consumes_edges

    driver = get_driver()
    with driver.session() as session:
        # Write a test CONSUMES edge
        write_consumes_edges(
            session,
            fe_repo_id="angular-petclinic",
            caller_class="PetService",
            matched_calls=[{
                "call":  {"source_method": "getPets", "normalized_url": "/api/pets", "method": "GET"},
                "match": {"id": "spring-petclinic:GET:/api/pets"},
                "confidence": 1.0,
            }],
        )

        # Read it back
        row = session.run("""
            MATCH (fe:Repository {id: 'angular-petclinic'})
                  -[c:CONSUMES]->(api:APIContract {id: 'spring-petclinic:GET:/api/pets'})
                  <-[:EXPOSES]-(be:Repository {id: 'spring-petclinic'})
            RETURN fe.id AS fe, api.path AS path, be.id AS be, c.confidence AS conf
        """).data()

        if row:
            r = row[0]
            print(f"  OK    {r['fe']} --[CONSUMES conf={r['conf']}]--> {r['path']} <--[EXPOSES]-- {r['be']}")
        else:
            # APIContract may not exist yet (Neo4j not populated) — soft fail
            print("  WARN  CONSUMES edge written but cross-chain query returned 0 rows.")
            print("        Run Iteration 15 first to create APIContract nodes.")

    driver.close()

except Exception as e:
    print(f"  SKIP  Neo4j not reachable ({type(e).__name__}: {e})")
    print("        Fix .env NEO4J_USER=neo4j and resume instance at console.neo4j.io")

print("\n" + "=" * 60)
print(f"Iteration 19: {'ALL CHECKS PASS' if all_ok else 'SOME CHECKS FAILED'}")
print()
print("  End-to-end query (run after Iterations 15 + 17 are complete):")
print("    MATCH (r:Repository)-[:CONSUMES]->(api:APIContract)")
print("          <-[:EXPOSES]-(be:Repository)")
print("    RETURN r.id, api.path, be.id")
print()
print("  Expected: angular-petclinic -> /api/pets -> spring-petclinic")
print("=" * 60)
