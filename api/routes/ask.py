"""
Ask route — updated Iteration 21.

Changes vs Iteration 16:
  - Uses model_router.route("ask") to select LLM adapter
  - Generates query_id per request; returned in response
  - Calls feedback.record_query() to persist Feedback node in Neo4j
  - Returns model_used in response so callers can display / log it
"""

import time
from fastapi import APIRouter
from pydantic import BaseModel
from qdrant_client.http.exceptions import UnexpectedResponse
from pipeline.embeddings.embedder import embed_text
from pipeline.embeddings.vector_store import get_client, semantic_search
from pipeline.graph.schema import get_driver
from api.intent_classifier import classify_intent, extract_entry_point
from api.model_router import route as model_route
from api import feedback as fb

router = APIRouter()

TOKEN_CEILING_CHARS = 2400   # ~600 tokens

ASK_PROMPT = """You are a code assistant with deep knowledge of a Spring Boot application.
Answer the developer's question using ONLY the wiki context provided below.
Be specific, technical, and reference actual class names and methods.

WIKI CONTEXT:
{context}
{confluence_context}
QUESTION: {question}

Answer concisely in 3-5 sentences. Reference specific classes and methods where relevant.
If Confluence design notes are provided, reference them to explain design intent."""

FLOW_ASK_PROMPT = """You are a code assistant. A developer asked: "{question}"

Here is the execution flow traced from the actual codebase:

{flow_steps}

Answer the question by explaining this flow step by step.
Reference actual class and method names. Under 300 words."""


class AskRequest(BaseModel):
    question: str
    top_k:    int  = 4
    scope:    str  = "repo"                        # "repo" | "suite" | "cross_suite"
    repo_id:  str  = "spring-petclinic"
    suite_id: str  = "pet-management-platform"


def _build_flow_context(flow_data: dict) -> str:
    steps = flow_data.get("steps", [])
    if not steps:
        return ""
    return "\n".join(
        f"Step {s['step']} [{s['layer']} · {s['class_name']}.{s['method_name']}()]: "
        f"{s['logic_summary'] or '(no summary)'}"
        for s in steps
    )


