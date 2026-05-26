"""
Iteration 12 — Schema Upgrade + Qdrant Migration

Steps:
  1. Upgrade Neo4j schema (new node constraints + indexes)
  2. Create all 8 fixed Qdrant collections
  3. Migrate existing data from deepwiki_classes → deepwiki_code_units
  4. Print verify summary

Run once. Safe to re-run — all operations are idempotent except migration
(which skips if legacy collection is already gone).
"""

from pipeline.graph.schema import get_driver, setup_schema
from pipeline.embeddings.vector_store import get_client, setup_all_collections, migrate_from_legacy

print("=" * 60)
print("DeepWiki — Iteration 12: Schema Upgrade + Qdrant Migration")
print("=" * 60)

# ── Step 1: Neo4j schema ──────────────────────────────────────
print("\n[1/3] Upgrading Neo4j schema...")
driver = get_driver()
setup_schema(driver)
driver.close()

# ── Step 2: Create all 8 Qdrant collections ───────────────────
print("\n[2/3] Creating all 8 Qdrant collections...")
qdrant = get_client()
setup_all_collections(qdrant)

# ── Step 3: Migrate legacy deepwiki_classes → deepwiki_code_units
print("\n[3/3] Migrating legacy collection...")
migrate_from_legacy(qdrant, legacy_name="deepwiki_classes", repo_id="spring-petclinic")

# ── Done ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("✅ Iteration 12 complete")
print("   Run verify.py to confirm all 8 collections + schema")
print("=" * 60)
