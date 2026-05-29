import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="DeepWiki API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import classes
from api.routes import search
from api.routes import ask
from api.routes import plan
from api.routes import compare
from api.routes import contracts
from api.routes import flow
from api.routes import suite
from api.routes import confluence
from api.routes import project
from api.routes import admin_routes
from api import feedback

app.include_router(classes.router,   prefix="/classes",   tags=["Classes"])
app.include_router(search.router,    prefix="/search",    tags=["Search"])
app.include_router(ask.router,       prefix="/ask",       tags=["Ask"])
app.include_router(plan.router,      prefix="/plan",      tags=["Plan"])
app.include_router(compare.router,   prefix="/compare",   tags=["Compare"])
app.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
app.include_router(flow.router,      prefix="/flow",      tags=["Flow"])
app.include_router(suite.router,     prefix="/suite",     tags=["Suite"])
app.include_router(project.router,      prefix="/project",  tags=["Project"])
app.include_router(admin_routes.router)
app.include_router(feedback.router,     prefix="/feedback", tags=["Feedback"])
app.include_router(confluence.router,  prefix="/confluence",  tags=["Confluence"])


@app.on_event("startup")
def bootstrap_qdrant_collections() -> None:
    """Ensure required Qdrant collections exist before serving requests."""
    if os.getenv("QDRANT_AUTO_BOOTSTRAP", "true").lower() in {"0", "false", "no"}:
        print("Qdrant bootstrap disabled by QDRANT_AUTO_BOOTSTRAP")
        return

    try:
        from pipeline.embeddings.vector_store import get_client, setup_all_collections

        client = get_client()
        setup_all_collections(client)
        print("Qdrant collections are ready")
    except Exception as exc:
        # Keep API process alive; endpoints will still surface connection errors at runtime.
        print(f"Qdrant bootstrap skipped: {exc}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def stats():
    from pipeline.graph.schema import get_driver
    driver = get_driver()
    with driver.session() as session:
        counts = session.run("""
            MATCH (n)
            RETURN labels(n)[0] AS label, count(n) AS count
            ORDER BY count DESC
        """)
        node_counts = {r["label"]: r["count"] for r in counts}
        rels = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS rel, count(r) AS count
        """)
        rel_counts = {r["rel"]: r["count"] for r in rels}
    driver.close()
    return {"nodes": node_counts, "relationships": rel_counts}


@app.get("/architecture")
def architecture():
    try:
        with open("output/architecture.md", encoding="utf-8") as f:
            return {"diagram": f.read()}
    except FileNotFoundError:
        return {"diagram": ""}