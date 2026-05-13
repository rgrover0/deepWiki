from fastapi import APIRouter, HTTPException
from pipeline.graph.schema import get_driver

router = APIRouter()


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