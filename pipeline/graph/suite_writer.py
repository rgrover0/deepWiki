"""
Suite + Repository graph writer — Iteration 17.

Manages:
  ApplicationSuite  {id, name, description}
  Repository        {id, name, language, framework}
  (Suite)-[:HAS_REPO]->(Repository)
"""

import json
from pathlib import Path


def ensure_suite(session, suite_id: str, suite_name: str, description: str = ""):
    session.run("""
        MERGE (s:ApplicationSuite {id: $id})
        ON CREATE SET s.name = $name, s.description = $description
        ON MATCH  SET s.name = $name
    """, id=suite_id, name=suite_name, description=description)


def ensure_repo_node(session, repo_id: str, repo_name: str,
                     language: str, suite_id: str):
    session.run("""
        MERGE (r:Repository {id: $repo_id})
        ON CREATE SET r.name = $repo_name, r.language = $language
        ON MATCH  SET r.name = $repo_name
    """, repo_id=repo_id, repo_name=repo_name, language=language)

    session.run("""
        MATCH (s:ApplicationSuite {id: $suite_id})
        MATCH (r:Repository       {id: $repo_id})
        MERGE (s)-[:HAS_REPO]->(r)
    """, suite_id=suite_id, repo_id=repo_id)


def _resolve_config_path(config_path: str | None = None) -> Path:
    """Resolve suites config path across local and deployed runtimes."""
    if config_path:
        p = Path(config_path)
        if p.exists():
            return p

    # 1) Relative to current working dir (local dev)
    cwd_candidate = Path("config/suites.json")
    if cwd_candidate.exists():
        return cwd_candidate

    # 2) Relative to repository root from this file (deployed/runtime-safe)
    repo_candidate = Path(__file__).resolve().parents[2] / "config" / "suites.json"
    if repo_candidate.exists():
        return repo_candidate

    looked = [str(cwd_candidate), str(repo_candidate)]
    if config_path:
        looked.insert(0, str(Path(config_path)))
    raise FileNotFoundError(f"suites config not found. looked in: {looked}")


def write_suite_config(driver, config_path: str | None = None) -> dict:
    """
    Read suites.json and MERGE all Suite + Repository nodes into Neo4j.
    Returns counts: {suites, repos}.
    """
    cfg    = _resolve_config_path(config_path)
    data   = json.loads(cfg.read_text(encoding="utf-8"))
    suites = 0
    repos  = 0

    with driver.session() as session:
        for suite in data["suites"]:
            ensure_suite(session, suite["id"], suite["name"],
                         suite.get("description", ""))
            suites += 1
            for repo in suite["repos"]:
                ensure_repo_node(session, repo["id"], repo["name"],
                                 repo["language"], suite["id"])
                repos += 1

    driver.close()
    return {"suites": suites, "repos": repos}
