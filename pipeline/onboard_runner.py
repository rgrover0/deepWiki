"""Admin onboard / reindex ingestion runner (pipeline package)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import traceback
from pathlib import Path
from typing import Optional

from core.graph.schema import get_driver
from core import jobs as job_store

logger = logging.getLogger(__name__)

REPO_CLONE_DIR = os.environ.get("REPO_CLONE_DIR", "repos")
PIPELINE_STEPS = job_store.PIPELINE_STEPS


def _persist(repo_id: str, job: dict) -> None:
    job_store.save_job(repo_id, job)

class _PipelineAbort(Exception):
    """Raised to halt the pipeline after a critical step failure."""


def _make_job() -> dict:
    job = job_store.make_job()
    # UI expects "label" key on steps
    for step, name in zip(job["steps"], PIPELINE_STEPS):
        step["label"] = name
        step.pop("name", None)
    return job


def _log(repo_id: str, job: dict, msg: str) -> None:
    """Append a log line to job state and emit to Python logger."""
    logger.info("[pipeline] %s", msg)
    job.setdefault("logs", []).append(msg)
    if len(job["logs"]) > 100:
        job["logs"] = job["logs"][-100:]
    _persist(repo_id, job)


def _step_start(repo_id: str, job: dict, idx: int) -> None:
    job["current_step"] = PIPELINE_STEPS[idx]
    job["steps"][idx]["status"] = "running"
    _persist(repo_id, job)


def _step_done(repo_id: str, job: dict, idx: int, detail: str = "") -> None:
    job["steps"][idx]["status"] = "done"
    job["steps"][idx]["detail"] = detail
    _recalc_progress(job)
    _persist(repo_id, job)


def _step_skip(repo_id: str, job: dict, idx: int, detail: str = "") -> None:
    """Mark a non-critical step as skipped (shown as ✅ with grey detail)."""
    job["steps"][idx]["status"] = "skipped"
    job["steps"][idx]["detail"] = detail or "skipped"
    _recalc_progress(job)
    _persist(repo_id, job)


def _fail(repo_id: str, job: dict, idx: int, detail: str) -> None:
    """Mark step as error, set job to error, and raise to abort the pipeline."""
    job["steps"][idx]["status"] = "error"
    job["steps"][idx]["detail"] = detail
    job["status"] = "error"
    job["error"] = f"Step '{PIPELINE_STEPS[idx]}' failed: {detail}"
    _persist(repo_id, job)
    raise _PipelineAbort(detail)


def _recalc_progress(job: dict) -> None:
    done = sum(1 for s in job["steps"] if s["status"] in ("done", "skipped"))
    job["progress"] = int(done / len(PIPELINE_STEPS) * 100)




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
        _fail(repo_id, job, 0, "Repository URL is empty")

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
        _log(repo_id, job, f"Repo already cloned at {target}")
        _step_done(repo_id, job, 0, f"Already cloned — {target}")
        return target

    # Corrupt / partial dir → wipe before retrying
    if target.exists():
        _log(repo_id, job, f"Wiping incomplete clone dir: {target}")
        shutil.rmtree(str(target), ignore_errors=True)

    git_errors: list[str] = []
    for url in candidates:
        _log(repo_id, job, f"git clone --depth 1 {url}")
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", url, str(target)],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode == 0:
                _log(repo_id, job, f"Clone succeeded → {target}")
                _step_done(repo_id, job, 0, f"Cloned {url.split('/')[-1].replace('.git', '')}")
                return target
            stderr = (result.stderr or result.stdout or "non-zero exit").strip()
            short_err = stderr.splitlines()[-1][:200] if stderr else "clone failed"
            git_errors.append(f"{url}: {short_err}")
            _log(repo_id, job, f"Clone failed for {url}: {short_err}")
            if target.exists():
                shutil.rmtree(str(target), ignore_errors=True)
        except FileNotFoundError:
            _fail(repo_id, job, 0, "git binary not found. Ensure git is installed in the container.")
        except subprocess.TimeoutExpired:
            git_errors.append(f"{url}: timed out after 180 s")
            _log(repo_id, job, f"Clone timed out: {url}")
            if target.exists():
                shutil.rmtree(str(target), ignore_errors=True)
        except Exception as exc:
            short = str(exc)[:200]
            git_errors.append(f"{url}: {short}")
            _log(repo_id, job, f"Clone error {url}: {short}")
            if target.exists():
                shutil.rmtree(str(target), ignore_errors=True)

    summary = " | ".join(git_errors[:2]) if git_errors else "clone failed"
    _fail(repo_id, job, 0, summary[:500])


# ────────────────────────────────────────────────────────────────────────────
# Pipeline runner (executes in daemon thread)
# ────────────────────────────────────────────────────────────────────────────

def run_ingestion(repo_id: str, repo_url: str, suite_id: str, confluence_link: str) -> None:
    job = job_store.load_job(repo_id) or _make_job()
    _persist(repo_id, job)
    driver = None
    graph_stats: dict = {}
    contract_count = 0
    analysis_results: list = []
    method_summaries: dict = {}
    is_ts = False

    try:
        _log(repo_id, job, f"Pipeline started: repo_id={repo_id} url={repo_url or '(none)'} suite={suite_id}")
        driver = get_driver()
        # ── Step 0: Clone ──────────────────────────────────────────────────
        _step_start(repo_id, job, 0)
        repo_path: Optional[Path] = None

        if repo_url.strip():
            repo_path = _clone(repo_url, repo_id, job)   # raises _PipelineAbort on failure
        else:
            # No URL provided — metadata-only mode, skip ingestion steps
            _step_skip(repo_id, job, 0, "No repository URL — metadata-only mode")

        # ── Detect language ────────────────────────────────────────────────
        if repo_path and repo_path.exists():
            is_ts = bool(next(
                (p for p in repo_path.rglob("*.ts")
                 if "node_modules" not in str(p).lower()), None
            ))

        # ── Step 1: Parse ──────────────────────────────────────────────────
        _step_start(repo_id, job, 1)

        if repo_path and repo_path.exists():
            if is_ts:
                from pipeline.ingestion.ts_analysis_client import (
                    analyse_files_detailed, is_service_healthy,
                )
                ts_files = [
                    str(p) for p in repo_path.rglob("*.ts")
                    if "node_modules" not in str(p).lower()
                ]
                _log(repo_id, job, f"TypeScript parse candidate files: {len(ts_files)}")
                if not ts_files:
                    _fail(repo_id, job, 1, "No .ts files found in the cloned repository")
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
                        _log(repo_id, job, f"TS parse error: {err.get('file','<unknown>')} :: {err.get('error','unknown')}")
                    if len(parse_errors) > 8:
                        _log(repo_id, job, f"TS parse errors truncated: {len(parse_errors) - 8} more")
                if not analysis_results:
                    detail = (
                        f"TypeScript analysis returned no results. "
                        f"attempted={len(ts_files)}, parse_errors={len(parse_errors)}"
                    )
                    if parse_errors:
                        detail += f". first_error={parse_errors[0].get('error', '')[:180]}"
                    _fail(repo_id, job, 1, detail)
                _log(repo_id, job, f"TypeScript parse output units: {len(analysis_results)}")
                _step_done(repo_id, job, 1, f"{len(ts_files)} TypeScript files parsed")

            else:
                from pipeline.ingestion.git_reader import get_java_files
                from pipeline.ingestion.java_analysis_client import (
                    analyze_files_detailed, is_service_healthy,
                )
                java_files = get_java_files(str(repo_path))
                _log(repo_id, job, f"Java parse candidate files: {len(java_files)}")
                if not java_files:
                    _fail(repo_id, job, 1, "No .java files found in the cloned repository")
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
                    _log(repo_id, job, f"Java parse: {len(parse_errors)} files failed (HTTP errors / exceptions)")
                    for err in parse_errors[:10]:
                        _log(repo_id, job, f"  ✗ {Path(err.get('file','<unknown>')).name} — {err.get('error','?')[:220]}")
                    if len(parse_errors) > 10:
                        _log(repo_id, job, f"  … {len(parse_errors) - 10} more failures (see server logs)")

                parsed_count = len(analysis_results)
                total_attempted = len(java_files)
                _log(repo_id, job, f"Java parse results: {parsed_count}/{total_attempted} files yielded classes")

                if not analysis_results:
                    detail = (
                        f"Java analysis yielded no class data. "
                        f"attempted={total_attempted}, http_errors={len(parse_errors)}"
                    )
                    if parse_errors:
                        detail += f". first_error={parse_errors[0].get('error', '')[:200]}"
                    _fail(repo_id, job, 1, detail)
                _step_done(repo_id, job, 1, f"{parsed_count}/{total_attempted} Java files produced classes")

        else:
            # No repo (metadata-only) — skip remaining ingestion steps
            _step_skip(repo_id, job, 1, "No repository to parse")

        # ── Step 2: Write knowledge graph ──────────────────────────────────
        _step_start(repo_id, job, 2)

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
                _step_done(repo_id, job, 2, f"{total} code units written to graph")
            except Exception as exc:
                _fail(repo_id, job, 2, str(exc))
        else:
            _step_skip(repo_id, job, 2, "No analysis results to write")

        # ── Step 3: Wiki summaries ─────────────────────────────────────────
        _step_start(repo_id, job, 3)
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
                _step_done(repo_id, job, 3, f"{len(wiki_by_class)} class summaries generated")
            except Exception as exc:
                _fail(repo_id, job, 3, str(exc))
        else:
            _step_skip(repo_id, job, 3, "No classes to summarise")

        # ── Step 4: API contracts ──────────────────────────────────────────
        _step_start(repo_id, job, 4)

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
                _step_done(repo_id, job, 4, f"{contract_count} contracts extracted")
            except Exception as exc:
                _fail(repo_id, job, 4, str(exc))
        else:
            _step_skip(repo_id, job, 4, "No code to extract contracts from")

        # ── Step 5: Embed to Qdrant (non-critical) ─────────────────────────
        _step_start(repo_id, job, 5)
        try:
            from core.embeddings.embedder import embed_batch, build_method_text
            from core.embeddings.vector_store import get_client, COLLECTION, ensure_required_collections
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
                _log(repo_id, job, f"Embedding {len(texts)} methods for Qdrant...")
                vectors = embed_batch(texts)
                points = [
                    PointStruct(id=str(_uuid.uuid4()), vector=v, payload=p)
                    for v, p in zip(vectors, payloads)
                ]
                _log(repo_id, job, f"Upserting {len(points)} vectors into '{COLLECTION}'")
                client.upsert(collection_name=COLLECTION, points=points)
                _step_done(repo_id, job, 5, f"{len(points)} vectors stored")
            else:
                _step_skip(repo_id, job, 5, "No methods to embed")
        except Exception as exc:
            _log(repo_id, job, f"Qdrant embed step failed: {exc}")
            _step_skip(repo_id, job, 5, f"Qdrant unavailable — {exc}")

        # ── Step 6: Match API contracts FE ↔ BE (non-critical) ────────────
        _step_start(repo_id, job, 6)
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
                    _step_done(repo_id, job, 6, "FE → BE contracts matched")
                else:
                    _step_skip(repo_id, job, 6, "No backend repo with contracts in this suite")
            except Exception as exc:
                _step_skip(repo_id, job, 6, f"Matching skipped — {exc}")
        else:
            _step_skip(repo_id, job, 6, "Java repo — FE↔BE matching not needed")

        # ── Step 7: Confluence / finalise ──────────────────────────────────
        _step_start(repo_id, job, 7)
        if confluence_link.strip():
            try:
                from pipeline.ingestion.confluence_ingester import ingest_page
                ingest_page(
                    url_or_id=confluence_link,
                    category="current",
                    module_tags=[],
                    suite_id=suite_id,
                )
                _step_done(repo_id, job, 7, "Confluence page ingested")
            except Exception as exc:
                _step_skip(repo_id, job, 7, f"Confluence skipped — {exc}")
        else:
            _step_done(repo_id, job, 7, "Project registered in DeepWiki")

        # ── Finalise ───────────────────────────────────────────────────────
        code_units = (
            graph_stats.get("classes", 0)
            + graph_stats.get("methods", 0)
            + graph_stats.get("fields", 0)
        )
        job["stats"] = {"code_units": code_units, "contracts": contract_count}
        job["status"] = "done"
        job["progress"] = 100
        _persist(repo_id, job)

    except _PipelineAbort:
        # Error state already set by _fail() — mark remaining steps as cancelled
        _log(repo_id, job, f"Pipeline aborted: {job.get('error', '')}")
        for step in job["steps"]:
            if step["status"] == "pending":
                step["status"] = "cancelled"
            elif step["status"] == "running":
                step["status"] = "error"
                step["detail"] = step["detail"] or "Aborted"

    except Exception as exc:
        tb = traceback.format_exc()
        _log(repo_id, job, f"Unexpected pipeline error: {exc}\n{tb}")
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

        _persist(repo_id, job)
    finally:
        _persist(repo_id, job)
        if driver:
            try:
                driver.close()
            except Exception:
                pass


