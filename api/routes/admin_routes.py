"""
Admin pipeline routes — Build Now / Re-index flow.

POST /admin/onboard-repo        create repo in graph + start full ingestion pipeline
GET  /admin/status/{repo_id}    poll job progress (2-second polling from Angular)
GET  /admin/jobs                list all active/recent jobs (debug)
POST /admin/reindex/{repo_id}   re-trigger ingestion for an existing repo
"""

import logging
import os
import shutil
import subprocess
import threading
import traceback
from pathlib import Path
from typing import Optional
import tempfile

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipeline.graph.schema import get_driver

logger = logging.getLogger(__name__)

# Allow Railway env override for clone directory (use /tmp/repos if /app/repos is read-only)
REPO_CLONE_DIR = os.environ.get("REPO_CLONE_DIR", "repos")

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
        "logs": [],
    }


def _log(job: dict, msg: str) -> None:
    """Append a log line to job state and emit to Python logger."""
    logger.info("[pipeline] %s", msg)
    job.setdefault("logs", []).append(msg)
    if len(job["logs"]) > 100:
        job["logs"] = job["logs"][-100:]


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


# ────────────────────────────────────────────────────────────────────────────
# Clone helper — detects corrupt/empty dirs and re-clones
# ────────────────────────────────────────────────────────────────────────────

def _clone(repo_url: str, repo_id: str, job: dict) -> Path:
    """
    Clone repo via `git clone --depth 1`. Detects corrupt dirs and re-clones.
    Uses subprocess so git stderr is captured as a clean string.
    Raises _PipelineAbort on any failure.
    """
    raw = (repo_url or "").strip()
    if not raw:
        _fail(job, 0, "Repository URL is empty")

    # Normalise URL: add https://, strip /tree/ and /blob/ suffixes
    normalized = raw
    for prefix in ("github.com/", "gitlab.com/", "bitbucket.org/"):
        if normalized.startswith(prefix):
            normalized = "https://" + normalized
            break
    for fragment in ("/tree/", "/blob/"):
        if fragment in normalized:
            normalized = normalized.split(fragment)[0]

    candidates: list[str] = []
    for url in (normalized, raw):
        if not url:
            continue
        base = url.rstrip("/")
        if base not in candidates:
            candidates.append(base)
        if base.startswith("http") and not base.endswith(".git"):
            with_git = base + ".git"
            if with_git not in candidates:
                candidates.append(with_git)

    repos_dir = Path(REPO_CLONE_DIR)
    repos_dir.mkdir(parents=True, exist_ok=True)
    target = repos_dir / repo_id

    # Resume-safe: valid git repo already present → skip
    if target.exists() and (target / ".git").exists():
        _log(job, f"Repo already cloned at {target}")
        _step_done(job, 0, f"Already cloned — {target}")
        return target

    # Corrupt / partial dir → wipe before retrying
    if target.exists():
        _log(job, f"Wiping incomplete clone dir: {target}")
        shutil.rmtree(str(target), ignore_errors=True)

    git_errors: list[str] = []
    for url in candidates:
        _log(job, f"git clone --depth 1 {url}")
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", url, str(target)],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode == 0:
                _log(job, f"Clone succeeded → {target}")
                _step_done(job, 0, f"Cloned {url.split('/')[-1].replace('.git', '')}")
                return target
            stderr = (result.stderr or result.stdout or "non-zero exit").strip()
            short_err = stderr.splitlines()[-1][:200] if stderr else "clone failed"
            git_errors.append(f"{url}: {short_err}")
            _log(job, f"Clone failed for {url}: {short_err}")
            if target.exists():
                shutil.rmtree(str(target), ignore_errors=True)
        except FileNotFoundError:
            _fail(job, 0, "git binary not found. Ensure git is installed in the container.")
        except subprocess.TimeoutExpired:
            git_errors.append(f"{url}: timed out after 180 s")
            _log(job, f"Clone timed out: {url}")
            if target.exists():
                shutil.rmtree(str(target), ignore_errors=True)
        except Exception as exc:
            short = str(exc)[:200]
            git_errors.append(f"{url}: {short}")
            _log(job, f"Clone error {url}: {short}")
            if target.exists():
                shutil.rmtree(str(target), ignore_errors=True)

    summary = " | ".join(git_errors[:2]) if git_errors else "clone failed"
    _fail(job, 0, summary[:500])


