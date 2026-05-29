"""
Admin pipeline routes — Build Now / Re-index flow.

POST /admin/onboard-repo        create repo in graph + start full ingestion pipeline
GET  /admin/status/{repo_id}    poll job progress (2-second polling from Angular)
GET  /admin/jobs                list all active/recent jobs (debug)
POST /admin/reindex/{repo_id}   re-trigger ingestion for an existing repo
"""

import shutil
import threading
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipeline.graph.schema import get_driver

router = APIRouter(prefix="/admin", tags=["Admin"])

# ── In-memory job state (per-process; fine for single-worker Railway deploy) ──
_JOBS: dict[str, dict] = {}

PIPELINE_STEPS = [
    "Cloning repository",       # 0 — critical
    "Parsing source files",     # 1 — critical
    "Writing knowledge graph",  # 2 — critical
    "Generating wiki summaries",# 3 — critical
    "Extracting API contracts", # 4 — critical
    "Embedding to Qdrant",      # 5 — optional (graceful skip)
    "Matching API contracts",   # 6 — optional
    "Registering project",      # 7 — always runs
]


# ────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ────────────────────────────────────────────────────────────────────────────

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


# ────────────────────────────────────────────────────────────────────────────
# Job / step helpers
# ────────────────────────────────────────────────────────────────────────────

class _PipelineAbort(Exception):
    """Raised to halt the pipeline after a critical step failure."""


def _make_job() -> dict:
    return {
        "status": "running",
        "progress": 0,
        "current_step": PIPELINE_STEPS[0],
        "steps": [{"label": s, "status": "pending", "detail": ""} for s in PIPELINE_STEPS],
        "stats": {},
        "error": None,
    }


def _step_start(job: dict, idx: int) -> None:
    job["current_step"] = PIPELINE_STEPS[idx]
    job["steps"][idx]["status"] = "running"


def _step_done(job: dict, idx: int, detail: str = "") -> None:
    job["steps"][idx]["status"] = "done"
    job["steps"][idx]["detail"] = detail
    _recalc_progress(job)


def _step_skip(job: dict, idx: int, detail: str = "") -> None:
    """Mark a non-critical step as skipped (shown as ✅ with grey detail)."""
    job["steps"][idx]["status"] = "skipped"
    job["steps"][idx]["detail"] = detail or "skipped"
    _recalc_progress(job)


def _fail(job: dict, idx: int, detail: str) -> None:
    """Mark step as error, set job to error, and raise to abort the pipeline."""
    job["steps"][idx]["status"] = "error"
    job["steps"][idx]["detail"] = detail
    job["status"] = "error"
    job["error"] = f"Step '{PIPELINE_STEPS[idx]}' failed: {detail}"
    raise _PipelineAbort(detail)


def _recalc_progress(job: dict) -> None:
    done = sum(1 for s in job["steps"] if s["status"] in ("done", "skipped"))
    job["progress"] = int(done / len(PIPELINE_STEPS) * 100)


