import os
import time
from fastapi import APIRouter
from pydantic import BaseModel
from groq import Groq
from pipeline.embeddings.embedder import embed_text
from pipeline.embeddings.vector_store import get_client, semantic_search
from pipeline.graph.schema import get_driver
from api.intent_classifier import classify_intent, extract_entry_point
from dotenv import load_dotenv

load_dotenv()

router      = APIRouter()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TOKEN_CEILING_CHARS = 2400   # ~600 tokens

ASK_PROMPT = """You are a code assistant with deep knowledge of a Spring Boot application.
Answer the developer's question using ONLY the wiki context provided below.
Be specific, technical, and reference actual class names and methods.

WIKI CONTEXT:
{context}

QUESTION: {question}

Answer concisely in 3-5 sentences. Reference specific classes and methods where relevant."""

FLOW_ASK_PROMPT = """You are a code assistant. A developer asked: "{question}"

Here is the execution flow traced from the actual codebase:

{flow_steps}

Answer the question by explaining this flow step by step.
Reference actual class and method names. Under 300 words."""


class AskRequest(BaseModel):
    question: str
    top_k: int = 4
    scope: str = "repo"                       # "repo" | "suite" | "cross_suite"
    repo_id: str = "spring-petclinic"
    suite_id: str = "pet-management-platform"


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
    intent = classify_intent(req.question)

    # ── FLOW_TRACE intent: use flow tracer ───────────────────
    if intent == "FLOW_TRACE":
        entry_point = extract_entry_point(req.question)

        driver = get_driver()
        from api.routes.flow import trace_flow, FlowRequest
        flow_data = trace_flow(FlowRequest(entry_point=entry_point))

        flow_context = _build_flow_context(flow_data)
        sources      = [
            f"{s['class_name']}.{s['method_name']}()"
            for s in flow_data.get("steps", [])
        ]

        if not flow_context:
            # Fall through to class lookup if no flow found
            intent = "CLASS_LOOKUP"
        else:
            # Enforce 600-token ceiling
            if len(flow_context) > TOKEN_CEILING_CHARS:
                flow_context = flow_context[:TOKEN_CEILING_CHARS] + "…"

            try:
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": FLOW_ASK_PROMPT.format(
                        question=req.question,
                        flow_steps=flow_context,
                    )}],
                    max_tokens=350,
                    temperature=0.2,
                )
                answer      = response.choices[0].message.content.strip()
                token_count = (response.usage.prompt_tokens or 0) + (response.usage.completion_tokens or 0)
            except Exception as e:
                answer      = f"LLM error: {e}"
                token_count = 0

            return {
                "answer":       answer,
                "sources":      sources,
                "scores":       [1.0] * len(sources),
                "intent":       intent,
                "token_count":  token_count,
            }

    # ── CLASS_LOOKUP / default: semantic search + wiki ───────
    query_vector  = embed_text(req.question)
    qdrant        = get_client()
    repo_filter   = req.repo_id  if req.scope == "repo"  else None
    suite_filter  = req.suite_id if req.scope == "suite" else None
    results       = semantic_search(qdrant, query_vector, top_k=req.top_k,
                                    repo_id=repo_filter, suite_id=suite_filter)

    if not results:
        return {"answer": "No relevant classes found.", "sources": [],
                "scores": [], "intent": intent}

    driver = get_driver()
    context_parts: list[str] = []

    with driver.session() as session:
        for r in results:
            row = session.run("""
                MATCH (c:Class {name: $name})
                RETURN c.wiki_summary AS summary, c.component_type AS type
            """, name=r["name"]).single()

            if row and row["summary"]:
                context_parts.append(
                    f"[{row['type']}] {r['name']}: {row['summary']}"
                )

    driver.close()

    # Enforce 600-token ceiling
    context = "\n\n".join(context_parts)
    if len(context) > TOKEN_CEILING_CHARS:
        context = context[:TOKEN_CEILING_CHARS] + "…"

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": ASK_PROMPT.format(
                context=context,
                question=req.question,
            )}],
            max_tokens=300,
            temperature=0.2,
        )
        answer      = response.choices[0].message.content.strip()
        token_count = (response.usage.prompt_tokens or 0) + (response.usage.completion_tokens or 0)
    except Exception as e:
        answer      = f"LLM error: {e}"
        token_count = 0

    return {
        "answer":      answer,
        "sources":     [r["name"] for r in results],
        "scores":      [r["score"] for r in results],
        "intent":      intent,
        "token_count": token_count,
    }
