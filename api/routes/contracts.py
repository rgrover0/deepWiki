from fastapi import APIRouter
from pipeline.graph.schema import get_driver

router = APIRouter()


@router.get("")
def get_contracts(repo_id: str = "spring-petclinic"):
    """All APIContracts exposed by a repository, with implementing class."""
    driver = get_driver()
    with driver.session() as session:
        rows = session.run("""
            MATCH (r:Repository {id: $repo_id})-[:EXPOSES]->(a:APIContract)
            OPTIONAL MATCH (c:Class)-[:IMPLEMENTS_CONTRACT]->(a)
            RETURN a.id                AS id,
                   a.http_method       AS http_method,
                   a.path              AS path,
                   a.path_variables    AS path_variables,
                   a.return_type       AS return_type,
                   a.controller_method AS controller_method,
                   a.controller_class  AS controller_class,
                   a.request_body_type AS request_body_type
            ORDER BY a.path, a.http_method
        """, repo_id=repo_id).data()
    driver.close()
    return {"repo_id": repo_id, "contracts": rows, "count": len(rows)}


@router.get("/consumers")
def get_consumers(repo_id: str = "spring-petclinic"):
    """All APIContracts consumed by a repository (from Angular, etc.)."""
    driver = get_driver()
    with driver.session() as session:
        rows = session.run("""
            MATCH (r:Repository {id: $repo_id})-[c:CONSUMES]->(a:APIContract)
            RETURN a.http_method       AS http_method,
                   a.path              AS path,
                   a.controller_class  AS controller_class,
                   c.confidence        AS confidence,
                   c.caller_class      AS caller_class
            ORDER BY a.path
        """, repo_id=repo_id).data()
    driver.close()
    return {"repo_id": repo_id, "consumed": rows, "count": len(rows)}
