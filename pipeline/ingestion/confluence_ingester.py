"""
Confluence MCP Ingester — Iteration 23.

Fetches Confluence pages via Atlassian REST API v2 (the recommended alternative
to a custom scraper when @atlassian/mcp-atlassian is not reachable from Python).
Classifies content, embeds into the appropriate Qdrant collection, scores
alignment against code wiki summaries, and writes Neo4j ConfluencePage nodes
with DOCUMENTS edges.

Env vars required:
  CONFLUENCE_URL    — e.g. https://your-org.atlassian.net
  CONFLUENCE_EMAIL  — Atlassian account email
  CONFLUENCE_TOKEN  — Atlassian API token (create at id.atlassian.com)

Optional:
  ANTHROPIC_API_KEY / GROQ_API_KEY — for content classification prompt
"""

import hashlib
import logging
import math
import os
import re
import time
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Content type -> Qdrant collection ─────────────────────────────────────────

CONTENT_COLLECTIONS: dict[str, Optional[str]] = {
    "meeting_notes": "deepwiki_confluence_meeting_notes",
    "api_docs":      "deepwiki_confluence_api_docs",
    "architecture":  "deepwiki_confluence_architecture",
    "user_flows":    "deepwiki_confluence_general",
    "server_db":     None,   # VAULT ONLY — never store in Qdrant
    "general":       "deepwiki_confluence_general",
}

CONTENT_TYPES = list(CONTENT_COLLECTIONS.keys())

# Alignment threshold — contradiction flag raised when score < this and category = "current"
CONTRADICTION_THRESHOLD = -0.3


# ── Atlassian REST API client ──────────────────────────────────────────────────

def _confluence_session() -> requests.Session:
    url   = os.getenv("CONFLUENCE_URL", "").rstrip("/")
    email = os.getenv("CONFLUENCE_EMAIL", "")
    token = os.getenv("CONFLUENCE_TOKEN", "")
    if not all([url, email, token]):
        raise EnvironmentError(
            "CONFLUENCE_URL, CONFLUENCE_EMAIL, and CONFLUENCE_TOKEN must be set in .env"
        )
    s = requests.Session()
    s.auth    = (email, token)
    s.headers = {"Accept": "application/json"}
    s.base    = url
    return s


def fetch_page(page_url_or_id: str) -> dict:
    """
    Fetch a Confluence page by URL or numeric page ID.
    Returns: {id, title, body_text, page_url, space_key, author, last_modified}
    """
    session = _confluence_session()
    base    = os.getenv("CONFLUENCE_URL", "").rstrip("/")

    # Extract page ID from URL like /wiki/spaces/SPACE/pages/123456/Title
    page_id = _extract_page_id(page_url_or_id)

    api_url = f"{base}/wiki/api/v2/pages/{page_id}?body-format=storage"
    resp    = session.get(api_url, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    body_storage = (
        data.get("body", {}).get("storage", {}).get("value", "")
        or data.get("body", {}).get("view",    {}).get("value", "")
    )
    body_text = _strip_html(body_storage)

    return {
        "id":            str(data["id"]),
        "title":         data.get("title", ""),
        "body_text":     body_text,
        "page_url":      f"{base}/wiki/spaces/{data.get('spaceId', '')}/pages/{data['id']}",
        "space_key":     data.get("spaceId", ""),
        "author":        data.get("version", {}).get("authorId", ""),
        "last_modified": data.get("version", {}).get("createdAt", ""),
    }


def _extract_page_id(url_or_id: str) -> str:
    if url_or_id.isdigit():
        return url_or_id
    # /pages/123456/...
    m = re.search(r"/pages/(\d+)", url_or_id)
    if m:
        return m.group(1)
    # ?pageId=123456
    m = re.search(r"pageId=(\d+)", url_or_id)
    if m:
        return m.group(1)
    raise ValueError(f"Cannot extract Confluence page ID from: {url_or_id!r}")


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ── Content classification ─────────────────────────────────────────────────────

_CLASSIFY_PROMPT = """You are a technical documentation classifier.
Given a Confluence page title and excerpt, classify it into exactly ONE of these types:

  meeting_notes   — action items, decisions from meetings, retrospectives
  api_docs        — REST endpoint docs, request/response schemas, Swagger annotations
  architecture    — system design diagrams, ADRs, tech stack decisions, module boundaries
  user_flows      — user story walkthroughs, UX flows, feature descriptions
  server_db       — passwords, connection strings, private keys, server IPs, DB credentials
  general         — anything else: how-to guides, FAQs, onboarding docs

Title: {title}
Excerpt (first 500 chars): {excerpt}

Reply with ONLY the type name, nothing else."""


def classify_content(title: str, body_text: str) -> str:
    """Return content_type string. Falls back to 'general' on LLM failure."""
    from core.llm.model_router import route as model_route
    excerpt = body_text[:500]
    prompt  = _CLASSIFY_PROMPT.format(title=title, excerpt=excerpt)
    try:
        adapter = model_route("annotation_extraction")
        raw, _  = adapter.complete(prompt, max_tokens=10, temperature=0.0)
        ctype   = raw.strip().lower().split()[0]
        if ctype in CONTENT_TYPES:
            logger.info("confluence: classified '%s' as %s", title, ctype)
            return ctype
    except Exception as e:
        logger.warning("confluence: classify failed (%s), defaulting to 'general'", e)
    return "general"


# ── Qdrant storage ─────────────────────────────────────────────────────────────

def embed_and_store(
    page_id: str,
    title: str,
    body_text: str,
    content_type: str,
    page_url: str,
    suite_id: str = "",
) -> Optional[str]:
    """
    Embed page and upsert into the appropriate Qdrant collection.
    Returns collection name, or None if content_type is server_db (vault-only).
    """
    collection = CONTENT_COLLECTIONS.get(content_type)
    if collection is None:
        logger.info("confluence: server_db page '%s' — vault only, skipping Qdrant", page_id)
        return None

    from core.embeddings.embedder import embed_text
    from core.embeddings.vector_store import get_client
    from qdrant_client.models import PointStruct

    text    = f"Title: {title}\n\n{body_text}"
    vector  = embed_text(text[:4000])   # keep within token budget
    point_id = int(hashlib.md5(page_id.encode()).hexdigest()[:8], 16)

    client = get_client()
    client.upsert(
        collection_name=collection,
        points=[PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "page_id":      page_id,
                "title":        title,
                "body_text":    body_text[:2000],
                "page_url":     page_url,
                "content_type": content_type,
                "suite_id":     suite_id,
            },
        )],
    )
    logger.info("confluence: stored page '%s' in %s", page_id, collection)
    return collection


