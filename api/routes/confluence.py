"""
Confluence API routes — Iteration 23.

POST /confluence/ingest            — submit a Confluence page for ingestion
GET  /confluence/pages             — list all ingested ConfluencePage nodes
GET  /confluence/{page_id}         — page detail + alignment scores
GET  /confluence/for-module/{module_id} — pages linked to a module
GET  /confluence/flags             — all unresolved ContradictionFlags
PUT  /confluence/flags/{flag_id}/resolve — mark a flag resolved
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pipeline.graph.schema import get_driver

router = APIRouter()


class IngestRequest(BaseModel):
    url:         str
    category:    str         = "current"    # historical | current | upcoming | update
    module_tags: list[str]   = []
    suite_id:    str         = ""


@router.post("/ingest")
def ingest_confluence_page(req: IngestRequest):
    """
    Fetch, classify, embed, align, and store a Confluence page.
    Returns ingestion summary with content_type, collection, alignment scores, flags.
    """
    from pipeline.ingestion.confluence_ingester import ingest_page
    try:
        result = ingest_page(
            url_or_id=req.url,
            category=req.category,
            module_tags=req.module_tags,
            suite_id=req.suite_id,
        )
        return {"ok": True, "result": result}
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pages")
def list_confluence_pages():
    """Return all ingested ConfluencePage nodes."""
    driver = get_driver()
    with driver.session() as session:
        rows = session.run("""
            MATCH (p:ConfluencePage)
            OPTIONAL MATCH (p)-[d:DOCUMENTS]->(m:Module)
            RETURN p.id            AS page_id,
                   p.title         AS title,
                   p.page_url      AS page_url,
                   p.content_type  AS content_type,
                   p.category      AS category,
                   p.collection    AS collection,
                   p.last_modified AS last_modified,
                   collect({module_id: m.id, score: d.alignment_score}) AS modules
            ORDER BY p.ingested_at DESC
        """)
        pages = []
        for r in rows:
            page = dict(r)
            page["modules"] = [m for m in page["modules"] if m.get("module_id")]
            pages.append(page)
    driver.close()
    return {"pages": pages, "count": len(pages)}


@router.get("/for-module/{module_id}")
def pages_for_module(module_id: str):
    """Return all Confluence pages linked to a module, ordered by alignment score."""
    driver = get_driver()
    with driver.session() as session:
        rows = session.run("""
            MATCH (p:ConfluencePage)-[d:DOCUMENTS]->(m:Module {id: $module_id})
            RETURN p.id           AS page_id,
                   p.title        AS title,
                   p.page_url     AS page_url,
                   p.content_type AS content_type,
                   p.category     AS category,
                   d.alignment_score AS alignment_score
            ORDER BY d.alignment_score DESC
        """, module_id=module_id)
        pages = [dict(r) for r in rows]
    driver.close()
    return {"module_id": module_id, "pages": pages, "count": len(pages)}


@router.get("/flags")
def list_contradiction_flags():
    """Return all unresolved ContradictionFlag nodes."""
    driver = get_driver()
    with driver.session() as session:
        rows = session.run("""
            MATCH (f:ContradictionFlag {resolved: false})
            OPTIONAL MATCH (p:ConfluencePage {id: f.page_id})
            RETURN f.id             AS flag_id,
                   f.page_id        AS page_id,
                   f.module_id      AS module_id,
                   f.alignment_score AS alignment_score,
                   f.severity       AS severity,
                   p.title          AS page_title,
                   p.page_url       AS page_url
            ORDER BY f.alignment_score ASC
        """)
        flags = [dict(r) for r in rows]
    driver.close()
    return {"flags": flags, "count": len(flags)}


@router.put("/flags/{flag_id}/resolve")
def resolve_flag(flag_id: str):
    """Mark a ContradictionFlag as resolved."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (f:ContradictionFlag {id: $flag_id})
            SET f.resolved = true, f.resolved_at = timestamp()
            RETURN f.id AS id
        """, flag_id=flag_id)
        row = result.single()
    driver.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Flag {flag_id} not found")
    return {"ok": True, "flag_id": row["id"]}


@router.get("/{page_id}")
def get_confluence_page(page_id: str):
    """Return a single ConfluencePage with its module links and alignment scores."""
    driver = get_driver()
    with driver.session() as session:
        row = session.run("""
            MATCH (p:ConfluencePage {id: $page_id})
            OPTIONAL MATCH (p)-[d:DOCUMENTS]->(m:Module)
            RETURN p.id            AS page_id,
                   p.title         AS title,
                   p.page_url      AS page_url,
                   p.content_type  AS content_type,
                   p.category      AS category,
                   p.collection    AS collection,
                   p.author        AS author,
                   p.last_modified AS last_modified,
                   collect({
                     module_id:       m.id,
                     alignment_score: d.alignment_score,
                     category:        d.category
                   }) AS modules
        """, page_id=page_id).single()

        if not row:
            raise HTTPException(status_code=404, detail=f"ConfluencePage {page_id} not found")

        data = dict(row)
        data["modules"] = [m for m in data["modules"] if m.get("module_id")]

        # Attach any active contradiction flags
        flags = session.run("""
            MATCH (f:ContradictionFlag {page_id: $page_id, resolved: false})
            RETURN f.id AS flag_id, f.module_id AS module_id,
                   f.alignment_score AS score, f.severity AS severity
        """, page_id=page_id)
        data["flags"] = [dict(f) for f in flags]

    driver.close()
    return data
