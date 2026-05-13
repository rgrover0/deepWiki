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

# 2. Neo4j
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )
    driver.verify_connectivity()
    print("✅ Neo4j: Connected")
    driver.close()
except Exception as e:
    print("❌ Neo4j failed:", e)

# 3. Qdrant
try:
    from qdrant_client import QdrantClient

    url     = os.getenv("QDRANT_HOST")
    api_key = os.getenv("QDRANT_API_KEY")

    print(f"   Connecting to Qdrant: {url}")
    
    if url and api_key:
        client = QdrantClient(url=url, api_key=api_key)
    else:
        # Fallback local
        client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        
    client.get_collections()
    print("✅ Qdrant: Connected")
except Exception as e:
    print("❌ Qdrant failed:", e)

print("\n=== Done ===")