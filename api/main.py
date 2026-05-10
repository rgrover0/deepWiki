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

app.include_router(classes.router, prefix="/classes", tags=["Classes"])
app.include_router(search.router,  prefix="/search",  tags=["Search"])
app.include_router(ask.router,     prefix="/ask",     tags=["Ask"])
app.include_router(plan.router,    prefix="/plan",    tags=["Plan"])
app.include_router(compare.router, prefix="/compare", tags=["Compare"])


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