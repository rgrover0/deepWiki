import json
from pipeline.graph.schema import get_driver, setup_schema
from pipeline.graph.writer import write_analysis

print("=" * 50)
print("DeepWiki — Iteration 3: Build Knowledge Graph")
print("=" * 50)

# 1. Load analysis from Iteration 2
print("\n📂 Loading analysis from Iteration 2...")
with open("output/analysis.json") as f:
    results = json.load(f)
print(f"✅ Loaded {len(results)} files")

# 2. Connect to Neo4j
driver = get_driver()

# 3. Setup schema
print("\n🔧 Setting up Neo4j schema...")
setup_schema(driver)

# 4. Write graph
print("\n✍️  Writing knowledge graph...")
stats = write_analysis(driver, results)

print(f"""
✅ Graph written:
   Classes : {stats['classes']}
   Methods : {stats['methods']}
   Fields  : {stats['fields']}
""")

# 5. Verify — run queries to show what's in the graph
print("=" * 50)
print("GRAPH VERIFICATION")
print("=" * 50)

with driver.session() as session:

    # Node counts
    counts = session.run("""
        MATCH (n)
        RETURN labels(n)[0] AS label, count(n) AS count
        ORDER BY count DESC
    """)
    print("\n📊 Node counts:")
    for row in counts:
        print(f"   {row['label']:15s}: {row['count']}")

    # Relationship counts
    rels = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) AS rel, count(r) AS count
        ORDER BY count DESC
    """)
    print("\n🔗 Relationship counts:")
    for row in rels:
        print(f"   {row['rel']:20s}: {row['count']}")

    # Show controllers and what they depend on
    print("\n🎯 Controllers and their dependencies:")
    controllers = session.run("""
        MATCH (c:Class {component_type: 'REST_CONTROLLER'})
        OPTIONAL MATCH (c)-[:DEPENDS_ON]->(dep:Class)
        RETURN c.name AS controller, collect(dep.name) AS depends_on
    """)
    for row in controllers:
        deps = ", ".join(row["depends_on"]) or "none"
        print(f"   {row['controller']} → [{deps}]")

    # Show entities
    print("\n📦 Entities found:")
    entities = session.run("""
        MATCH (c:Class {component_type: 'ENTITY'})
        RETURN c.name AS name, c.package AS package
    """)
    for row in entities:
        print(f"   {row['name']} ({row['package']})")

driver.close()
print("\n✅ Iteration 3 complete")
print("\n🌐 View graph visually:")
print("   Open browser → http://localhost:7474")
print("   Login: neo4j / deepwiki123")
print("   Run: MATCH (n) RETURN n LIMIT 50")