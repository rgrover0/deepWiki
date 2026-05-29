"""
Admin pipeline routes — Build Now / Re-index flow.

POST /admin/onboard-repo        create repo in graph + start full ingestion pipeline
GET  /admin/status/{repo_id}    poll job progress (2-second polling from Angular)
POST /admin/reindex/{repo_id}   re-trigger ingestion for an existing repo
"""

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
    "Cloning repository",
    "Parsing source files",
    "Writing knowledge graph",
    "Generating wiki summaries",
    "Extracting API contracts",
    "Embedding to Qdrant",
    "Matching API contracts",
    "Registering project",
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


# ────────────────────────────────────────────────────────────────────────────
# Job helpers
# ────────────────────────────────────────────────────────────────────────────

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
    done = sum(1 for s in job["steps"] if s["status"] == "done")
    job["progress"] = int(done / len(PIPELINE_STEPS) * 100)


def _step_skip(job: dict, idx: int, detail: str = "") -> None:
    job["steps"][idx]["status"] = "done"
    job["steps"][idx]["detail"] = detail or "skipped"
    done = sum(1 for s in job["steps"] if s["status"] == "done")
    job["progress"] = int(done / len(PIPELINE_STEPS) * 100)


def _step_error(job: dict, idx: int, detail: str) -> None:
    job["steps"][idx]["status"] = "error"
    job["steps"][idx]["detail"] = detail


def _slugify(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ────────────────────────────────────────────────────────────────────────────
# Pipeline runner (executes in daemon thread)
# ────────────────────────────────────────────────────────────────────────────

def _run_ingestion(repo_id: str, repo_url: str, suite_id: str, confluence_link: str) -> None:
    job = _JOBS[repo_id]
    driver = get_driver()
    graph_stats: dict = {}
    contract_count = 0

    try:
        # ── Step 0: Clone ──────────────────────────────────────────────────
        _step_start(job, 0)
        repo_path: Optional[Path] = None
        if repo_url.strip():
            from pipeline.ingestion.git_reader import clone_repo
            target = Path("repos") / repo_id
            clone_repo(repo_url, str(target))
            repo_path = target
            _step_done(job, 0, f"Cloned to repos/{repo_id}")
        else:
            _step_skip(job, 0, "No URL — skipped")

        # ── Detect language ────────────────────────────────────────────────
        is_ts = False
        if repo_path and repo_path.exists():
            is_ts = bool(next(
                (p for p in repo_path.rglob("*.ts")
                 if "node_modules" not in str(p).lower()), None
            ))

        # ── Step 1: Parse ──────────────────────────────────────────────────
        _step_start(job, 1)
        analysis_results: list = []
        if repo_path and repo_path.exists():
            if is_ts:
                from pipeline.ingestion.ts_analysis_client import (
                    analyse_files, is_service_healthy,
                )
                ts_files = [
                    str(p) for p in repo_path.rglob("*.ts")
                    if "node_modules" not in str(p).lower()
                ]
                if ts_files and is_service_healthy():
                    analysis_results = analyse_files(ts_files) or []
                    _step_done(job, 1, f"{len(ts_files)} TypeScript files")
                else:
                    _step_skip(job, 1, "TS analysis service unavailable")
            else:
                from pipeline.ingestion.git_reader import get_java_files
                from pipeline.ingestion.java_analysis_client import (
                    analyze_files, is_service_healthy,
                )
                java_files = get_java_files(str(repo_path))
                if java_files and is_service_healthy():
                    analysis_results = analyze_files(java_files) or []
                    _step_done(job, 1, f"{len(java_files)} Java files found")
                else:
                    _step_skip(job, 1, "Java analysis service unavailable")
        else:
            _step_skip(job, 1, "No repo to parse")

        # ── Step 2: Write knowledge graph ──────────────────────────────────
        _step_start(job, 2)
        if analysis_results:
            from pipeline.graph.writer import write_analysis
            graph_stats = write_analysis(driver, analysis_results)
            total = graph_stats.get("classes", 0) + graph_stats.get("methods", 0)
            _step_done(job, 2, f"{total} code units written")
        else:
            _step_skip(job, 2, "No analysis results")

        # ── Step 3: Wiki summaries ─────────────────────────────────────────
        _step_start(job, 3)
        wiki_by_class: dict[str, str] = {}
        method_summaries: dict[str, dict] = {}
        if analysis_results:
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
        else:
            _step_skip(job, 3, "No classes to summarise")

        # ── Step 4: API contracts ──────────────────────────────────────────
        _step_start(job, 4)
        if analysis_results:
            from pipeline.graph.api_writer import write_all_api_contracts
            from pipeline.graph.api_impact import run_api_impact_nightly
            from pipeline.graph.method_writer import write_all_method_data
            write_all_method_data(driver, analysis_results, method_summaries)
            contract_count = write_all_api_contracts(driver, analysis_results, repo_id)
            run_api_impact_nightly(driver)
            _step_done(job, 4, f"{contract_count} contracts extracted")
        else:
            _step_skip(job, 4, "No contracts")

        # ── Step 5: Embed to Qdrant ────────────────────────────────────────
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
                        payloads.append({"repo_id": repo_id, "class": cls["name"], "method": method["name"]})
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

        # ── Step 6: Match API contracts (FE ↔ BE) ─────────────────────────
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
                    _step_skip(job, 6, "No backend repo in suite to match against")
            except Exception as exc:
                _step_skip(job, 6, f"Skipped — {exc}")
        else:
            _step_skip(job, 6, "Java repo — no FE matching needed")

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

    except Exception as exc:
        running_idx = next(
            (i for i, s in enumerate(job["steps"]) if s["status"] == "running"), 0
        )
        _step_error(job, running_idx, str(exc))
        job["status"] = "error"
        job["error"] = str(exc)
    finally:
        driver.close()


# ────────────────────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────────────────────

@router.post("/onboard-repo", status_code=202)
def onboard_repo(body: OnboardRequest):
    """Create project metadata in Neo4j then start full ingestion pipeline."""
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
    """Poll pipeline job progress."""
    job = _JOBS.get(repo_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"No active job for '{repo_id}'")
    return {"repo_id": repo_id, **job}


@router.post("/reindex/{repo_id}", status_code=202)
def reindex_repo(repo_id: str):
    """Re-trigger full ingestion pipeline for an existing repository."""
    driver = get_driver()
    try:
        with driver.session() as session:
            row = session.run(
                """
                MATCH (s:ApplicationSuite)-[:HAS_REPO]->(r:Repository {id: $id})
                RETURN r.repository_url AS url,
                       s.id             AS suite_id,
                       r.confluence_link AS confluence_link
                """,
                id=repo_id,
            ).single()
    finally:
        driver.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found")

    repo_url       = row.get("url")            or ""
    suite_id       = row.get("suite_id")       or ""
    confluence_link = row.get("confluence_link") or ""

    _JOBS[repo_id] = _make_job()
    threading.Thread(
        target=_run_ingestion,
        args=(repo_id, repo_url, suite_id, confluence_link),
        daemon=True,
        name=f"admin-reindex-{repo_id}",
    ).start()

    return {"repo_id": repo_id, "status": "started"}
