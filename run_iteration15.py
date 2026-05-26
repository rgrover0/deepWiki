"""
Iteration 15 — APIContract Extraction

Steps:
  1. Analyze all petclinic Java files via code-analysis-service
  2. Write APIContract nodes + Repository + EXPOSES edges to Neo4j
  3. Run api_impact nightly job (creates empty impact nodes)
  4. Store APIContract embeddings in deepwiki_api_contracts
  5. Print catalog summary

Done when: 12+ endpoints visible in portal and each shows its controller class.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from pipeline.ingestion.git_reader import get_java_files
from pipeline.ingestion.java_analysis_client import analyze_files, is_service_healthy
from pipeline.graph.schema import get_driver
from pipeline.graph.api_writer import write_all_api_contracts
from pipeline.graph.api_impact import run_api_impact_nightly
from pipeline.embeddings.embedder import embed_batch
from pipeline.embeddings.vector_store import get_client
from qdrant_client.models import PointStruct
import zlib

REPO_PATH = "repos/spring-petclinic"
REPO_ID   = "spring-petclinic"

print("=" * 60)
print("DeepWiki — Iteration 15: APIContract Extraction")
print("=" * 60)

# ── Step 1: Analyze ───────────────────────────────────────────
print("\n[1/4] Analyzing Java files...")
if not is_service_healthy():
    print("  code-analysis-service not running.")
    print("  Start: java -jar code-analysis-service/target/*.jar")
    exit(1)

java_files       = get_java_files(REPO_PATH)
analysis_results = analyze_files(java_files)

all_contracts = [
    c
    for r in analysis_results
    for cls in r.get("classes", [])
    for c in cls.get("api_contracts", [])
]
print(f"  Files analyzed : {len(analysis_results)}")
print(f"  API contracts  : {len(all_contracts)}")

# ── Step 2: Write to Neo4j ────────────────────────────────────
print("\n[2/4] Writing APIContract nodes to Neo4j...")
try:
    driver = get_driver()
    total  = write_all_api_contracts(driver, analysis_results, REPO_ID)
    print(f"  Written: {total} APIContracts")

    # ── Step 3: API impact nightly job ────────────────────────
    print("\n[3/4] Running api_impact nightly job...")
    processed = run_api_impact_nightly(driver)
    driver.close()
    print(f"  Impact nodes created/updated: {processed}")
except Exception as e:
    print(f"  Neo4j unavailable: {e}")

# ── Step 4: Embed into deepwiki_api_contracts ─────────────────
print("\n[4/4] Embedding APIContracts → Qdrant...")
try:
    texts = [
        f"{c['http_method']} {c['path']}. "
        f"Controller: {c['controller_class']}.{c['controller_method']}. "
        f"Returns: {c.get('return_type', '')}."
        for c in all_contracts
    ]
    vectors = embed_batch(texts)
    qdrant  = get_client()
    points  = []
    for contract, vector in zip(all_contracts, vectors):
        pid = zlib.crc32(
            f"api:{REPO_ID}:{contract['http_method']}:{contract['path']}".encode()
        ) & 0x7FFFFFFF
        points.append(PointStruct(
            id=pid,
            vector=vector,
            payload={
                "http_method":       contract["http_method"],
                "path":              contract["path"],
                "controller_class":  contract.get("controller_class", ""),
                "controller_method": contract.get("controller_method", ""),
                "return_type":       contract.get("return_type", ""),
                "repo_id":           REPO_ID,
                "method":            contract["http_method"],
                "version":           "v1",
            }
        ))
    qdrant.upsert(collection_name="deepwiki_api_contracts", points=points)
    print(f"  Stored {len(points)} API contract embeddings")
except Exception as e:
    print(f"  Qdrant unavailable: {e}")

# ── Summary ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"Iteration 15 complete — {len(all_contracts)} endpoints found")
print("\nEndpoint catalog:")
for c in sorted(all_contracts, key=lambda x: x["path"]):
    rb = f"  body:{c['request_body_type']}" if c.get("request_body_type") else ""
    print(f"  {c['http_method']:7s} {c['path']:40s} {c['controller_class']}{rb}")
print("=" * 60)
