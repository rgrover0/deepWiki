"""
Project / Repository CRUD routes.

POST   /project                create a new Repository node linked to a Suite
PATCH  /project/{id}           update Repository metadata
DELETE /project/{id}           detach-delete a Repository node

POST   /project/suite          create a new ApplicationSuite node
PATCH  /project/suite/{id}     update Suite metadata
DELETE /project/suite/{id}     detach-delete a Suite node
"""

import re
import uuid
from threading import Thread
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipeline.graph.schema import get_driver
from pipeline.project_bootstrap import start_project_bootstrap

router = APIRouter()


# ──────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────

class CreateRepoRequest(BaseModel):
    name: str
    description: str = ""
    story: str = ""
    suite_id: str
    tech_stack: list[str] = []
    repository_url: str = ""
    confluence_link: str = ""
    architecture_diagram: str = ""
    language: str = ""
    status: str = "active"


class UpdateRepoRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    story: Optional[str] = None
    suite_id: Optional[str] = None
    tech_stack: Optional[list[str]] = None
    repository_url: Optional[str] = None
    confluence_link: Optional[str] = None
    architecture_diagram: Optional[str] = None
    language: Optional[str] = None
    status: Optional[str] = None


class CreateSuiteRequest(BaseModel):
    name: str
    description: str = ""


class UpdateSuiteRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ──────────────────────────────────────────────
# Suite CRUD  (must be defined before /{id} routes to avoid path collision)
# ──────────────────────────────────────────────

@router.post("/suite", status_code=201)
def create_suite(body: CreateSuiteRequest):
    suite_id = _slugify(body.name) or str(uuid.uuid4())
    driver = get_driver()
    try:
        with driver.session() as session:
            existing = session.run(
                "MATCH (s:ApplicationSuite {id: $id}) RETURN s.id",
                id=suite_id,
            ).single()
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Suite with id '{suite_id}' already exists",
                )
            session.run(
                """
                CREATE (s:ApplicationSuite {
                    id:          $id,
                    name:        $name,
                    description: $description
                })
                """,
                id=suite_id,
                name=body.name,
                description=body.description,
            )
    finally:
        driver.close()
    return {"id": suite_id, "name": body.name, "description": body.description}


@router.patch("/suite/{suite_id}")
def update_suite(suite_id: str, body: UpdateSuiteRequest):
    driver = get_driver()
    try:
        with driver.session() as session:
            existing = session.run(
                "MATCH (s:ApplicationSuite {id: $id}) RETURN s",
                id=suite_id,
            ).single()
            if not existing:
                raise HTTPException(status_code=404, detail=f"Suite '{suite_id}' not found")

            updates = {k: v for k, v in body.model_dump().items() if v is not None}
            if not updates:
                return {"id": suite_id, "updated": []}

            set_clauses = ", ".join(f"s.{k} = ${k}" for k in updates)
            session.run(
                f"MATCH (s:ApplicationSuite {{id: $id}}) SET {set_clauses}",
                id=suite_id,
                **updates,
            )
    finally:
        driver.close()
    return {"id": suite_id, "updated": list(updates.keys())}