def _slugify(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


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


# ────────────────────────────────────────────────────────────────────────────
# Clone helper — detects corrupt/empty dirs and re-clones
# ────────────────────────────────────────────────────────────────────────────

def _clone(repo_url: str, repo_id: str, job: dict) -> Path:
    """
    Clone the repo. If the target directory already exists:
      - valid git repo  → skip (already cloned, resume-safe)
      - empty / corrupt → wipe and re-clone
    Raises _PipelineAbort on any failure.
    """
    import git as _git

    url = repo_url.strip()
    if url.startswith("http") and not url.endswith(".git"):
        url = url.rstrip("/") + ".git"

    repos_dir = Path("repos")
    repos_dir.mkdir(parents=True, exist_ok=True)
    target = repos_dir / repo_id

    if target.exists():
        try:
            _git.Repo(str(target))
            _step_done(job, 0, f"Already cloned at repos/{repo_id}")
            return target
        except _git.InvalidGitRepositoryError:
            # Directory exists but is not a valid git repo — wipe it
            shutil.rmtree(str(target), ignore_errors=True)

    try:
        _git.Repo.clone_from(url, str(target), depth=1)
        _step_done(job, 0, f"Cloned to repos/{repo_id}")
        return target
    except Exception as exc:
        # Clean up any partial clone
        if target.exists():
            shutil.rmtree(str(target), ignore_errors=True)
        _fail(job, 0, str(exc))


# ────────────────────────────────────────────────────────────────────────────
# Pipeline runner (executes in daemon thread)
# ────────────────────────────────────────────────────────────────────────────

def _run_ingestion(repo_id: str, repo_url: str, suite_id: str, confluence_link: str) -> None:
    job = _JOBS[repo_id]
    driver = get_driver()
    graph_stats: dict = {}
    contract_count = 0
    analysis_results: list = []
    method_summaries: dict = {}
    is_ts = False

    try:
        # ── Step 0: Clone ──────────────────────────────────────────────────
        _step_start(job, 0)
        repo_path: Optional[Path] = None

        if repo_url.strip():
            repo_path = _clone(repo_url, repo_id, job)   # raises _PipelineAbort on failure
        else:
            # No URL provided — metadata-only mode, skip ingestion steps
            _step_skip(job, 0, "No repository URL — metadata-only mode")

        # ── Detect language ────────────────────────────────────────────────
        if repo_path and repo_path.exists():
            is_ts = bool(next(
                (p for p in repo_path.rglob("*.ts")
                 if "node_modules" not in str(p).lower()), None
            ))

        # ── Step 1: Parse ──────────────────────────────────────────────────
        _step_start(job, 1)

        if repo_path and repo_path.exists():
            if is_ts:
                from pipeline.ingestion.ts_analysis_client import (
                    analyse_files, is_service_healthy,
                )
                ts_files = [
                    str(p) for p in repo_path.rglob("*.ts")
                    if "node_modules" not in str(p).lower()
                ]
                if not ts_files:
                    _fail(job, 1, "No .ts files found in the cloned repository")
                if not is_service_healthy():
                    _fail(
                        job, 1,
                        "TypeScript analysis service is unreachable. "
                        "Ensure ts-analysis-service is running and TS_ANALYSIS_URL is set.",
                    )
                analysis_results = analyse_files(ts_files) or []
                if not analysis_results:
                    _fail(job, 1, "TypeScript analysis returned no results")
                _step_done(job, 1, f"{len(ts_files)} TypeScript files parsed")

            else:
                from pipeline.ingestion.git_reader import get_java_files
                from pipeline.ingestion.java_analysis_client import (
                    analyze_files, is_service_healthy,
                )
                java_files = get_java_files(str(repo_path))
                if not java_files:
                    _fail(job, 1, "No .java files found in the cloned repository")
                if not is_service_healthy():
                    _fail(
                        job, 1,
                        "Java analysis service is unreachable. "
                        "Ensure code-analysis-service is running (default port 8081) "
                        "and CODE_ANALYSIS_URL is set.",
                    )
                analysis_results = analyze_files(java_files) or []
                if not analysis_results:
                    _fail(job, 1, "Java analysis returned no results")
                _step_done(job, 1, f"{len(java_files)} Java files parsed")

        else:
            # No repo (metadata-only) — skip remaining ingestion steps
            _step_skip(job, 1, "No repository to parse")

        # ── Step 2: Write knowledge graph ──────────────────────────────────
        _step_start(job, 2)

        if analysis_results:
            try:
                from pipeline.graph.writer import write_analysis
                graph_stats = write_analysis(driver, analysis_results)
                total = graph_stats.get("classes", 0) + graph_stats.get("methods", 0)
                _step_done(job, 2, f"{total} code units written to graph")
            except Exception as exc:
                _fail(job, 2, str(exc))
        else:
            _step_skip(job, 2, "No analysis results to write")

        # ── Step 3: Wiki summaries ─────────────────────────────────────────
        _step_start(job, 3)
        wiki_by_class: dict[str, str] = {}

        if analysis_results:
            try:
                from pipeline.delta.updater import update_wiki_summary
                from pipeline.wiki.summarizer import summarize_methods

                class_lookup = {
                    cls["name"]: cls
                    for fr in analysis_results
                    for cls in fr.get("classes", [])
                }
                for cls_name, cls in class_lookup.items():
                    wiki_by_class[cls_name] = update_wiki_summary(cls)
                for cls_name, cls in class_lookup.items():
                    method_summaries[cls_name] = summarize_methods(
                        cls, wiki_by_class.get(cls_name, ""), delay=0.0
                    )
                _step_done(job, 3, f"{len(wiki_by_class)} class summaries generated")
            except Exception as exc:
                _fail(job, 3, str(exc))
        else:
            _step_skip(job, 3, "No classes to summarise")

        # ── Step 4: API contracts ──────────────────────────────────────────
        _step_start(job, 4)

        if analysis_results:
            try:
                from pipeline.graph.api_writer import write_all_api_contracts
                from pipeline.graph.api_impact import run_api_impact_nightly
                from pipeline.graph.method_writer import write_all_method_data

                write_all_method_data(driver, analysis_results, method_summaries)
                contract_count = write_all_api_contracts(driver, analysis_results, repo_id)
                run_api_impact_nightly(driver)
                _step_done(job, 4, f"{contract_count} contracts extracted")
            except Exception as exc:
                _fail(job, 4, str(exc))
        else:
            _step_skip(job, 4, "No code to extract contracts from")

        # ── Step 5: Embed to Qdrant (non-critical) ─────────────────────────
        _step_start(job, 5)
        try:
            from pipeline.embeddings.embedder import embed_batch, build_method_text
            from pipeline.embeddings.vector_store import get_client, COLLECTION
            from qdrant_client.models import PointStruct
            import uuid as _uuid

            client = get_client()
            texts: list[str] = []
            payloads: list[dict] = []
            for fr in analysis_results:
                for cls in fr.get("classes", []):
                    for method in cls.get("methods", []):
                        summary = method_summaries.get(cls["name"], {}).get(method["name"], "")
                        texts.append(build_method_text(cls["name"], method, summary))
                        payloads.append({
                            "repo_id": repo_id,
                            "class":  cls["name"],
                            "method": method["name"],
                        })
            if texts:
                vectors = embed_batch(texts)
                points = [
                    PointStruct(id=str(_uuid.uuid4()), vector=v, payload=p)
                    for v, p in zip(vectors, payloads)
                ]
                client.upsert(collection_name=COLLECTION, points=points)
                _step_done(job, 5, f"{len(points)} vectors stored")
            else:
                _step_skip(job, 5, "No methods to embed")
        except Exception as exc:
            _step_skip(job, 5, f"Qdrant unavailable — {exc}")

        # ── Step 6: Match API contracts FE ↔ BE (non-critical) ────────────
        _step_start(job, 6)
        if is_ts and analysis_results:
            try:
                from pipeline.graph.api_matcher import run_api_matching
                with driver.session() as session:
                    backend_row = session.run(
                        """
                        MATCH (s:ApplicationSuite {id: $suite_id})-[:HAS_REPO]->(r:Repository)
                        WHERE r.id <> $repo_id
                        OPTIONAL MATCH (r)-[:EXPOSES]->(a:APIContract)
                        WITH r, count(a) AS cnt WHERE cnt > 0
                        RETURN r.id AS repo_id ORDER BY cnt DESC LIMIT 1
                        """,
                        suite_id=suite_id, repo_id=repo_id,
                    ).single()
                if backend_row:
                    run_api_matching(driver, repo_id, backend_row["repo_id"], analysis_results)
                    _step_done(job, 6, "FE → BE contracts matched")
                else:
                    _step_skip(job, 6, "No backend repo with contracts in this suite")
            except Exception as exc:
                _step_skip(job, 6, f"Matching skipped — {exc}")
        else:
            _step_skip(job, 6, "Java repo — FE↔BE matching not needed")

        # ── Step 7: Confluence / finalise ──────────────────────────────────
        _step_start(job, 7)
        if confluence_link.strip():
            try:
                from pipeline.ingestion.confluence_ingester import ingest_page
                ingest_page(
                    url_or_id=confluence_link,
                    category="current",
                    module_tags=[],
                    suite_id=suite_id,
                )
                _step_done(job, 7, "Confluence page ingested")
            except Exception as exc:
                _step_skip(job, 7, f"Confluence skipped — {exc}")
        else:
            _step_done(job, 7, "Project registered in DeepWiki")

        # ── Finalise ───────────────────────────────────────────────────────
        code_units = (
            graph_stats.get("classes", 0)
            + graph_stats.get("methods", 0)
            + graph_stats.get("fields", 0)
        )
        job["stats"] = {"code_units": code_units, "contracts": contract_count}
        job["status"] = "done"
        job["progress"] = 100

    except _PipelineAbort:
        # Error state already set by _fail() — just ensure remaining steps show as cancelled
        for step in job["steps"]:
            if step["status"] == "pending":
                step["status"] = "cancelled"
            elif step["status"] == "running":
                step["status"] = "error"
                step["detail"] = step["detail"] or "Aborted"

    except Exception as exc:
        # Unexpected error outside a named step
        running_idx = next(
            (i for i, s in enumerate(job["steps"]) if s["status"] == "running"),
            None,
        )
        if running_idx is not None:
            job["steps"][running_idx]["status"] = "error"
            job["steps"][running_idx]["detail"] = str(exc)
        for step in job["steps"]:
            if step["status"] == "pending":
                step["status"] = "cancelled"
        job["status"] = "error"
        job["error"] = str(exc)

    finally:
        driver.close()


# ────────────────────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────────────────────

@router.post("/onboard-repo", status_code=202)
def onboard_repo(body: OnboardRequest):
    """Save project metadata to Neo4j then start the full ingestion pipeline."""
    import re, uuid as _uuid_mod

    repo_id = re.sub(r"[^a-z0-9]+", "-", body.name.lower()).strip("-") or str(_uuid_mod.uuid4())

    driver = get_driver()
    try:
        with driver.session() as session:
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

    _JOBS[repo_id] = _make_job()
    threading.Thread(
        target=_run_ingestion,
        args=(repo_id, body.repo_url, body.suite_id, body.confluence_link),
        daemon=True,
        name=f"admin-ingest-{repo_id}",
    ).start()

    return {"repo_id": repo_id, "status": "started"}


@router.get("/status/{repo_id}")
def get_status(repo_id: str):
    """Poll pipeline job progress (polled every 2 s by Angular)."""
    job = _JOBS.get(repo_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"No active job for '{repo_id}'")
    return {"repo_id": repo_id, **job}


@router.get("/jobs")
def list_jobs():
    """List all recent pipeline jobs (debug)."""
    return {
        "jobs": [
            {
                "repo_id":      rid,
                "status":       j["status"],
                "progress":     j["progress"],
                "current_step": j.get("current_step"),
                "error":        j.get("error"),
            }
            for rid, j in _JOBS.items()
        ]
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

    repo_url        = row.get("url")             or ""
    suite_id        = row.get("suite_id")        or ""
    confluence_link = row.get("confluence_link") or ""

    _JOBS[repo_id] = _make_job()
    threading.Thread(
        target=_run_ingestion,
        args=(repo_id, repo_url, suite_id, confluence_link),
        daemon=True,
        name=f"admin-reindex-{repo_id}",
    ).start()

    return {"repo_id": repo_id, "status": "started"}
