from pipeline.graph.schema import get_driver
from pipeline.embeddings.embedder import embed_text, embed_batch, build_class_text
from pipeline.embeddings.vector_store import (
    get_client, setup_collection, store_class_embeddings, semantic_search
)

print("=" * 55)
print("DeepWiki — Iteration 4: Embeddings + Semantic Search")
print("=" * 55)

# 1. Load classes from Neo4j
print("\n📂 Loading classes from Neo4j...")
driver = get_driver()
classes = []

with driver.session() as session:
    result = session.run("""
        MATCH (c:Class)
        OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
        OPTIONAL MATCH (c)-[:HAS_FIELD]->(f:Field)
        RETURN
            c.name           AS name,
            c.component_type AS component_type,
            c.package        AS package,
            c.file           AS file,
            c.annotations    AS annotations,
            collect(DISTINCT {name: m.name, return_type: m.return_type}) AS methods,
            collect(DISTINCT {name: f.name, type: f.type}) AS fields
    """)
    for row in result:
        classes.append({
            "name":           row["name"],
            "component_type": row["component_type"],
            "package":        row["package"] or "",
            "file":           row["file"] or "",
            "annotations":    row["annotations"] or [],
            "methods":        [m for m in row["methods"] if m["name"]],
            "fields":         [f for f in row["fields"] if f["name"]]
        })

driver.close()
print(f"✅ Loaded {len(classes)} classes from Neo4j")

# 2. Build text descriptions
print("\n📝 Building text descriptions...")
texts = [build_class_text(cls) for cls in classes]

print("\nSample description:")
print(f"  {texts[0][:120]}...")

# 3. Generate embeddings
print("\n🔢 Generating embeddings...")
embeddings = embed_batch(texts)
print(f"✅ Generated {len(embeddings)} embeddings "
      f"(dimension: {len(embeddings[0])})")

# 4. Store in Qdrant
print("\n💾 Storing in Qdrant...")
qdrant = get_client()
setup_collection(qdrant)
store_class_embeddings(qdrant, classes, embeddings)

# 5. Test semantic search
print("\n" + "=" * 55)
print("SEMANTIC SEARCH TEST")
print("=" * 55)

queries = [
    "Which class handles pet data and CRUD operations?",
    "Where are REST API endpoints defined?",
    "Which class manages owner information?",
    "What handles database repository operations?",
    "Show me the class that have only create operations?",
    "Understand the code and explain the business logic?",
]

for query in queries:
    print(f"\n🔍 Query: '{query}'")
    query_vector = embed_text(query)
    results = semantic_search(qdrant, query_vector, top_k=3)

    for i, r in enumerate(results, 1):
        print(f"   {i}. [{r['component_type']:18s}] "
              f"{r['name']:30s} score: {r['score']}")

print("\n✅ Iteration 4 complete")
print("\nNext: Iteration 5 — LLM Wiki Summarization")