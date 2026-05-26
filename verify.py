import os
from dotenv import load_dotenv

load_dotenv()

print("=== DeepWiki Stack Verification ===\n")

# 1. Groq
try:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say: Groq connected"}],
        max_tokens=10
    )
    print("✅ Groq API:", response.choices[0].message.content)
except Exception as e:
    print("❌ Groq failed:", e)

# 2. Neo4j — connectivity + schema nodes
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )
    driver.verify_connectivity()
    print("✅ Neo4j: Connected")

    with driver.session() as session:
        # Check new node types exist as constraints
        result = session.run("SHOW CONSTRAINTS YIELD name RETURN name").data()
        constraint_names = {r["name"] for r in result}

        expected_constraints = {
            "suite_unique", "repo_unique", "module_unique", "api_contract_unique"
        }
        for c in sorted(expected_constraints):
            status = "✅" if c in constraint_names else "❌"
            print(f"   {status} Constraint: {c}")

        # Count existing nodes per new type
        for label in ["ApplicationSuite", "Repository", "Module", "APIContract", "APIContractImpact"]:
            count = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
            print(f"   {'✅' if True else ''} {label}: {count} nodes")

    driver.close()
except Exception as e:
    print("❌ Neo4j failed:", e)

# 3. Qdrant — all 8 collections
try:
    from qdrant_client import QdrantClient
    from pipeline.embeddings.vector_store import ALL_COLLECTIONS

    url     = os.getenv("QDRANT_HOST")
    api_key = os.getenv("QDRANT_API_KEY")

    print(f"\n   Connecting to Qdrant: {url}")

    if url and api_key:
        client = QdrantClient(url=url, api_key=api_key)
    else:
        client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )

    existing = {c.name for c in client.get_collections().collections}
    print("✅ Qdrant: Connected\n")

    all_ok = True
    for name in ALL_COLLECTIONS:
        if name in existing:
            info  = client.get_collection(name)
            count = info.points_count
            print(f"   ✅ {name}: {count} points")
        else:
            print(f"   ❌ {name}: MISSING")
            all_ok = False

    if all_ok:
        print("\n✅ All 8 Qdrant collections present")
    else:
        print("\n⚠️  Some collections missing — run run_iteration12.py")

except Exception as e:
    print("❌ Qdrant failed:", e)

print("\n=== Done ===")
