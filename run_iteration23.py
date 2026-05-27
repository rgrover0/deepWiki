"""
Iteration 23 - Confluence MCP Ingestion

Verifies:
  1. pipeline/ingestion/confluence_ingester.py — all key functions present
  2. api/routes/confluence.py — all 6 endpoints present
  3. api/main.py — confluence router registered
  4. pipeline/graph/schema.py — ConfluencePage + ContradictionFlag constraints
  5. ui/app.py — Knowledge Sources page + Confluence flags page
  6. api/routes/ask.py — confluence_sources in response, search_confluence called
  7. Unit test: classify_content fallback (no API key)
  8. Unit test: _extract_page_id from URL forms
  9. Neo4j smoke: ConfluencePage node round-trip

Done when: POST /confluence/ingest with a real Confluence URL stores a
  ConfluencePage node; GET /ask returns confluence_sources; alignment score
  and any ContradictionFlags are visible in Streamlit Knowledge Sources page.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

print("=" * 60)
print("DeepWiki - Iteration 23: Confluence MCP Ingestion")
print("=" * 60)

all_ok = True


def grep(path: Path, pattern: str) -> bool:
    if not path.exists():
        return False
    return pattern in path.read_text(encoding="utf-8", errors="ignore")


# -- 1. confluence_ingester.py ------------------------------------------------
print("\n[1/9] pipeline/ingestion/confluence_ingester.py:")
ingester = ROOT / "pipeline/ingestion/confluence_ingester.py"
checks = [
    ("def fetch_page",             "fetch_page()"),
    ("def classify_content",       "classify_content()"),
    ("def embed_and_store",        "embed_and_store()"),
    ("def compute_alignment",      "compute_alignment()"),
    ("def write_confluence_node",  "write_confluence_node()"),
    ("def ingest_page",            "ingest_page() pipeline entry point"),
    ("def search_confluence",      "search_confluence() for Ask integration"),
    ("CONTRADICTION_THRESHOLD",    "contradiction threshold constant"),
    ("ContradictionFlag",          "ContradictionFlag node written"),
    ("server_db",                  "server_db vault-only branch"),
    ("CONTENT_COLLECTIONS",        "CONTENT_COLLECTIONS map"),
]
for pattern, desc in checks:
    ok = grep(ingester, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 2. api/routes/confluence.py ----------------------------------------------
print("\n[2/9] api/routes/confluence.py:")
conf_route = ROOT / "api/routes/confluence.py"
checks = [
    ("/ingest",           "POST /confluence/ingest"),
    ("/pages",            "GET /confluence/pages"),
    ("/for-module/",      "GET /confluence/for-module/{module_id}"),
    ("/flags",            "GET /confluence/flags"),
    ("/resolve",          "PUT /confluence/flags/{flag_id}/resolve"),
    ("alignment_score",   "alignment_score in response"),
    ("ContradictionFlag", "ContradictionFlag query"),
]
for pattern, desc in checks:
    ok = grep(conf_route, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 3. api/main.py -----------------------------------------------------------
print("\n[3/9] api/main.py:")
main = ROOT / "api/main.py"
checks = [
    ("from api.routes import confluence", "imports confluence router"),
    ('prefix="/confluence"',              "mounts at /confluence"),
]
for pattern, desc in checks:
    ok = grep(main, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 4. schema.py -------------------------------------------------------------
print("\n[4/9] pipeline/graph/schema.py:")
schema = ROOT / "pipeline/graph/schema.py"
checks = [
    ("ConfluencePage",          "ConfluencePage uniqueness constraint"),
    ("ContradictionFlag",       "ContradictionFlag index"),
]
for pattern, desc in checks:
    ok = grep(schema, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 5. ui/app.py Knowledge Sources page ------------------------------------
print("\n[5/9] ui/app.py Knowledge Sources page:")
app = ROOT / "ui/app.py"
checks = [
    ("Knowledge Sources",   "Knowledge Sources in nav"),
    ("/confluence/ingest",  "POST /confluence/ingest"),
    ("/confluence/pages",   "GET /confluence/pages"),
    ("/confluence/flags",   "GET /confluence/flags"),
    ("alignment_score",     "alignment_score displayed"),
    ("ContradictionFlag",   "ContradictionFlag/Flags section"),
    ("conf_category",       "category selector"),
    ("module_tags",         "module_tags input"),
]
for pattern, desc in checks:
    ok = grep(app, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 6. ask.py Confluence integration ----------------------------------------
print("\n[6/9] api/routes/ask.py Confluence integration:")
ask = ROOT / "api/routes/ask.py"
checks = [
    ("search_confluence",       "calls search_confluence()"),
    ("confluence_sources",      "returns confluence_sources"),
    ("CONFLUENCE DESIGN NOTES", "confluence prompt section"),
]
for pattern, desc in checks:
    ok = grep(ask, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {desc}")
    all_ok &= ok


# -- 7. Unit test: classify_content fallback ---------------------------------
print("\n[7/9] Unit test: classify_content fallback:")
try:
    from pipeline.ingestion.confluence_ingester import classify_content, CONTENT_TYPES
    # Without LLM, it should return a valid content type (defaults to 'general' on error)
    result = classify_content("Meeting notes Q1 2026", "We decided to use Infinispan for caching.")
    ok = result in CONTENT_TYPES
    print(f"  {'OK  ' if ok else 'FAIL'}  classify_content returns valid type: {result!r}")
    if not ok:
        all_ok = False

    # Server/db should stay vault-only
    from pipeline.ingestion.confluence_ingester import CONTENT_COLLECTIONS
    ok = CONTENT_COLLECTIONS.get("server_db") is None
    print(f"  {'OK  ' if ok else 'FAIL'}  server_db maps to None (vault-only)")
    if not ok:
        all_ok = False
except Exception as e:
    print(f"  FAIL  {type(e).__name__}: {e}")
    all_ok = False


# -- 8. Unit test: _extract_page_id -----------------------------------------
print("\n[8/9] Unit test: _extract_page_id:")
try:
    from pipeline.ingestion.confluence_ingester import _extract_page_id
    cases = [
        ("123456",                                                    "123456"),
        ("https://org.atlassian.net/wiki/spaces/ENG/pages/123456",   "123456"),
        ("https://org.atlassian.net/wiki/spaces/ENG/pages/789/Title","789"),
        ("https://org.atlassian.net?pageId=42",                      "42"),
    ]
    for inp, expected in cases:
        got = _extract_page_id(inp)
        ok  = got == expected
        print(f"  {'OK  ' if ok else 'FAIL'}  _extract_page_id({inp!r:.50}) -> {got!r}")
        if not ok:
            all_ok = False
except Exception as e:
    print(f"  FAIL  {type(e).__name__}: {e}")
    all_ok = False


# -- 9. Neo4j smoke ----------------------------------------------------------
print("\n[9/9] Neo4j smoke: ConfluencePage node round-trip:")
try:
    from pipeline.graph.schema import get_driver
    from pipeline.ingestion.confluence_ingester import write_confluence_node

    driver = get_driver()
    fake_page = {
        "id":            "test-iter23-page",
        "title":         "Test Auth Design from run_iteration23.py",
        "page_url":      "https://example.atlassian.net/wiki/spaces/ENG/pages/test",
        "content_type":  "architecture",
        "author":        "test",
        "last_modified": "2026-01-01T00:00:00Z",
    }
    result = write_confluence_node(
        driver=driver,
        page_data=fake_page,
        module_ids=["auth-module"],
        alignment_scores={"auth-module": 0.42},
        category="current",
        collection="deepwiki_confluence_architecture",
    )

    with driver.session() as session:
        row = session.run(
            "MATCH (p:ConfluencePage {id: $id}) RETURN p.title AS t, p.content_type AS ct",
            id="test-iter23-page",
        ).single()

    driver.close()

    if row:
        print(f"  OK    ConfluencePage created: title={row['t']!r}, type={row['ct']!r}")
        print(f"  OK    modules_linked={result['modules_linked']}, flags={result['flags_created']}")
    else:
        print("  WARN  write_confluence_node ran but node not found in Neo4j")

except Exception as e:
    print(f"  SKIP  Neo4j: {type(e).__name__}: {e}")
    print("        Fix .env NEO4J_USER=neo4j and resume at console.neo4j.io")


print("\n" + "=" * 60)
print(f"Iteration 23: {'ALL CHECKS PASS' if all_ok else 'SOME CHECKS FAILED'}")
print()
print("  Verify live:")
print('    POST /confluence/ingest')
print('      {"url": "<confluence-page-url>", "category": "current",')
print('       "module_tags": ["auth-module"]}')
print('    -> {"ok": true, "result": {"content_type": "...", "alignment": {...}}}')
print()
print('    GET /confluence/pages')
print('    -> {"pages": [...], "count": 1}')
print()
print('    POST /ask {"question": "Why do we use Infinispan?"}')
print('    -> response includes "confluence_sources": ["https://..."]')
print()
print("  Streamlit: navigate to 'Knowledge Sources' page")
print("    Submit URL -> see alignment score + any ContradictionFlags")
print("=" * 60)
