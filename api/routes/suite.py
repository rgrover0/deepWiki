"""
Suite management routes — Iteration 17.

GET /suite                  list all ApplicationSuite nodes
GET /suite/{suite_id}       suite details: repos + API counts + wiki coverage
POST /suite/bootstrap       write suites from config/suites.json into Neo4j
"""

from fastapi import APIRouter, HTTPException
from neo4j.exceptions import AuthError, ServiceUnavailable, Neo4jError
from pipeline.graph.schema import get_driver

router = APIRouter()


def _neo4j_503(exc: Exception) -> HTTPException:
    """Convert a Neo4j connection/auth error into a friendly 503."""
    return HTTPException(
        status_code=503,
        detail=(
            f"Neo4j unavailable or credentials invalid: {exc}. "
            "Check NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD in your .env file."
        ),
    )


@router.get("")
def list_suites():
    driver = get_driver()
    try:
        with driver.session() as session:
            rows = session.run("""
                MATCH (s:ApplicationSuite)
                OPTIONAL MATCH (s)-[:HAS_REPO]->(r:Repository)
                WITH s, [repo IN collect(r) WHERE repo IS NOT NULL |
                    {
                        id: repo.id,
                        name: repo.name,
                        language: coalesce(repo['language'], '')
                    }
                ] AS repos
                RETURN s.id          AS id,
                       s.name        AS name,
                       s.description AS description,
                       repos,
                       size(repos)   AS repo_count
                ORDER BY s.name
            """).data()
        return {"suites": rows}
    except (AuthError, ServiceUnavailable, Neo4jError) as exc:
        raise _neo4j_503(exc)
    finally:
        driver.close()


@router.get("/{suite_id}")
def get_suite(suite_id: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            suite_row = session.run("""
                MATCH (s:ApplicationSuite {id: $id})
                RETURN s.id AS id, s.name AS name, s.description AS description
            """, id=suite_id).single()

            if not suite_row:
                raise HTTPException(status_code=404,
                                    detail=f"Suite '{suite_id}' not found")

            repos = session.run("""
                MATCH (s:ApplicationSuite {id: $suite_id})-[:HAS_REPO]->(r:Repository)
                OPTIONAL MATCH (r)-[:EXPOSES]->(api:APIContract)
                RETURN r.id       AS id,
                       r.name     AS name,
                       coalesce(r['language'], '') AS language,
                       count(DISTINCT api) AS api_count
                ORDER BY r.name
            """, suite_id=suite_id).data()

            coverage = session.run("""
                MATCH (c:Class)
                RETURN count(c) AS total,
                       count(CASE WHEN c.wiki_summary IS NOT NULL THEN 1 END) AS with_wiki
            """).single()

        data            = dict(suite_row)
        data["repos"]   = repos
        total           = coverage["total"] if coverage else 0
        with_wiki       = coverage["with_wiki"] if coverage else 0
        data["coverage"] = {
            "total_classes":      total,
            "wiki_coverage":      with_wiki,
            "coverage_pct":       round(with_wiki / total * 100, 1) if total else 0,
        }
        return data
    except HTTPException:
        raise
    except (AuthError, ServiceUnavailable, Neo4jError) as exc:
        raise _neo4j_503(exc)
    finally:
        driver.close()


@router.post("/bootstrap")
def bootstrap_suites():
    """Write all suites from config/suites.json into Neo4j."""
    from pipeline.graph.suite_writer import write_suite_config
    driver = get_driver()
    try:
        counts = write_suite_config(driver)
        return {"status": "ok", **counts}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except (AuthError, ServiceUnavailable, Neo4jError) as exc:
        raise _neo4j_503(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"suite bootstrap failed: {exc}")
    finally:
        driver.close()
