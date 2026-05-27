"""
DeepWiki MCP Server — Iteration 22.

Exposes 5 tools to GitHub Copilot (and any MCP-compatible client):
  deepwiki_search          — semantic search across the knowledge graph
  deepwiki_get_class       — class wiki + method signatures
  deepwiki_get_flow        — cross-repo call-chain trace
  deepwiki_get_api_consumers — who calls a given API endpoint
  deepwiki_get_decisions   — design decision context for a module

Deploy: Railway (separate service from the main FastAPI backend).
Transport: streamable-http (MCP 1.x standard).
"""

import os
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from client import api_get, api_post

load_dotenv()

mcp = FastMCP(
    "DeepWiki",
    host="0.0.0.0",
    port=int(os.getenv("PORT", 8090)),
)


# ── Tool 1: semantic search ────────────────────────────────────────────────────

@mcp.tool()
def deepwiki_search(
    query: str,
    repo_id: str = "",
    suite_id: str = "",
    top_k: int = 5,
) -> str:
    """
    Search the DeepWiki knowledge graph using semantic similarity.
    Returns ranked code snippets with class names, method signatures, and wiki summaries.
    Use this to locate relevant classes or methods before reading full detail.

    Args:
        query:    Natural-language search query (e.g. "how is pet ownership validated").
        repo_id:  Optional — limit search to a specific repository ID.
        suite_id: Optional — limit search to a specific application suite.
        top_k:    Number of results to return (default 5, max 20).
    """
    payload: dict = {"query": query, "top_k": min(top_k, 20)}
    if repo_id:
        payload["repo_id"] = repo_id
    if suite_id:
        payload["suite_id"] = suite_id

    data = api_post("/search", payload)
    results = data.get("results", [])
    if not results:
        return "No results found."

    lines = [f"DeepWiki search: '{query}' -> {len(results)} result(s)\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('class_name', '?')} ({r.get('repo_id', '?')})")
        if r.get("method_name"):
            lines.append(f"     method: {r['method_name']}")
        if r.get("wiki_summary"):
            lines.append(f"     {r['wiki_summary'][:200]}")
        lines.append(f"     score: {r.get('score', 0):.3f}")
    return "\n".join(lines)


# ── Tool 2: class detail ───────────────────────────────────────────────────────

@mcp.tool()
def deepwiki_get_class(class_name: str) -> str:
    """
    Retrieve the full wiki summary and method signatures for a class.
    Use deepwiki_search first to find the correct class_name if unsure.

    Args:
        class_name: Exact class name as stored in the knowledge graph (e.g. "PetService").
    """
    data = api_get(f"/classes/{class_name}")
    if not data:
        return f"Class '{class_name}' not found."

    lines = [
        f"Class: {data.get('name', class_name)}",
        f"Repo: {data.get('repo_id', '?')}",
        f"Package: {data.get('package', '?')}",
        "",
    ]

    wiki = data.get("wiki_summary") or data.get("summary")
    if wiki:
        lines += ["## Wiki Summary", wiki, ""]

    methods = data.get("methods", [])
    if methods:
        lines.append("## Methods")
        for m in methods:
            sig = m.get("signature") or m.get("name", "?")
            lines.append(f"  - {sig}")
            if m.get("wiki_summary"):
                lines.append(f"    {m['wiki_summary'][:120]}")

    return "\n".join(lines)


# ── Tool 3: flow trace ─────────────────────────────────────────────────────────

