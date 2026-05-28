"""
Project bootstrap pipeline.

Triggered after a repository is created from the Admin page. It performs a
best-effort background ingestion of the provided GitHub repo and optional
Confluence page so the project becomes searchable without manual iteration
runs.
"""

from __future__ import annotations

import threading
from pathlib import Path

from pipeline.graph.api_impact import run_api_impact_nightly
from pipeline.graph.api_matcher import run_api_matching
from pipeline.graph.api_writer import write_all_api_contracts
from pipeline.graph.method_writer import write_all_method_data
from pipeline.graph.schema import get_driver
from pipeline.ingestion.git_reader import clone_repo, get_java_files
from pipeline.ingestion.java_analysis_client import analyze_files as analyze_java_files
from pipeline.ingestion.java_analysis_client import is_service_healthy as is_java_analysis_healthy
from pipeline.ingestion.ts_analysis_client import analyse_files as analyze_ts_files
from pipeline.ingestion.ts_analysis_client import is_service_healthy as is_ts_analysis_healthy
from pipeline.wiki.summarizer import summarize_methods
from pipeline.delta.updater import update_wiki_summary


def _repo_dir(repo_id: str) -> Path:
    return Path("repos") / repo_id


def _clone_if_needed(repo_url: str, repo_id: str) -> Path | None:
    if not repo_url.strip():
        return None
    target_dir = _repo_dir(repo_id)
    clone_repo(repo_url, str(target_dir))
    return target_dir


def _run_java_pipeline(driver, repo_id: str, repo_path: Path) -> dict:
    java_files = get_java_files(str(repo_path))
    if not java_files or not is_java_analysis_healthy():
        return {"classes": 0, "methods": 0, "fields": 0, "contracts": 0}

    analysis_results = analyze_java_files(java_files)
    if not analysis_results:
        return {"classes": 0, "methods": 0, "fields": 0, "contracts": 0}

    from pipeline.graph.writer import write_analysis

    graph_stats = write_analysis(driver, analysis_results)

    class_lookup = {
        cls["name"]: cls
        for file_result in analysis_results
        for cls in file_result.get("classes", [])
    }

    wiki_by_class: dict[str, str] = {}
    for cls_name, cls in class_lookup.items():
        wiki = update_wiki_summary(cls)
        wiki_by_class[cls_name] = wiki

    method_summaries: dict[str, dict[str, str]] = {}
    for cls_name, cls in class_lookup.items():
        method_summaries[cls_name] = summarize_methods(cls, wiki_by_class.get(cls_name, ""), delay=0.0)

    with driver.session() as session:
        from pipeline.graph.method_writer import write_all_method_data

        method_stats = write_all_method_data(driver, analysis_results, method_summaries)
    contract_count = write_all_api_contracts(driver, analysis_results, repo_id)
    impact_count = run_api_impact_nightly(driver)

    return {
        **graph_stats,
        **method_stats,
        "contracts": contract_count,
        "impact_nodes": impact_count,
    }


def _run_ts_pipeline(driver, repo_id: str, suite_id: str, repo_path: Path) -> dict:
    ts_files = [str(path) for path in repo_path.rglob("*.ts") if "node_modules" not in str(path).lower()]
    if not ts_files or not is_ts_analysis_healthy():
        return {"ts_classes": 0, "consumes_written": 0}

    analysis_results = analyze_ts_files(ts_files)
    if not analysis_results:
        return {"ts_classes": 0, "consumes_written": 0}

    from pipeline.graph.writer import write_analysis

    graph_stats = write_analysis(driver, analysis_results)

    class_lookup = {
        cls["name"]: cls
        for file_result in analysis_results
        for cls in file_result.get("classes", [])
    }

    wiki_by_class: dict[str, str] = {}
    for cls_name, cls in class_lookup.items():
        wiki = update_wiki_summary(cls)
        wiki_by_class[cls_name] = wiki

    method_summaries: dict[str, dict[str, str]] = {}
    for cls_name, cls in class_lookup.items():
        method_summaries[cls_name] = summarize_methods(cls, wiki_by_class.get(cls_name, ""), delay=0.0)

    from pipeline.graph.method_writer import write_all_method_data

    method_stats = write_all_method_data(driver, analysis_results, method_summaries)

    # If a backend repo already exists in the same suite, use its contracts for FE matching.
    with driver.session() as session:
        backend_row = session.run(
            """
            MATCH (s:ApplicationSuite)-[:HAS_REPO]->(r:Repository)
            WHERE s.id = $suite_id AND r.id <> $repo_id
            OPTIONAL MATCH (r)-[:EXPOSES]->(a:APIContract)
            WITH r, count(a) AS contract_count
            WHERE contract_count > 0
            RETURN r.id AS repo_id
            ORDER BY contract_count DESC, r.id ASC
            LIMIT 1
            """,
            suite_id=suite_id,
            repo_id=repo_id,
        ).single()

    consumes_stats = {"written": 0, "fuzzy": 0, "unknown": 0, "classes_processed": 0}
    if backend_row:
        consumes_stats = run_api_matching(driver, repo_id, backend_row["repo_id"], analysis_results)

    return {**graph_stats, **method_stats, **consumes_stats}


def bootstrap_project(
    *,
    repo_id: str,
    repo_url: str,
    suite_id: str,
    confluence_link: str = "",
) -> dict:
    """
    Best-effort ingestion for a newly added project.

    Returns a compact status dictionary for logging/debugging.
    """
    repo_path = _clone_if_needed(repo_url, repo_id)
    driver = get_driver()
    try:
        results: dict = {"repo_id": repo_id, "suite_id": suite_id}

        if repo_path and repo_path.exists():
            results["repo_path"] = str(repo_path)
            results.update(_run_java_pipeline(driver, repo_id, repo_path))
            results.update(_run_ts_pipeline(driver, repo_id, suite_id, repo_path))

        if confluence_link.strip():
            from pipeline.ingestion.confluence_ingester import ingest_page

            results["confluence"] = ingest_page(
                url_or_id=confluence_link,
                category="current",
                module_tags=[],
                suite_id=suite_id,
            )

        return results
    finally:
        driver.close()


def start_project_bootstrap(
    *,
    repo_id: str,
    repo_url: str,
    suite_id: str,
    confluence_link: str = "",
) -> threading.Thread:
    """Start project bootstrap in a daemon thread."""
    thread = threading.Thread(
        target=bootstrap_project,
        kwargs={
            "repo_id": repo_id,
            "repo_url": repo_url,
            "suite_id": suite_id,
            "confluence_link": confluence_link,
        },
        daemon=True,
        name=f"project-bootstrap-{repo_id}",
    )
    thread.start()
    return thread