# ── Alignment scoring ──────────────────────────────────────────────────────────

def compute_alignment(page_text: str, module_ids: list[str], driver) -> dict[str, float]:
    """
    Compare page embedding to class wiki summaries in each module.
    Returns {module_id: alignment_score} where score is in [-1.0, 1.0].

    Approach: embed page, search code_units collection filtered by module_ids,
    then compute avg cosine similarity (normalized vectors -> dot product).
    """
    from core.embeddings.embedder import embed_text
    from core.embeddings.vector_store import get_client
    from qdrant_client.models import Filter, FieldCondition, MatchAny

    page_vec = embed_text(page_text[:3000])
    client   = get_client()
    scores: dict[str, float] = {}

    for module_id in module_ids:
        try:
            # Search code units whose package contains the module name
            results = client.search(
                collection_name="deepwiki_code_units",
                query_vector=page_vec,
                query_filter=Filter(must=[
                    FieldCondition(key="module_id", match=MatchAny(any=[module_id]))
                ]),
                limit=5,
                with_vectors=False,
            )
            if not results:
                # Fallback: search without filter, use top results
                results = client.search(
                    collection_name="deepwiki_code_units",
                    query_vector=page_vec,
                    limit=5,
                    with_vectors=False,
                )

            if results:
                # Qdrant cosine scores are in [0, 1] for normalized vectors
                # Remap to [-1, 1]: alignment = 2*score - 1
                avg_qdrant = sum(r.score for r in results) / len(results)
                alignment  = round(2 * avg_qdrant - 1, 3)
            else:
                alignment = 0.0

            scores[module_id] = alignment
        except Exception as e:
            logger.warning("confluence: alignment for module %s failed: %s", module_id, e)
            scores[module_id] = 0.0

    return scores


# ── Neo4j write ────────────────────────────────────────────────────────────────

def write_confluence_node(
    driver,
    page_data: dict,
    module_ids: list[str],
    alignment_scores: dict[str, float],
    category: str,
    collection: Optional[str],
) -> dict:
    """
    Merge ConfluencePage node + DOCUMENTS edges.
    Raises ContradictionFlag node when alignment < CONTRADICTION_THRESHOLD and category = 'current'.
    Returns summary dict.
    """
    page_id    = page_data["id"]
    flags_created = []

    with driver.session() as session:
        # Upsert ConfluencePage node
        session.run("""
            MERGE (p:ConfluencePage {id: $id})
            SET p.title         = $title,
                p.page_url      = $page_url,
                p.content_type  = $content_type,
                p.category      = $category,
                p.collection    = $collection,
                p.author        = $author,
                p.last_modified = $last_modified,
                p.ingested_at   = timestamp()
        """, id=page_id, title=page_data["title"], page_url=page_data["page_url"],
             content_type=page_data.get("content_type", "general"), category=category,
             collection=collection or "vault", author=page_data.get("author", ""),
             last_modified=page_data.get("last_modified", ""))

        for module_id in module_ids:
            score = alignment_scores.get(module_id, 0.0)

            # Upsert Module node (may already exist from code ingestion)
            session.run("""
                MERGE (m:Module {id: $module_id})
                ON CREATE SET m.name = $module_id
            """, module_id=module_id)

            # Create/update DOCUMENTS edge
            session.run("""
                MATCH (p:ConfluencePage {id: $page_id})
                MATCH (m:Module {id: $module_id})
                MERGE (p)-[d:DOCUMENTS]->(m)
                SET d.alignment_score = $score,
                    d.category        = $category
            """, page_id=page_id, module_id=module_id, score=score, category=category)

            # Contradiction flag
            if score < CONTRADICTION_THRESHOLD and category == "current":
                flag_id = f"flag:{page_id}:{module_id}"
                session.run("""
                    MERGE (f:ContradictionFlag {id: $flag_id})
                    SET f.page_id        = $page_id,
                        f.module_id      = $module_id,
                        f.alignment_score = $score,
                        f.severity       = $severity,
                        f.resolved       = false,
                        f.created_at     = timestamp()
                """, flag_id=flag_id, page_id=page_id, module_id=module_id,
                     score=score, severity="HIGH" if score < -0.6 else "MEDIUM")
                flags_created.append(flag_id)
                logger.warning(
                    "confluence: ContradictionFlag raised — page=%s module=%s score=%.3f",
                    page_id, module_id, score,
                )

    return {
        "page_id":        page_id,
        "modules_linked": len(module_ids),
        "flags_created":  flags_created,
        "alignment":      alignment_scores,
    }