@mcp.tool()
def deepwiki_get_flow(
    entry_point: str,
    be_repo_id: str = "spring-petclinic",
    fe_repo_id: str = "angular-petclinic",
    max_hops: int = 8,
) -> str:
    """
    Trace a cross-repository call chain from a frontend component or backend method.
    Shows [Angular FE] -> [API Contract] -> [Spring Boot BE] step-by-step.
    Token savings vs raw LLM context are included.

    Args:
        entry_point: Class or method name to start the trace from (e.g. "PetService.getPets").
        be_repo_id:  Backend repository ID (default "spring-petclinic").
        fe_repo_id:  Frontend repository ID (default "angular-petclinic").
        max_hops:    Maximum BFS depth (default 8).
    """
    payload = {
        "entry_point": entry_point,
        "be_repo_id": be_repo_id,
        "fe_repo_id": fe_repo_id,
        "max_hops": max_hops,
    }
    data = api_post("/flow", payload)
    steps = data.get("steps", [])
    if not steps:
        return f"No flow trace found for '{entry_point}'."

    lines = [
        f"Flow trace: '{entry_point}'",
        f"Mode: {data.get('trace_mode', 'unknown')}",
        f"Steps: {len(steps)}",
        "",
    ]

    current_repo = None
    for step in steps:
        repo = step.get("repo_id", "?")
        if repo != current_repo:
            repo_type = step.get("repo_type", repo)
            lines.append(f"--- [{repo_type.upper()}] ---")
            current_repo = repo
        hop = step.get("hop", "?")
        cls = step.get("class_name", "?")
        method = step.get("method_name", "?")
        lines.append(f"  {hop}. {cls}.{method}")
        if step.get("component_type"):
            lines[-1] += f"  [{step['component_type']}]"

    raw = data.get("raw_token_estimate", 0)
    dw = data.get("token_count", 0)
    if raw and dw:
        saved = raw - dw
        pct = int(saved / raw * 100) if raw else 0
        lines += ["", f"Token savings: {dw} DeepWiki vs {raw} raw ({pct}% saved)"]

    lines += ["", data.get("explanation", "")]
    return "\n".join(lines)


# ── Tool 4: API consumers ──────────────────────────────────────────────────────

@mcp.tool()
def deepwiki_get_api_consumers(
    method: str,
    path: str,
    be_repo_id: str = "spring-petclinic",
) -> str:
    """
    Find all frontend callers of a specific backend API endpoint.
    Returns the class and method names of Angular services that consume the endpoint.

    Args:
        method:     HTTP method (GET, POST, PUT, DELETE).
        path:       API path (e.g. "/api/pets/{petId}").
        be_repo_id: Backend repository ID (default "spring-petclinic").
    """
    contract_id = f"{be_repo_id}:{method.upper()}:{path}"
    try:
        data = api_get(f"/contracts/{contract_id}/consumers")
    except Exception:
        # Try URL-encoded version
        import urllib.parse
        encoded = urllib.parse.quote(contract_id, safe="")
        data = api_get(f"/contracts/{encoded}/consumers")

    consumers = data.get("consumers", [])
    if not consumers:
        return f"No consumers found for {method.upper()} {path}."

    lines = [f"Consumers of {method.upper()} {path} ({be_repo_id}):"]
    for c in consumers:
        caller = c.get("caller_class", "?")
        caller_method = c.get("caller_method") or c.get("method", "")
        confidence = c.get("confidence", 0)
        repo = c.get("fe_repo_id", "")
        line = f"  - {caller}"
        if caller_method:
            line += f".{caller_method}()"
        if repo:
            line += f"  [{repo}]"
        if confidence:
            line += f"  confidence={confidence:.2f}"
        lines.append(line)
    return "\n".join(lines)


# ── Tool 5: design decisions ───────────────────────────────────────────────────

@mcp.tool()
def deepwiki_get_decisions(
    module_name: str,
    repo_id: str = "",
) -> str:
    """
    Retrieve design decision context for a module or feature area.
    Searches for architectural notes, patterns, and rationale within the knowledge graph.
    Use this before modifying a module to understand its design intent.

    Args:
        module_name: Module or feature name (e.g. "authentication", "pet ownership", "visit scheduling").
        repo_id:     Optional — limit to a specific repository.
    """
    query = f"design decision architecture pattern rationale {module_name}"
    payload: dict = {"query": query, "top_k": 6}
    if repo_id:
        payload["repo_id"] = repo_id

    data = api_post("/search", payload)
    results = data.get("results", [])
    if not results:
        return f"No design context found for '{module_name}'."

    lines = [f"Design context for '{module_name}':\n"]
    for i, r in enumerate(results, 1):
        cls = r.get("class_name", "?")
        repo = r.get("repo_id", "?")
        summary = r.get("wiki_summary", "")
        lines.append(f"[{i}] {cls} ({repo})")
        if summary:
            lines.append(f"     {summary[:300]}")
    return "\n".join(lines)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
