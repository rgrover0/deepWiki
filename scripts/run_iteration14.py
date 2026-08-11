"""
Iteration 14 — Method Logic + CALLS Edges

Steps:
  1. Analyze all petclinic Java files via code-analysis-service
  2. Fetch existing class wiki summaries from Neo4j (for LLM context)
  3. Generate logic_summary for every non-trivial method (cached to disk)
  4. Write Method nodes + CALLS edges + hierarchy edges to Neo4j
  5. Embed all methods and store in deepwiki_code_units (unit_type=method)
  6. Verify: MATCH (m:Method)-[:CALLS]->(called) RETURN m.name, called.name

Requires:
  - code-analysis-service running on localhost:8081
  - Neo4j and Qdrant reachable
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

from pipeline.ingestion.git_reader import get_java_files
from pipeline.ingestion.java_analysis_client import analyze_files, is_service_healthy
from core.graph.schema import get_driver
from pipeline.graph.method_writer import write_all_method_data
from pipeline.wiki.summarizer import summarize_methods
from core.embeddings.embedder import build_method_text, embed_batch
from core.embeddings.vector_store import get_client, store_method_embeddings

REPO_PATH = "repos/spring-petclinic"

print("=" * 60)
print("DeepWiki — Iteration 14: Method Logic + CALLS Edges")
print("=" * 60)

# ── Step 1: Analyze Java files ────────────────────────────────
print("\n[1/5] Analyzing Java files via code-analysis-service...")
if not is_service_healthy():
    print("  code-analysis-service not running.")
    print("  Start with: java -jar code-analysis-service/target/*.jar")
    exit(1)

java_files = get_java_files(REPO_PATH)
print(f"  Found {len(java_files)} Java files")
analysis_results = analyze_files(java_files)
print(f"  Analyzed {len(analysis_results)} files with classes")

total_classes = sum(len(r.get("classes", [])) for r in analysis_results)
total_methods = sum(
    len(cls.get("methods", []))
    for r in analysis_results
    for cls in r.get("classes", [])
)
print(f"  Classes: {total_classes}  |  Methods: {total_methods}")

# ── Step 2: Fetch class wiki summaries from Neo4j ─────────────
print("\n[2/5] Fetching class wiki summaries...")
wiki_by_class: dict[str, str] = {}
try:
    driver = get_driver()
    with driver.session() as session:
        rows = session.run(
            "MATCH (c:Class) WHERE c.wiki_summary IS NOT NULL "
            "RETURN c.name AS name, c.wiki_summary AS wiki"
        ).data()
    for row in rows:
        wiki_by_class[row["name"]] = row["wiki"]
    driver.close()
    print(f"  Loaded {len(wiki_by_class)} wiki summaries from Neo4j")
except Exception as e:
    print(f"  Neo4j unavailable ({e}) — generating summaries without class context")

# ── Step 3: Generate method logic summaries ───────────────────
print("\n[3/5] Generating method logic_summaries (LLM, cached)...")
method_summaries: dict[str, dict[str, str]] = {}
total_non_trivial = 0

for file_result in analysis_results:
    for cls in file_result.get("classes", []):
        cls_name = cls["name"]
        cls_wiki = wiki_by_class.get(cls_name, "")
        print(f"  {cls_name}...", end=" ", flush=True)

        summaries = summarize_methods(cls, cls_wiki, delay=0.3)
        method_summaries[cls_name] = summaries

        generated = sum(1 for s in summaries.values() if s)
        total_non_trivial += generated
        print(f"{generated} summaries")

print(f"  Total logic_summaries generated: {total_non_trivial}")

# ── Step 4: Write to Neo4j ────────────────────────────────────
print("\n[4/5] Writing Method nodes + CALLS + hierarchy edges to Neo4j...")
try:
    driver = get_driver()
    counts = write_all_method_data(driver, analysis_results, method_summaries)
    driver.close()
    print(f"  logic_summary written  : {counts['logic_written']}")
    print(f"  CALLS edges attempted  : {counts['calls_attempted']}")

    # Verify CALLS chain
    driver = get_driver()
    with driver.session() as session:
        calls_sample = session.run("""
            MATCH (src:Method)-[r:CALLS]->(tgt:Method)
            WHERE r.confidence >= 1.0
            RETURN src.name AS caller, tgt.name AS callee, r.line AS line
            LIMIT 10
        """).data()
    driver.close()

    print(f"\n  CALLS chain sample (confidence=1.0):")
    if calls_sample:
        for row in calls_sample:
            print(f"    {row['caller']}() -> {row['callee']}()  [line {row['line']}]")
    else:
        print("    (none found — check Neo4j connectivity)")
except Exception as e:
    print(f"  Neo4j write failed: {e}")
    print("  Run verify.py after services are restored to confirm CALLS edges.")

# ── Step 5: Method embeddings → Qdrant ───────────────────────
print("\n[5/5] Embedding methods → deepwiki_code_units...")
try:
    method_data = []
    texts       = []
    for file_result in analysis_results:
        for cls in file_result.get("classes", []):
            cls_name  = cls["name"]
            summaries = method_summaries.get(cls_name, {})
            for method in cls.get("methods", []):
                logic = summaries.get(method["name"], "")
                method_data.append({"cls_name": cls_name, "method": method,
                                    "logic_summary": logic})
                texts.append(build_method_text(cls_name, method, logic))

    print(f"  Embedding {len(texts)} methods...")
    vectors = embed_batch(texts)

    qdrant = get_client()
    store_method_embeddings(qdrant, method_data, vectors)
except Exception as e:
    print(f"  Qdrant write failed: {e}")

# ── Done ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Iteration 14 complete")
print("  Done when: MATCH (m:Method)-[:CALLS]->(c) RETURN m.name, c.name")
print("  returns actual call chains from OwnerController -> OwnerRepository")
print("=" * 60)
