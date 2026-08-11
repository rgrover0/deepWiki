"""
Admin pipeline routes — Build Now / Re-index flow.

POST /admin/onboard-repo        create repo in graph + start full ingestion pipeline
GET  /admin/status/{repo_id}    poll job progress (2-second polling from Angular)
GET  /admin/jobs                list all active/recent jobs (debug)
POST /admin/reindex/{repo_id}   re-trigger ingestion for an existing repo

Ingestion runs in a pipeline subprocess (``python -m pipeline.admin_cli``).
Job progress is shared via ``core.jobs`` (file-backed) — api never imports pipeline.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.pipeline_gateway import run_cli
from core import jobs as job_store
from core.graph.schema import get_driver

logger = logging.getLogger(__name__)

REPO_CLONE_DIR = os.environ.get("REPO_CLONE_DIR", "repos")

router = APIRouter(prefix="/admin", tags=["Admin"])


class OnboardRequest(BaseModel):
    name: str
    suite_id: str
    repo_url: str = ""
    confluence_link: str = ""
    description: str = ""
    story: str = ""
    tech_stack: list[str] = []
    architecture_diagram: str = ""
    status: str = "active"


class RepairLinksRequest(BaseModel):
    fallback_suite_id: str = "dummy-suite"
    fallback_suite_name: str = "Dummy Suite"
    dry_run: bool = False
    create_dummy_repo: bool = True


DUMMY_SUITE_ID = "dummy-suite"
DUMMY_SUITE_NAME = "Dummy Suite"
DUMMY_REPO_ID = "dummy-repo"
DUMMY_REPO_NAME = "Dummy Repository (Edit Me)"


def _slugify(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _repo_id_from_input(project_name: str, repo_url: str) -> str:
    """Prefer URL-derived repo id; fallback to project name."""
    import re

    raw = (repo_url or "").strip().rstrip("/")
    if raw:
        for fragment in ("/tree/", "/blob/"):
            if fragment in raw:
                raw = raw.split(fragment)[0]
        leaf = raw.split("/")[-1].replace(".git", "").strip()
        if leaf:
            return re.sub(r"[^a-z0-9]+", "-", leaf.lower()).strip("-")

    return _slugify(project_name) or "repo"


def _dir_size_bytes(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                continue
    return total



def run_orphan_repair(
    *,
    fallback_suite_id: str = DUMMY_SUITE_ID,
    fallback_suite_name: str = DUMMY_SUITE_NAME,
    dry_run: bool = False,
    create_dummy_repo: bool = True,
) -> dict:
    """
    Repair orphan repositories and optionally ensure a dummy repo exists.

    This function is used by both startup auto-repair and /admin/repair-links.
    """
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run(
                """
                MERGE (s:ApplicationSuite {id: $id})
                ON CREATE SET s.name = $name,
                              s.description = 'Auto-created fallback suite for orphan repositories'
                """,
                id=fallback_suite_id,
                name=fallback_suite_name,
            )

            orphan_count = session.run(
                """
                MATCH (r:Repository)
                WHERE NOT EXISTS { MATCH (:ApplicationSuite)-[:HAS_REPO]->(r) }
                RETURN count(r) AS count
                """
            ).single()["count"]

            if dry_run:
                repaired = 0
                dummy_created = False
            else:
                repaired = session.run(
                    """
                    MATCH (fallback:ApplicationSuite {id: $fallback_suite_id})
                    MATCH (r:Repository)
                    WHERE NOT EXISTS { MATCH (:ApplicationSuite)-[:HAS_REPO]->(r) }
                    OPTIONAL MATCH (target:ApplicationSuite {id: r.suite_id})
                    WITH r, coalesce(target, fallback) AS suite
                    MERGE (suite)-[:HAS_REPO]->(r)
                    SET r.suite_id = suite.id,
                        r.is_dummy = coalesce(r.is_dummy, false)
                    RETURN count(r) AS repaired
                    """,
                    fallback_suite_id=fallback_suite_id,
                ).single()["repaired"]

                dummy_created = False
                if create_dummy_repo:
                    row = session.run(
                        """
                        MATCH (s:ApplicationSuite {id: $suite_id})
                        MERGE (r:Repository {id: $repo_id})
                        ON CREATE SET r.name = $repo_name,
                                      r.description = 'Placeholder project created by auto-repair. Edit this entry in Admin.',
                                      r.story = '',
                                      r.tech_stack = [],
                                      r.repository_url = '',
                                      r.confluence_link = '',
                                      r.architecture_diagram = '',
                                      r.language = '',
                                      r.status = 'beta',
                                      r.suite_id = $suite_id,
                                      r.is_dummy = true
                        ON MATCH SET  r.suite_id = coalesce(r.suite_id, $suite_id),
                                      r.is_dummy = coalesce(r.is_dummy, true)
                        MERGE (s)-[:HAS_REPO]->(r)
                        RETURN exists((r)<-[:HAS_REPO]-(:ApplicationSuite {id: $suite_id})) AS linked
                        """,
                        suite_id=fallback_suite_id,
                        repo_id=DUMMY_REPO_ID,
                        repo_name=DUMMY_REPO_NAME,
                    ).single()
                    dummy_created = bool(row and row["linked"])
    finally:
        driver.close()

    return {
        "dry_run": dry_run,
        "orphans_found": orphan_count,
        "repaired": repaired,
        "fallback_suite_id": fallback_suite_id,
        "dummy_repo_id": DUMMY_REPO_ID if create_dummy_repo else "",
        "dummy_repo_created_or_linked": dummy_created,
    }


def _start_ingestion(repo_id: str, repo_url: str, suite_id: str, confluence_link: str) -> None:
    """Create job record and spawn pipeline CLI in the background."""
    job = job_store.make_job()
    job_store.save_job(repo_id, job)
    run_cli(
        "onboard",
        "--repo-id", repo_id,
        "--repo-url", repo_url or "",
        "--suite-id", suite_id,
        "--confluence-link", confluence_link or "",
        background=True,
    )


@router.post("/onboard-repo", status_code=202)
def onboard_repo(body: OnboardRequest):
    """Save project metadata to Neo4j then start the full ingestion pipeline."""
    import uuid as _uuid_mod

    if not body.name.strip():
        raise HTTPException(status_code=422, detail="Project name is required")

    if body.repo_url.strip():
        raw = body.repo_url.strip()
        looks_valid = (
            raw.startswith("http://") or raw.startswith("https://")
            or raw.startswith("github.com/") or raw.startswith("gitlab.com/")
            or raw.startswith("bitbucket.org/")
        )
        if not looks_valid:
            raise HTTPException(
                status_code=422,
                detail=f"Repository URL '{raw[:80]}' doesn't look valid. Use https://github.com/org/repo",
            )

    base_repo_id = _repo_id_from_input(body.name, body.repo_url)
    repo_id = base_repo_id or str(_uuid_mod.uuid4())

    driver = get_driver()
    try:
        with driver.session() as session:
            candidate = repo_id
            i = 2
            while session.run("MATCH (r:Repository {id: $id}) RETURN r.id", id=candidate).single():
                candidate = f"{repo_id}-{i}"
                i += 1
            repo_id = candidate

            suite_row = session.run(
                "MATCH (s:ApplicationSuite {id: $id}) RETURN s.id",
                id=body.suite_id,
            ).single()
            if not suite_row:
                raise HTTPException(status_code=404, detail=f"Suite '{body.suite_id}' not found")

            session.run(
                """
                MERGE (r:Repository {id: $id})
                SET r.name                 = $name,
                    r.description          = $description,
                    r.story                = $story,
                    r.suite_id             = $suite_id,
                    r.is_dummy             = false,
                    r.tech_stack           = $tech_stack,
                    r.repository_url       = $repository_url,
                    r.confluence_link      = $confluence_link,
                    r.architecture_diagram = $architecture_diagram,
                    r.status               = $status
                WITH r
                MATCH (s:ApplicationSuite {id: $suite_id})
                MERGE (s)-[:HAS_REPO]->(r)
                """,
                id=repo_id,
                name=body.name,
                description=body.description,
                story=body.story,
                tech_stack=body.tech_stack,
                repository_url=body.repo_url,
                confluence_link=body.confluence_link,
                architecture_diagram=body.architecture_diagram,
                status=body.status,
                suite_id=body.suite_id,
            )
    finally:
        driver.close()

    _start_ingestion(repo_id, body.repo_url, body.suite_id, body.confluence_link)
    return {"repo_id": repo_id, "status": "started"}


@router.get("/status/{repo_id}")
def get_status(repo_id: str):
    """Poll pipeline job progress (polled every 2 s by Angular)."""
    job = job_store.load_job(repo_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"No active job for '{repo_id}'")
    return job


@router.get("/jobs")
def list_jobs():
    """List all recent pipeline jobs (debug)."""
    return {
        "jobs": [
            {
                "repo_id": j.get("repo_id"),
                "status": j.get("status"),
                "progress": j.get("progress"),
                "current_step": j.get("current_step"),
                "error": j.get("error"),
            }
            for j in job_store.list_jobs()
        ]
    }


@router.get("/runtime/storage")
def runtime_storage():
    """Return disk usage and writeability details for the running container."""
    paths = [Path("/"), Path("/app"), Path("/tmp"), Path("repos")]
    usage = []
    for path in paths:
        if not path.exists():
            continue
        du = shutil.disk_usage(str(path))
        usage.append({
            "path": str(path),
            "total_bytes": du.total,
            "used_bytes": du.used,
            "free_bytes": du.free,
        })

    repos_dir = Path("repos")
    repos_size = _dir_size_bytes(repos_dir)

    writable = False
    write_error = ""
    try:
        probe = Path(tempfile.gettempdir()) / "deepwiki-write-probe.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        writable = True
    except Exception as exc:
        write_error = str(exc)

    return {
        "cwd": str(Path.cwd()),
        "repos_exists": repos_dir.exists(),
        "repos_size_bytes": repos_size,
        "tmp_writable": writable,
        "tmp_write_error": write_error,
        "usage": usage,
    }


@router.get("/orphans")
def list_orphan_repositories():
    """List repositories that are not linked to any ApplicationSuite."""
    driver = get_driver()
    try:
        with driver.session() as session:
            rows = session.run(
                """
                MATCH (r:Repository)
                WHERE NOT EXISTS { MATCH (:ApplicationSuite)-[:HAS_REPO]->(r) }
                RETURN r.id AS id,
                       coalesce(r.name, r.id) AS name,
                       coalesce(r.suite_id, '') AS suite_id,
                       coalesce(r.repository_url, '') AS repository_url
                ORDER BY name
                """
            ).data()
    finally:
        driver.close()

    return {"count": len(rows), "repos": rows}


@router.post("/repair-links")
def repair_repository_links(body: RepairLinksRequest):
    return run_orphan_repair(
        fallback_suite_id=body.fallback_suite_id,
        fallback_suite_name=body.fallback_suite_name,
        dry_run=body.dry_run,
        create_dummy_repo=body.create_dummy_repo,
    )


@router.post("/reindex/{repo_id}", status_code=202)
def reindex_repo(repo_id: str):
    """Re-trigger full ingestion pipeline for an existing repository."""
    driver = get_driver()
    try:
        with driver.session() as session:
            row = session.run(
                """
                MATCH (s:ApplicationSuite)-[:HAS_REPO]->(r:Repository {id: $id})
                RETURN r.repository_url  AS url,
                       s.id              AS suite_id,
                       r.confluence_link AS confluence_link
                """,
                id=repo_id,
            ).single()
    finally:
        driver.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found")

    _start_ingestion(
        repo_id,
        row.get("url") or "",
        row.get("suite_id") or "",
        row.get("confluence_link") or "",
    )
    return {"repo_id": repo_id, "status": "started"}
