import os
from pipeline.graph.schema import get_driver
from pipeline.wiki.summarizer import summarize_all
from pipeline.wiki.diagram_gen import generate_mermaid_diagram, generate_wiki_page
from pipeline.embeddings.embedder import embed_batch
from pipeline.embeddings.vector_store import (
    get_client, setup_collection, store_class_embeddings
)

os.makedirs("output/wiki", exist_ok=True)

print("=" * 55)
print("DeepWiki — Iteration 5: LLM Wiki Summarization")
print("=" * 55)

# 1. Load classes from Neo4j
print("\n📂 Loading classes from Neo4j...")
driver = get_driver()
classes = []
relationships = []

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
            collect(DISTINCT {
                name: m.name,
                return_type: m.return_type,
                annotations: m.annotations
            }) AS methods,
            collect(DISTINCT {
                name: f.name,
                type: f.type,
                annotations: f.annotations
            }) AS fields
    """)
    for row in result:
        classes.append({
            "name":           row["name"],
            "component_type": row["component_type"],
            "package":        row["package"] or "",
            "file":           row["file"] or "",
            "annotations":    row["annotations"] or [],
            "methods": [m for m in row["methods"] if m["name"]],
            "fields":  [f for f in row["fields"]  if f["name"]]
        })

    # Load relationships for diagram
    rels = session.run("""
        MATCH (a:Class)-[r:DEPENDS_ON]->(b:Class)
        RETURN a.name AS source, type(r) AS type, b.name AS target
    """)
    for row in rels:
        relationships.append({
            "source": row["source"],
            "type":   row["type"],
            "target": row["target"]
        })

driver.close()
print(f"✅ Loaded {len(classes)} classes, {len(relationships)} relationships")

# 2. Generate LLM summaries
print(f"\n🤖 Generating wiki summaries via Groq...")
print("   (2s delay between calls — respecting free tier rate limits)\n")
summaries = summarize_all(classes, delay=2.0)

# 3. Store summaries back in Neo4j
print("\n💾 Storing summaries in Neo4j...")
driver = get_driver()
with driver.session() as session:
    for name, summary in summaries.items():
        session.run(
            "MATCH (c:Class {name: $name}) SET c.wiki_summary = $summary",
            name=name, summary=summary
        )
driver.close()
print("✅ Summaries stored in Neo4j")

# 4. Generate individual wiki pages
print("\n📄 Generating wiki pages...")
for cls in classes:
    summary = summaries.get(cls["name"], "")
    page = generate_wiki_page(cls, summary)
    path = f"output/wiki/{cls['name']}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
print(f"✅ Generated {len(classes)} wiki pages in output/wiki/")

# 5. Generate architecture diagram
print("\n🗺️  Generating architecture diagram...")
diagram = generate_mermaid_diagram(classes, relationships)
with open("output/architecture.md", "w", encoding="utf-8") as f:
    f.write("# Architecture Diagram\n\n")
    f.write(diagram)
print("✅ Saved to output/architecture.md")

# 6. Update Qdrant with richer text (summary + structure)
print("\n🔄 Updating Qdrant with enriched embeddings...")
enriched_texts = [
    f"{cls['name']}: {summaries.get(cls['name'], '')} "
    f"Methods: {', '.join(m['name'] for m in cls.get('methods', []))}. "
    f"Fields: {', '.join(f['name'] for f in cls.get('fields', []))}."
    for cls in classes
]
embeddings = embed_batch(enriched_texts)
qdrant = get_client()
setup_collection(qdrant)
store_class_embeddings(qdrant, classes, embeddings)
print("✅ Qdrant updated with enriched embeddings")

# 7. Print sample summaries
print("\n" + "=" * 55)
print("SAMPLE WIKI SUMMARIES")
print("=" * 55)
for cls in classes[:4]:
    print(f"\n📖 {cls['name']} [{cls['component_type']}]")
    print(f"   {summaries.get(cls['name'], '')[:200]}...")

print(f"\n✅ Iteration 5 complete")
print(f"   Wiki pages: output/wiki/")
print(f"   Architecture: output/architecture.md")
print(f"\nNext: Iteration 6 — FastAPI + Streamlit web UI")