@router.post("")
def ask(req: AskRequest):
    query_id = fb.new_query_id()
    intent   = classify_intent(req.question)
    adapter  = model_route("ask")
    strategy = f"{intent}:{adapter.provider}/{adapter.model}"

    # ── FLOW_TRACE intent ─────────────────────────────────────
    if intent == "FLOW_TRACE":
        entry_point = extract_entry_point(req.question)

        from api.routes.flow import trace_flow, FlowRequest
        flow_data    = trace_flow(FlowRequest(entry_point=entry_point))
        flow_context = _build_flow_context(flow_data)
        sources      = [
            f"{s['class_name']}.{s['method_name']}()"
            for s in flow_data.get("steps", [])
        ]

        if not flow_context:
            intent = "CLASS_LOOKUP"   # fall through
        else:
            if len(flow_context) > TOKEN_CEILING_CHARS:
                flow_context = flow_context[:TOKEN_CEILING_CHARS] + "..."

            prompt = FLOW_ASK_PROMPT.format(
                question=req.question,
                flow_steps=flow_context,
            )
            flow_adapter = model_route("flow_trace", content_size=len(prompt))
            try:
                answer, token_count = flow_adapter.complete(prompt, max_tokens=350, temperature=0.2)
            except Exception as e:
                answer      = f"LLM error: {e}"
                token_count = 0

            fb.record_query(query_id, req.question,
                            f"FLOW_TRACE:{flow_adapter.provider}/{flow_adapter.model}",
                            f"{flow_adapter.provider}/{flow_adapter.model}")
            return {
                "answer":      answer,
                "sources":     sources,
                "scores":      [1.0] * len(sources),
                "intent":      intent,
                "token_count": token_count,
                "query_id":    query_id,
                "model_used":  f"{flow_adapter.provider}/{flow_adapter.model}",
            }

    # ── CLASS_LOOKUP / default: semantic search + wiki ────────
    query_vector = embed_text(req.question)
    qdrant       = get_client()
    repo_filter  = req.repo_id  if req.scope == "repo"  else None
    suite_filter = req.suite_id if req.scope == "suite" else None
    try:
        results = semantic_search(
            qdrant,
            query_vector,
            top_k=req.top_k,
            repo_id=repo_filter,
            suite_id=suite_filter,
        )
    except UnexpectedResponse as exc:
        fb.record_query(query_id, req.question, f"QDRANT_ERROR:{strategy}", f"{adapter.provider}/{adapter.model}")
        return {
            "answer": f"Search backend error: {exc}",
            "sources": [], "scores": [], "intent": intent,
            "token_count": 0, "query_id": query_id,
            "model_used": f"{adapter.provider}/{adapter.model}",
        }
    except Exception as exc:
        fb.record_query(query_id, req.question, f"SEARCH_ERROR:{strategy}", f"{adapter.provider}/{adapter.model}")
        return {
            "answer": f"Search is temporarily unavailable: {exc}",
            "sources": [], "scores": [], "intent": intent,
            "token_count": 0, "query_id": query_id,
            "model_used": f"{adapter.provider}/{adapter.model}",
        }

    if not results:
        fb.record_query(query_id, req.question, strategy, f"{adapter.provider}/{adapter.model}")
        return {
            "answer":     "No relevant classes found.",
            "sources":    [], "scores": [], "intent": intent,
            "token_count": 0, "query_id": query_id,
            "model_used": f"{adapter.provider}/{adapter.model}",
        }

    driver = get_driver()
    context_parts: list[str] = []

    with driver.session() as session:
        for r in results:
            row = session.run("""
                MATCH (c:Class {name: $name})
                RETURN c.wiki_summary AS summary, c.component_type AS type
            """, name=r["name"]).single()
            if row and row["summary"]:
                context_parts.append(f"[{row['type']}] {r['name']}: {row['summary']}")

    driver.close()

    context = "\n\n".join(context_parts)
    if len(context) > TOKEN_CEILING_CHARS:
        context = context[:TOKEN_CEILING_CHARS] + "..."

    # Enrich with Confluence design notes (Iteration 23)
    confluence_section = ""
    confluence_sources: list[str] = []
    try:
        from pipeline.ingestion.confluence_ingester import search_confluence
        conf_hits = search_confluence(query_vector, top_k=2, suite_id=req.suite_id)
        if conf_hits:
            parts = ["\nCONFLUENCE DESIGN NOTES:"]
            for h in conf_hits:
                parts.append(f"[{h['content_type'].upper()}] {h['title']}: {h['body_text'][:300]}")
                if h.get("page_url"):
                    confluence_sources.append(h["page_url"])
            confluence_section = "\n".join(parts) + "\n"
    except Exception:
        pass  # Confluence search is best-effort

    prompt = ASK_PROMPT.format(
        context=context,
        confluence_context=confluence_section,
        question=req.question,
    )
    ask_adapter = model_route("ask", content_size=len(prompt))
    try:
        answer, token_count = ask_adapter.complete(prompt, max_tokens=300, temperature=0.2)
    except Exception as e:
        answer      = f"LLM error: {e}"
        token_count = 0

    strategy = f"{intent}:{ask_adapter.provider}/{ask_adapter.model}"
    fb.record_query(query_id, req.question, strategy, f"{ask_adapter.provider}/{ask_adapter.model}")

    return {
        "answer":             answer,
        "sources":            [r["name"] for r in results],
        "scores":             [r["score"] for r in results],
        "confluence_sources": confluence_sources,
        "intent":             intent,
        "token_count":        token_count,
        "query_id":           query_id,
        "model_used":         f"{ask_adapter.provider}/{ask_adapter.model}",
    }
