import os
import time
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from pipeline.embeddings.embedder import embed_text
from pipeline.embeddings.vector_store import get_client, semantic_search
from pipeline.graph.schema import get_driver

load_dotenv()

# ── THREE SEPARATE CLIENTS → THREE SEPARATE DASHBOARD ROWS ──
raw_client   = Anthropic(api_key=os.getenv("ANTHROPIC_RAW_KEY"))
wiki_client  = Anthropic(api_key=os.getenv("ANTHROPIC_WIKI_KEY"))
cache_client = Anthropic(api_key=os.getenv("ANTHROPIC_CACHE_KEY"))

# Available models
MODELS = {
    "claude-haiku-4-5":   {"label": "Claude Haiku 4.5",  "input": 0.80,  "output": 4.00},
    "claude-sonnet-4-6":  {"label": "Claude Sonnet 4.6", "input": 3.00,  "output": 15.00},
}

DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_BASE = (
    "You are a senior Java Spring Boot developer. "
    "Answer concisely in 3-5 sentences. "
    "Reference specific class names and methods where relevant."
)


# ── HELPERS ────────────────────────────────────────────────

def compute_cost(
    input_tokens: int,
    output_tokens: int,
    cache_created: int = 0,
    cache_read: int = 0,
    model: str = DEFAULT_MODEL
) -> dict:
    """Calculate cost using Anthropic pricing."""
    pricing = MODELS.get(model, MODELS[DEFAULT_MODEL])

    # Cache creation costs same as input
    # Cache read costs 10% of input price
    input_cost   = ((input_tokens + cache_created) / 1_000_000) * pricing["input"]
    cache_cost   = (cache_read / 1_000_000) * (pricing["input"] * 0.10)
    output_cost  = (output_tokens / 1_000_000) * pricing["output"]

    return {
        "input_cost":  round(input_cost, 6),
        "cache_cost":  round(cache_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost":  round(input_cost + cache_cost + output_cost, 6)
    }


def build_wiki_context(query: str, top_k: int = 4) -> tuple[str, list]:
    """Fetch pre-built wiki summaries from Qdrant + Neo4j."""
    query_vector   = embed_text(query)
    qdrant         = get_client()
    search_results = semantic_search(qdrant, query_vector, top_k=top_k)

    driver = get_driver()
    parts  = []

    with driver.session() as session:
        for r in search_results:
            row = session.run("""
                MATCH (c:Class {name: $name})
                OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
                OPTIONAL MATCH (c)-[:HAS_FIELD]->(f:Field)
                RETURN
                    c.name           AS name,
                    c.component_type AS type,
                    c.package        AS package,
                    c.wiki_summary   AS summary,
                    collect(DISTINCT m.name) AS methods,
                    collect(DISTINCT f.name) AS fields
            """, name=r["name"]).single()

            if row:
                methods = ", ".join(
                    m for m in (row["methods"] or []) if m
                )[:200]
                fields = ", ".join(
                    f for f in (row["fields"] or []) if f
                )[:150]
                parts.append(
                    f"[{row['type']}] {row['name']}\n"
                    f"Package : {row['package']}\n"
                    f"Summary : {row['summary']}\n"
                    f"Methods : {methods}\n"
                    f"Fields  : {fields}"
                )

    driver.close()
    return "\n\n---\n\n".join(parts), search_results


def load_raw_source(source_files: list[str], max_files: int = 4) -> str:
    """Load actual Java source files — no summarization."""
    parts = []
    for path in source_files[:max_files]:
        if path and os.path.exists(path):
            content  = Path(path).read_text(encoding="utf-8", errors="replace")
            filename = Path(path).name
            parts.append(f"// ═══ {filename} ═══\n{content}")
    return "\n\n".join(parts)


# ── APPROACH 1: RAW SOURCE (ANTHROPIC_RAW_KEY) ─────────────

def run_claude_raw(
    query: str,
    source_files: list[str],
    model: str = DEFAULT_MODEL
) -> dict:
    """
    Sends raw Java source files as context.
    Uses ANTHROPIC_RAW_KEY → tracked separately on dashboard.
    Simulates developer copy-pasting source into Claude chat.
    """
    start    = time.time()
    raw_code = load_raw_source(source_files)

    if not raw_code:
        raw_code = "// No source files found — using empty context"

    response = raw_client.messages.create(
        model=model,
        max_tokens=400,
        system=f"{SYSTEM_BASE}\n\nSOURCE CODE:\n{raw_code}",
        messages=[{"role": "user", "content": query}]
    )

    elapsed = time.time() - start
    usage   = response.usage
    cost    = compute_cost(
        usage.input_tokens,
        usage.output_tokens,
        model=model
    )

    return {
        "approach":      "Claude — Raw Source",
        "key_label":     "ANTHROPIC_RAW_KEY",
        "model":         model,
        "answer":        response.content[0].text,
        "input_tokens":  usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_created": 0,
        "cache_read":    0,
        "total_tokens":  usage.input_tokens + usage.output_tokens,
        "cost":          cost,
        "latency_sec":   round(elapsed, 2),
        "context_chars": len(raw_code),
        "timestamp":     datetime.now().isoformat()
    }


# ── APPROACH 2: WIKI, NO CACHE (ANTHROPIC_WIKI_KEY) ────────

def run_claude_wiki(
    query: str,
    top_k: int = 4,
    model: str = DEFAULT_MODEL
) -> tuple[dict, list, list]:
    """
    Sends pre-built wiki summaries as context.
    Uses ANTHROPIC_WIKI_KEY → tracked separately on dashboard.
    No caching — full context paid every call.
    Returns result + search_results + source_files.
    """
    start            = time.time()
    context, results = build_wiki_context(query, top_k)
    source_files     = []

    driver = get_driver()
    with driver.session() as session:
        for r in results:
            row = session.run(
                "MATCH (c:Class {name: $name}) RETURN c.file AS file",
                name=r["name"]
            ).single()
            if row and row["file"]:
                source_files.append(row["file"])
    driver.close()

    response = wiki_client.messages.create(
        model=model,
        max_tokens=400,
        system=(
            f"{SYSTEM_BASE}\n\n"
            f"WIKI CONTEXT (answer using this only):\n{context}"
        ),
        messages=[{"role": "user", "content": query}]
    )

    elapsed = time.time() - start
    usage   = response.usage
    cost    = compute_cost(
        usage.input_tokens,
        usage.output_tokens,
        model=model
    )

    result = {
        "approach":      "Claude — Wiki, No Cache",
        "key_label":     "ANTHROPIC_WIKI_KEY",
        "model":         model,
        "answer":        response.content[0].text,
        "input_tokens":  usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_created": 0,
        "cache_read":    0,
        "total_tokens":  usage.input_tokens + usage.output_tokens,
        "cost":          cost,
        "latency_sec":   round(elapsed, 2),
        "context_chars": len(context),
        "classes_used":  [r["name"] for r in results],
        "timestamp":     datetime.now().isoformat()
    }

    return result, results, source_files


# ── APPROACH 3: WIKI + CACHE (ANTHROPIC_CACHE_KEY) ─────────

def run_claude_cache(
    query: str,
    top_k: int = 4,
    model: str = DEFAULT_MODEL
) -> dict:
    """
    Sends wiki context with prompt caching enabled.
    Uses ANTHROPIC_CACHE_KEY → tracked separately on dashboard.

    Call 1: cache_creation_input_tokens filled, cache_read = 0
    Call 2+: cache_read filled, cost = 10% of original
    Cache TTL = 5 minutes, refreshes on each use.
    """
    start            = time.time()
    context, results = build_wiki_context(query, top_k)

    response = cache_client.messages.create(
        model=model,
        max_tokens=400,
        system=[
            {
                "type": "text",
                "text": (
                    f"{SYSTEM_BASE}\n\n"
                    f"WIKI CONTEXT (answer using this only):\n{context}"
                ),
                # ← Marks this block as cacheable
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[{"role": "user", "content": query}]
    )

    elapsed       = time.time() - start
    usage         = response.usage
    cache_created = getattr(usage, "cache_creation_input_tokens", 0)
    cache_read    = getattr(usage, "cache_read_input_tokens", 0)
    cost          = compute_cost(
        usage.input_tokens,
        usage.output_tokens,
        cache_created=cache_created,
        cache_read=cache_read,
        model=model
    )

    return {
        "approach":      "Claude — Wiki + Cache",
        "key_label":     "ANTHROPIC_CACHE_KEY",
        "model":         model,
        "answer":        response.content[0].text,
        "input_tokens":  usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_created": cache_created,
        "cache_read":    cache_read,
        "total_tokens":  usage.input_tokens + usage.output_tokens,
        "cost":          cost,
        "latency_sec":   round(elapsed, 2),
        "context_chars": len(context),
        "classes_used":  [r["name"] for r in results],
        "is_cache_hit":  cache_read > 0,
        "timestamp":     datetime.now().isoformat()
    }


# ── FULL COMPARISON ────────────────────────────────────────

def run_full_comparison(
    query: str,
    top_k: int = 4,
    model: str = DEFAULT_MODEL
) -> dict:
    """Run all 3 Claude approaches + log results."""

    print(f"\n  [1/3] Claude Raw (ANTHROPIC_RAW_KEY)...")
    wiki_result, search_results, source_files = run_claude_wiki(
        query, top_k, model
    )
    raw_result = run_claude_raw(query, source_files, model)
    print(f"        {raw_result['total_tokens']:,} tokens "
          f"| ${raw_result['cost']['total_cost']:.6f}")
    time.sleep(2)

    print(f"  [2/3] Claude Wiki (ANTHROPIC_WIKI_KEY)...")
    print(f"        {wiki_result['total_tokens']:,} tokens "
          f"| ${wiki_result['cost']['total_cost']:.6f}")
    time.sleep(2)

    print(f"  [3/3] Claude Cache (ANTHROPIC_CACHE_KEY)...")
    cache_result = run_claude_cache(query, top_k, model)
    cache_label  = "CACHE HIT ✅" if cache_result["is_cache_hit"] else "CACHE MISS (first call)"
    print(f"        {cache_result['total_tokens']:,} tokens "
          f"| ${cache_result['cost']['total_cost']:.6f} | {cache_label}")

    return {
        "query":   query,
        "model":   model,
        "raw":     raw_result,
        "wiki":    wiki_result,
        "cache":   cache_result,
        "summary": {
            "raw_tokens":   raw_result["total_tokens"],
            "wiki_tokens":  wiki_result["total_tokens"],
            "cache_tokens": cache_result["total_tokens"],
            "raw_cost":     raw_result["cost"]["total_cost"],
            "wiki_cost":    wiki_result["cost"]["total_cost"],
            "cache_cost":   cache_result["cost"]["total_cost"],
            "wiki_vs_raw_saving_pct": round(
                (1 - wiki_result["total_tokens"] /
                 max(raw_result["total_tokens"], 1)) * 100, 1
            ),
            "cache_vs_raw_saving_pct": round(
                (1 - cache_result["cost"]["total_cost"] /
                 max(raw_result["cost"]["total_cost"], 0.000001)) * 100, 1
            )
        }
    }