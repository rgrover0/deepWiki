import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def get_driver():
    uri      = os.getenv("NEO4J_URI")
    user     = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    # AuraDB uses neo4j+s:// (SSL auto-handled)
    # Local uses bolt:// — both work with same code
    return GraphDatabase.driver(uri, auth=(user, password))


def setup_schema(driver):
    """Create constraints and indexes."""
    queries = [
        # Drop legacy global-only constraints before creating repo-scoped ones.
        "DROP CONSTRAINT class_unique IF EXISTS",
        "DROP CONSTRAINT file_unique IF EXISTS",
        # Phase 0 — base nodes
        "CREATE CONSTRAINT class_repo_unique IF NOT EXISTS FOR (c:Class) REQUIRE (c.repo_id, c.name) IS UNIQUE",
        "CREATE CONSTRAINT package_unique IF NOT EXISTS FOR (p:Package) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT file_repo_unique IF NOT EXISTS FOR (f:JavaFile) REQUIRE (f.repo_id, f.path) IS UNIQUE",
        "CREATE INDEX method_id IF NOT EXISTS FOR (m:Method) ON (m.id)",
        "CREATE INDEX field_id IF NOT EXISTS FOR (f:Field) ON (f.id)",
        # Iteration 12 — hierarchy + API nodes
        "CREATE CONSTRAINT suite_unique IF NOT EXISTS FOR (s:ApplicationSuite) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT repo_unique IF NOT EXISTS FOR (r:Repository) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT module_unique IF NOT EXISTS FOR (m:Module) REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT api_contract_unique IF NOT EXISTS FOR (a:APIContract) REQUIRE a.id IS UNIQUE",
        "CREATE INDEX api_impact_id IF NOT EXISTS FOR (i:APIContractImpact) ON (i.id)",
        # Iteration 23 — Confluence nodes
        "CREATE CONSTRAINT confluence_page_unique IF NOT EXISTS FOR (p:ConfluencePage) REQUIRE p.id IS UNIQUE",
        "CREATE INDEX contradiction_flag_page IF NOT EXISTS FOR (f:ContradictionFlag) ON (f.page_id)",
        "CREATE CONSTRAINT feedback_unique IF NOT EXISTS FOR (f:Feedback) REQUIRE f.id IS UNIQUE",
    ]
    with driver.session() as session:
        for q in queries:
            session.run(q)
    print("✅ Schema setup complete")