@router.delete("/suite/{suite_id}", status_code=204)
def delete_suite(suite_id: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(
                "MATCH (s:ApplicationSuite {id: $id}) DETACH DELETE s RETURN count(s) AS deleted",
                id=suite_id,
            ).single()
            if not result or result["deleted"] == 0:
                raise HTTPException(status_code=404, detail=f"Suite '{suite_id}' not found")
    finally:
        driver.close()


# ──────────────────────────────────────────────
# Repository CRUD
# ──────────────────────────────────────────────

@router.post("", status_code=201)
def create_project(body: CreateRepoRequest):
    repo_id = _slugify(body.name) or str(uuid.uuid4())
    driver = get_driver()
    try:
        with driver.session() as session:
            existing = session.run(
                "MATCH (r:Repository {id: $id}) RETURN r.id",
                id=repo_id,
            ).single()
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Repository with id '{repo_id}' already exists",
                )

            suite_row = session.run(
                "MATCH (s:ApplicationSuite {id: $id}) RETURN s.id",
                id=body.suite_id,
            ).single()
            if not suite_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Suite '{body.suite_id}' not found",
                )

            session.run(
                """
                MATCH (s:ApplicationSuite {id: $suite_id})
                CREATE (r:Repository {
                    id:                   $id,
                    name:                 $name,
                    description:          $description,
                    story:                $story,
                    tech_stack:           $tech_stack,
                    repository_url:       $repository_url,
                    confluence_link:      $confluence_link,
                    architecture_diagram: $architecture_diagram,
                    language:             $language,
                    status:               $status
                })
                CREATE (s)-[:HAS_REPO]->(r)
                """,
                id=repo_id,
                suite_id=body.suite_id,
                name=body.name,
                description=body.description,
                story=body.story,
                tech_stack=body.tech_stack,
                repository_url=body.repository_url,
                confluence_link=body.confluence_link,
                architecture_diagram=body.architecture_diagram,
                language=body.language,
                status=body.status,
            )
    finally:
        driver.close()

    if body.repository_url.strip() or body.confluence_link.strip():
        start_project_bootstrap(
            repo_id=repo_id,
            repo_url=body.repository_url.strip(),
            suite_id=body.suite_id,
            confluence_link=body.confluence_link.strip(),
        )

    return {
        "id": repo_id,
        "name": body.name,
        "suite_id": body.suite_id,
        "status": body.status,
        "ingestion_started": bool(body.repository_url.strip() or body.confluence_link.strip()),
    }


@router.get("/all")
def list_all_repos():
    """Return every Repository node regardless of suite membership."""
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (r:Repository)
                OPTIONAL MATCH (s:ApplicationSuite)-[:HAS_REPO]->(r)
                RETURN r.id                              AS id,
                       coalesce(r.name, r.id)            AS name,
                       coalesce(r.description, '')        AS description,
                       coalesce(r.language, '')           AS language,
                       coalesce(r.repository_url, '')     AS repository_url,
                       coalesce(r.confluence_link, '')    AS confluence_link,
                       coalesce(r.status, 'active')       AS status,
                       coalesce(r.tech_stack, [])         AS tech_stack,
                       coalesce(s.id, '')                 AS suite_id,
                       coalesce(s.name, '')               AS suite_name
                ORDER BY name
            """)
            return {"repos": [dict(r) for r in result]}
    finally:
        driver.close()


@router.patch("/{repo_id}")
def update_project(repo_id: str, body: UpdateRepoRequest):
    driver = get_driver()
    try:
        with driver.session() as session:
            existing = session.run(
                "MATCH (r:Repository {id: $id}) RETURN r",
                id=repo_id,
            ).single()
            if not existing:
                raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found")

            raw = body.model_dump()
            # Handle suite reassignment separately
            new_suite_id = raw.pop("suite_id", None)

            updates = {k: v for k, v in raw.items() if v is not None}

            if updates:
                set_clauses = ", ".join(f"r.{k} = ${k}" for k in updates)
                session.run(
                    f"MATCH (r:Repository {{id: $id}}) SET {set_clauses}",
                    id=repo_id,
                    **updates,
                )

            if new_suite_id:
                suite_row = session.run(
                    "MATCH (s:ApplicationSuite {id: $id}) RETURN s.id",
                    id=new_suite_id,
                ).single()
                if not suite_row:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Suite '{new_suite_id}' not found",
                    )
                session.run(
                    """
                    MATCH (r:Repository {id: $repo_id})
                    OPTIONAL MATCH (old:ApplicationSuite)-[rel:HAS_REPO]->(r) DELETE rel
                    WITH r
                    MATCH (s:ApplicationSuite {id: $suite_id})
                    CREATE (s)-[:HAS_REPO]->(r)
                    """,
                    repo_id=repo_id,
                    suite_id=new_suite_id,
                )
    finally:
        driver.close()
    return {"id": repo_id, "updated": list(updates.keys()) + (["suite_id"] if new_suite_id else [])}


@router.delete("/{repo_id}", status_code=204)
def delete_project(repo_id: str):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(
                "MATCH (r:Repository {id: $id}) DETACH DELETE r RETURN count(r) AS deleted",
                id=repo_id,
            ).single()
            if not result or result["deleted"] == 0:
                raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found")
    finally:
        driver.close()
