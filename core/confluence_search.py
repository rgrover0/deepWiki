"""Confluence vector search — read path shared by API /ask."""

from __future__ import annotations

from core.embeddings.vector_store import get_client

CONTENT_COLLECTIONS = {
    "meeting_notes": "deepwiki_confluence_meeting_notes",
    "api_docs": "deepwiki_confluence_api_docs",
    "architecture": "deepwiki_confluence_architecture",
    "user_flows": "deepwiki_confluence_general",
    "general": "deepwiki_confluence_general",
}


def search_confluence(
    query_vector: list[float],
    top_k: int = 3,
    content_types: list[str] | None = None,
    suite_id: str = "",
) -> list[dict]:
    """Search Confluence Qdrant collections for relevant pages."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    client = get_client()
    target_types = content_types or [
        "meeting_notes",
        "api_docs",
        "architecture",
        "user_flows",
        "general",
    ]
    collections = [
        CONTENT_COLLECTIONS[ct]
        for ct in target_types
        if CONTENT_COLLECTIONS.get(ct)
    ]

    all_results: list[dict] = []
    for coll in collections:
        try:
            filt = None
            if suite_id:
                filt = Filter(
                    must=[FieldCondition(key="suite_id", match=MatchValue(value=suite_id))]
                )
            hits = client.search(
                collection_name=coll,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filt,
            )
            for hit in hits:
                payload = hit.payload or {}
                all_results.append(
                    {
                        "page_id": payload.get("page_id", ""),
                        "title": payload.get("title", ""),
                        "body_text": payload.get("body_text", payload.get("text", "")),
                        "page_url": payload.get("page_url", ""),
                        "content_type": payload.get("content_type", ""),
                        "score": hit.score,
                    }
                )
        except Exception:
            continue

    all_results.sort(key=lambda r: r.get("score", 0), reverse=True)
    return all_results[:top_k]
