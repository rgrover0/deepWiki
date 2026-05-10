from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()


def get_driver():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )


def setup_schema(driver):
    """Create constraints and indexes."""
    queries = [
        "CREATE CONSTRAINT class_unique IF NOT EXISTS FOR (c:Class) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT package_unique IF NOT EXISTS FOR (p:Package) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT file_unique IF NOT EXISTS FOR (f:JavaFile) REQUIRE f.path IS UNIQUE",
        "CREATE INDEX method_id IF NOT EXISTS FOR (m:Method) ON (m.id)",
        "CREATE INDEX field_id IF NOT EXISTS FOR (f:Field) ON (f.id)",
    ]
    with driver.session() as session:
        for q in queries:
            session.run(q)
    print("✅ Schema setup complete")