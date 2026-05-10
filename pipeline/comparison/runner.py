import os
import time
from pathlib import Path
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
from pipeline.embeddings.embedder import embed_text
from pipeline.embeddings.vector_store import get_client, semantic_search
from pipeline.graph.schema import get_driver

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

# Two separate Groq clients — tracked separately on dashboard
deepwiki_client = Groq(api_key=os.getenv("GROQ_DEEPWIKI_KEY"))
raw_client      = Groq(api_key=os.getenv("GROQ_RAW_KEY"))

DEEPWIKI_SYSTEM = """You are a code assistant with deep knowledge of a
Spring Boot application. Answer using ONLY the wiki context provided.
Be specific — reference actual class names and methods."""

RAW_SYSTEM = """You are a code assistant. Answer the developer's question
using the source code provided. Be specific and technical."""


# ── APPROACH 1: DEEPWIKI ───────────────────────────────────

def run_deepwiki_approach(query: str, top_k: int = 4) -> dict:
    """
    1. Embed query → vector
    2. Semantic search Qdrant → top-K relevant classes
    3. Fetch pre-built wiki summaries from Neo4j
    4. Build compact context from summaries (~800-2000 tokens)
    5. Call LLM via GROQ_DEEPWIKI_KEY
    """
    start = time.time()

    # Semantic search
    query_vector   = embed_text(query)
    qdrant         = get_client()
    search_results = semantic_search(qdrant, query_vector, top_k=top_k)

    # Fetch wiki summaries from Neo4j
    driver        = get_driver()
    context_parts = []
    source_files  = []

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
                    c.file           AS file,
                    collect(DISTINCT m.name) AS methods,
                    collect(DISTINCT f.name) AS fields
            """, name=r["name"]).single()

            if row:
                methods = ", ".join(
                    m for m in (row["methods"] or []) if m
                )
                fields = ", ".join(
                    f for f in (row["fields"] or []) if f
                )
                context_parts.append(
                    f"[{row['type']}] {row['name']}\n"
                    f"Summary : {row['summary']}\n"
                    f"Methods : {methods}\n"
                    f"Fields  : {fields}"
                )
                if row["file"]:
                    source_files.append(row["file"])

    driver.close()

    context = "\n\n---\n\n".join(context_parts)
    prompt  = (
        f"WIKI CONTEXT:\n{context}\n\n"
        f"QUESTION: {query}\n\n"
        f"Answer concisely in 3-5 sentences."
    )

    response = deepwiki_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": DEEPWIKI_SYSTEM},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=400,
        temperature=0.2
    )

    elapsed = time.time() - start

    return {
        "approach":       "DeepWiki (Wiki Context)",
        "key_used":       "GROQ_DEEPWIKI_KEY",
        "answer":         response.choices[0].message.content.strip(),
        "prompt_tokens":  response.usage.prompt_tokens,
        "output_tokens":  response.usage.completion_tokens,
        "total_tokens":   response.usage.total_tokens,
        "latency_sec":    round(elapsed, 2),
        "context_chars":  len(context),
        "classes_used":   [r["name"] for r in search_results],
        "source_files":   source_files,
        "model":          MODEL,
        "timestamp":      datetime.now().isoformat()
    }


# ── APPROACH 2: RAW SOURCE ─────────────────────────────────

def load_source_files(
    file_paths: list[str],
    max_files: int = 4
) -> tuple[str, list[str]]:
    """
    Load actual Java source files from disk.
    Full content — comments, imports, boilerplate included.
    Average file = 150-400 lines = 1,500-4,000 tokens.
    """
    parts        = []
    loaded_files = []

    for path in file_paths[:max_files]:
        if path and os.path.exists(path):
            content  = Path(path).read_text(
                encoding="utf-8", errors="replace"
            )
            filename   = Path(path).name
            line_count = len(content.splitlines())
            parts.append(
                f"// ═══ FILE: {filename} ({line_count} lines) ═══\n"
                f"{content}"
            )
            loaded_files.append(filename)

    return "\n\n".join(parts), loaded_files


def run_raw_approach(
    query: str,
    source_files: list[str]
) -> dict:
    """
    1. Load actual Java source files from disk
    2. Concatenate full content — no summarization
    3. Call LLM via GROQ_RAW_KEY
    Simulates developer copy-pasting source into an LLM.
    """
    start = time.time()

    files_to_load = source_files if source_files else [
        "repos/spring-petclinic/src/main/java/org/springframework"
        "/samples/petclinic/owner/Owner.java",
        "repos/spring-petclinic/src/main/java/org/springframework"
        "/samples/petclinic/owner/OwnerController.java",
        "repos/spring-petclinic/src/main/java/org/springframework"
        "/samples/petclinic/owner/Pet.java",
    ]

    raw_code, loaded_files = load_source_files(files_to_load, max_files=4)

    if not raw_code:
        raw_code = "// No source files found"

    prompt = (
        f"SOURCE CODE:\n{raw_code}\n\n"
        f"QUESTION: {query}\n\n"
        f"Answer concisely in 3-5 sentences."
    )

    response = raw_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": RAW_SYSTEM},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=400,
        temperature=0.2
    )

    elapsed = time.time() - start

    return {
        "approach":       "Raw Source Code",
        "key_used":       "GROQ_RAW_KEY",
        "answer":         response.choices[0].message.content.strip(),
        "prompt_tokens":  response.usage.prompt_tokens,
        "output_tokens":  response.usage.completion_tokens,
        "total_tokens":   response.usage.total_tokens,
        "latency_sec":    round(elapsed, 2),
        "context_chars":  len(raw_code),
        "files_loaded":   loaded_files,
        "model":          MODEL,
        "timestamp":      datetime.now().isoformat()
    }


# ── COMPARE ────────────────────────────────────────────────

def compare(query: str, top_k: int = 4) -> dict:
    """Run both approaches and return side-by-side comparison."""
    print(f"\n{'─' * 55}")
    print(f"  ▶ DeepWiki approach (GROQ_DEEPWIKI_KEY)...")
    wiki_result = run_deepwiki_approach(query, top_k)
    print(f"  ✅ {wiki_result['total_tokens']:,} tokens "
          f"| {wiki_result['latency_sec']}s")

    time.sleep(3)

    print(f"  ▶ Raw approach (GROQ_RAW_KEY)...")
    raw_result = run_raw_approach(query, wiki_result["source_files"])
    print(f"  ✅ {raw_result['total_tokens']:,} tokens "
          f"| {raw_result['latency_sec']}s")

    saved_tokens = raw_result["total_tokens"] - wiki_result["total_tokens"]
    saved_pct    = (
        saved_tokens / raw_result["total_tokens"] * 100
        if raw_result["total_tokens"] > 0 else 0
    )

    def cost(r):
        return (
            (r["prompt_tokens"] / 1_000_000) * 0.59 +
            (r["output_tokens"] / 1_000_000) * 0.79
        )

    return {
        "query":        query,
        "deepwiki":     wiki_result,
        "raw":          raw_result,
        "saved_tokens": saved_tokens,
        "saved_pct":    round(saved_pct, 1),
        "wiki_cost":    round(cost(wiki_result), 6),
        "raw_cost":     round(cost(raw_result),  6),
        "cost_saved":   round(cost(raw_result) - cost(wiki_result), 6),
        "model":        MODEL
    }