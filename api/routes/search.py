from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.graph.schema import get_driver
from core.embeddings.embedder import embed_text
from core.embeddings.vector_store import get_client, semantic_search

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    component_type: str = None
    unit_type: str = None          # "class" | "method" | None (both)
    scope: str = "repo"            # "repo" | "suite" | "cross_suite"
    repo_id: str = "spring-petclinic"
    suite_id: str = "pet-management-platform"


@router.post("")
def semantic_search_endpoint(req: SearchRequest):
    """Vector similarity search across classes and/or methods."""
    query_vector = embed_text(req.query)
    client       = get_client()

    repo_filter  = req.repo_id  if req.scope == "repo"   else None
    suite_filter = req.suite_id if req.scope == "suite"  else None

    results = semantic_search(
        client,
        query_vector,
        top_k=req.top_k,
        component_type=req.component_type,
        repo_id=repo_filter,
        suite_id=suite_filter,
        unit_type=req.unit_type,
    )
    return {"results": results, "scope": req.scope, "count": len(results)}


@router.get("/")
def list_classes():
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Class)
            RETURN c.name           AS name,
                   c.component_type AS component_type,
                   c.package        AS package,
                   c.wiki_summary   AS wiki_summary
            ORDER BY c.component_type, c.name
        """)
        classes = [dict(r) for r in result]
    driver.close()
    return classes


@router.get("/{name}")
def get_class(name: str):
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Class {name: $name})
            WITH c ORDER BY c.repo_id
            LIMIT 1
            OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
            OPTIONAL MATCH (c)-[:HAS_FIELD]->(f:Field)
            OPTIONAL MATCH (c)-[:DEPENDS_ON]->(dep:Class)
            RETURN
                c.name           AS name,
                c.component_type AS component_type,
                c.package        AS package,
                c.file           AS file,
                c.annotations    AS annotations,
                c.wiki_summary   AS wiki_summary,
                collect(DISTINCT {
                    name: m.name,
                    return_type: m.return_type,
                    params: m.params,
                    annotations: m.annotations
                }) AS methods,
                collect(DISTINCT {
                    name: f.name,
                    type: f.type,
                    annotations: f.annotations
                }) AS fields,
                collect(DISTINCT dep.name) AS dependencies
        """, name=name)

        row = result.single()
        if not row:
            raise HTTPException(status_code=404, detail=f"Class {name} not found")

        data = dict(row)
        data["methods"] = [m for m in data["methods"] if m["name"]]
        data["fields"]  = [f for f in data["fields"]  if f["name"]]

    driver.close()

    # Load wiki markdown if exists
    try:
        with open(f"output/wiki/{name}.md", encoding="utf-8") as f:
            data["wiki_page"] = f.read()
    except FileNotFoundError:
        data["wiki_page"] = ""

    return data