# ────────────────────────────────────────────────────────────────────────────
# Pipeline runner (executes in daemon thread)
# ────────────────────────────────────────────────────────────────────────────

def _run_ingestion(repo_id: str, repo_url: str, suite_id: str, confluence_link: str) -> None:
    job = _JOBS[repo_id]
    driver = None
    graph_stats: dict = {}
    contract_count = 0
    analysis_results: list = []
    method_summaries: dict = {}
    is_ts = False

    try:
        _log(job, f"Pipeline started: repo_id={repo_id} url={repo_url or '(none)'} suite={suite_id}")
        driver = get_driver()
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
                    analyse_files_detailed, is_service_healthy,
                )
                ts_files = [
                    str(p) for p in repo_path.rglob("*.ts")
                    if "node_modules" not in str(p).lower()
                ]
                _log(job, f"TypeScript parse candidate files: {len(ts_files)}")
                if not ts_files:
                    _fail(job, 1, "No .ts files found in the cloned repository")
                if not is_service_healthy():
                    _fail(
                        job, 1,
                        "TypeScript analysis service is unreachable. "
                        "Ensure ts-analysis-service is running and TS_ANALYSIS_URL is set.",
                    )
                analysis_results, parse_errors = analyse_files_detailed(ts_files)
                analysis_results = analysis_results or []
                parse_errors = parse_errors or []
                if parse_errors:
                    for err in parse_errors[:8]:
                        _log(job, f"TS parse error: {err.get('file','<unknown>')} :: {err.get('error','unknown')}")
                    if len(parse_errors) > 8:
                        _log(job, f"TS parse errors truncated: {len(parse_errors) - 8} more")
                if not analysis_results:
                    detail = (
                        f"TypeScript analysis returned no results. "
                        f"attempted={len(ts_files)}, parse_errors={len(parse_errors)}"
                    )
                    if parse_errors:
                        detail += f". first_error={parse_errors[0].get('error', '')[:180]}"
                    _fail(job, 1, detail)
                _log(job, f"TypeScript parse output units: {len(analysis_results)}")
                _step_done(job, 1, f"{len(ts_files)} TypeScript files parsed")

            else:
                from pipeline.ingestion.git_reader import get_java_files
                from pipeline.ingestion.java_analysis_client import (
                    analyze_files_detailed, is_service_healthy,
                )
                java_files = get_java_files(str(repo_path))
                _log(job, f"Java parse candidate files: {len(java_files)}")
                if not java_files:
                    _fail(job, 1, "No .java files found in the cloned repository")
                if not is_service_healthy():
                    _fail(
                        job, 1,
                        "Java analysis service is unreachable. "
                        "Ensure code-analysis-service is running (default port 8081) "
                        "and CODE_ANALYSIS_URL is set.",
                    )
                analysis_results, parse_errors = analyze_files_detailed(java_files)
                analysis_results = analysis_results or []
                parse_errors = parse_errors or []

                # Log every HTTP-error failure (with response body) so they appear in UI logs
                if parse_errors:
                    _log(job, f"Java parse: {len(parse_errors)} files failed (HTTP errors / exceptions)")
                    for err in parse_errors[:10]:
                        _log(job, f"  ✗ {Path(err.get('file','<unknown>')).name} — {err.get('error','?')[:220]}")
                    if len(parse_errors) > 10:
                        _log(job, f"  … {len(parse_errors) - 10} more failures (see server logs)")

                parsed_count = len(analysis_results)
                total_attempted = len(java_files)
                _log(job, f"Java parse results: {parsed_count}/{total_attempted} files yielded classes")

                if not analysis_results:
                    detail = (
                        f"Java analysis yielded no class data. "
                        f"attempted={total_attempted}, http_errors={len(parse_errors)}"
                    )
                    if parse_errors:
                        detail += f". first_error={parse_errors[0].get('error', '')[:200]}"
                    _fail(job, 1, detail)
                _step_done(job, 1, f"{parsed_count}/{total_attempted} Java files produced classes")

        else:
            # No repo (metadata-only) — skip remaining ingestion steps
            _step_skip(job, 1, "No repository to parse")

        # ── Step 2: Write knowledge graph ──────────────────────────────────
        _step_start(job, 2)

        if analysis_results:
            try:
                from pipeline.graph.writer import write_analysis
                graph_stats = write_analysis(
                    driver,
                    analysis_results,
                    repo_id=repo_id,
                    suite_id=suite_id,
                )
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

                write_all_method_data(
                    driver,
                    analysis_results,
                    method_summaries,
                    repo_id=repo_id,
                )
                contract_count = write_all_api_contracts(
                    driver,
                    analysis_results,
                    repo_id=repo_id,
                    suite_id=suite_id,
                )
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
            from pipeline.embeddings.vector_store import get_client, COLLECTION, ensure_required_collections
            from qdrant_client.models import PointStruct
            import uuid as _uuid

            client = get_client()
            ensure_required_collections(client)
            texts: list[str] = []
            payloads: list[dict] = []
            for fr in analysis_results:
                for cls in fr.get("classes", []):
                    for method in cls.get("methods", []):
                        summary = method_summaries.get(cls["name"], {}).get(method["name"], "")
                        texts.append(build_method_text(cls["name"], method, summary))
                        payloads.append({
                            # Keep payload contract aligned with semantic_search + /ask.
                            "name": cls["name"],
                            "class_name": cls["name"],
                            "unit_type": "method",
                            "logic_summary": summary,
                            "repo_id": repo_id,
                            "suite_id": suite_id,
                            "method_name": method["name"],
                        })
            if texts:
                _log(job, f"Embedding {len(texts)} methods for Qdrant...")
                vectors = embed_batch(texts)
                points = [
                    PointStruct(id=str(_uuid.uuid4()), vector=v, payload=p)
                    for v, p in zip(vectors, payloads)
                ]
                _log(job, f"Upserting {len(points)} vectors into '{COLLECTION}'")
                client.upsert(collection_name=COLLECTION, points=points)
                _step_done(job, 5, f"{len(points)} vectors stored")
            else:
                _step_skip(job, 5, "No methods to embed")
        except Exception as exc:
            _log(job, f"Qdrant embed step failed: {exc}")
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
        # Error state already set by _fail() — mark remaining steps as cancelled
        _log(job, f"Pipeline aborted: {job.get('error', '')}")
        for step in job["steps"]:
            if step["status"] == "pending":
                step["status"] = "cancelled"
            elif step["status"] == "running":
                step["status"] = "error"
                step["detail"] = step["detail"] or "Aborted"

    except Exception as exc:
        tb = traceback.format_exc()
        _log(job, f"Unexpected pipeline error: {exc}\n{tb}")
        running_idx = next(
            (i for i, s in enumerate(job["steps"]) if s["status"] == "running"),
            None,
        )
        if running_idx is not None:
            job["steps"][running_idx]["status"] = "error"
            job["steps"][running_idx]["detail"] = str(exc)[:300]
        for step in job["steps"]:
            if step["status"] == "pending":
                step["status"] = "cancelled"
        job["status"] = "error"
        job["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"

    finally:
        if driver:
            try:
                driver.close()
            except Exception:
                pass


# ────────────────────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────────────────────

@router.post("/onboard-repo", status_code=202)
def onboard_repo(body: OnboardRequest):
    """Save project metadata to Neo4j then start the full ingestion pipeline."""
    import re, uuid as _uuid_mod

    if not body.name.strip():
        raise HTTPException(status_code=422, detail="Project name is required")

    if body.repo_url.strip():
        raw = body.repo_url.strip()
        # Accept https://, http://, or bare github.com/... forms; reject everything else
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
            # Avoid collisions for unrelated projects with same display name.
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