# ── Full pipeline entry point ──────────────────────────────────────────────────

def ingest_page(
    url_or_id: str,
    category: str = "current",
    module_tags: list[str] = None,
    suite_id: str = "",
) -> dict:
    """
    Full Confluence ingestion pipeline:
      1. Fetch page from Atlassian REST API
      2. Classify content type
      3. Embed + store in Qdrant (skipped for server_db)
      4. Compute alignment against tagged modules
      5. Write ConfluencePage node + DOCUMENTS edges to Neo4j

    Args:
        url_or_id:   Confluence page URL or numeric ID
        category:    historical | current | upcoming | update
        module_tags: Module IDs this page documents (e.g. ["owner-module", "auth-module"])
        suite_id:    Optional suite for Qdrant payload filtering

    Returns:
        Summary dict with page_id, content_type, collection, alignment scores, flags
    """
    from core.graph.schema import get_driver

    module_tags = module_tags or []
    result: dict = {}

    # 1. Fetch
    logger.info("confluence: fetching page %s", url_or_id)
    page_data = fetch_page(url_or_id)

    # 2. Classify
    content_type          = classify_content(page_data["title"], page_data["body_text"])
    page_data["content_type"] = content_type

    # 3. Embed + store
    collection = embed_and_store(
        page_id=page_data["id"],
        title=page_data["title"],
        body_text=page_data["body_text"],
        content_type=content_type,
        page_url=page_data["page_url"],
        suite_id=suite_id,
    )

    # 4. Alignment scoring
    driver = get_driver()
    alignment_scores: dict[str, float] = {}
    if module_tags:
        alignment_scores = compute_alignment(
            page_data["body_text"], module_tags, driver
        )

    # 5. Neo4j write
    write_result = write_confluence_node(
        driver=driver,
        page_data=page_data,
        module_ids=module_tags,
        alignment_scores=alignment_scores,
        category=category,
        collection=collection,
    )
    driver.close()

    result = {
        "page_id":      page_data["id"],
        "title":        page_data["title"],
        "page_url":     page_data["page_url"],
        "content_type": content_type,
        "collection":   collection,
        "category":     category,
        "module_tags":  module_tags,
        "alignment":    alignment_scores,
        "flags":        write_result["flags_created"],
    }
    logger.info("confluence: ingest complete — %s", result)
    return result


# ── Qdrant search (used by Ask route) ─────────────────────────────────────────

def search_confluence(
    query_vector: list[float],
    top_k: int = 3,
    content_types: list[str] = None,
    suite_id: str = "",
) -> list[dict]:
    """
    Search Confluence Qdrant collections for relevant pages.
    Returns list of {page_id, title, body_text, page_url, content_type, score}.
    """
    from core.embeddings.vector_store import get_client
    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

    client     = get_client()
    target_types = content_types or ["meeting_notes", "api_docs", "architecture", "user_flows", "general"]
    collections  = [
        CONTENT_COLLECTIONS[ct]
        for ct in target_types
        if CONTENT_COLLECTIONS.get(ct)
    ]

    all_results: list[dict] = []
    for coll in collections:
        try:
            filt = None
            if suite_id:
                filt = Filter(must=[FieldCondition(key="suite_id", match=MatchValue(value=suite_id))])
            hits = client.search(
                collection_name=coll,
                query_vector=query_vector,
                query_filter=filt,
                limit=top_k,
                with_payload=True,
            )
            for h in hits:
                p = h.payload or {}
                all_results.append({
                    "page_id":      p.get("page_id", ""),
                    "title":        p.get("title", ""),
                    "body_text":    p.get("body_text", ""),
                    "page_url":     p.get("page_url", ""),
                    "content_type": p.get("content_type", ""),
                    "score":        round(h.score, 4),
                })
        except Exception as e:
            logger.debug("confluence search skipped for %s: %s", coll, e)

    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:top_k]
