import os
import time
from fastapi import APIRouter
from pydantic import BaseModel
from groq import Groq
from pipeline.embeddings.embedder import embed_text
from pipeline.embeddings.vector_store import get_client, semantic_search
from pipeline.graph.schema import get_driver
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ASK_PROMPT = """You are a code assistant with deep knowledge of a Spring Boot application.
Answer the developer's question using ONLY the wiki context provided below.
Be specific, technical, and reference actual class names and methods.

WIKI CONTEXT:
{context}

QUESTION: {question}

Answer concisely in 3-5 sentences. Reference specific classes and methods where relevant."""


class AskRequest(BaseModel):
    question: str
    top_k: int = 4


@router.post("/")
def ask(req: AskRequest):
    # 1. Semantic search for relevant classes
    query_vector = embed_text(req.question)
    qdrant = get_client()
    results = semantic_search(qdrant, query_vector, top_k=req.top_k)

    if not results:
        return {"answer": "No relevant classes found.", "sources": []}

    # 2. Fetch wiki summaries from Neo4j
    driver = get_driver()
    context_parts = []

    with driver.session() as session:
        for r in results:
            row = session.run("""
                MATCH (c:Class {name: $name})
                RETURN c.wiki_summary AS summary,
                       c.component_type AS type
            """, name=r["name"]).single()

            if row and row["summary"]:
                context_parts.append(
                    f"[{row['type']}] {r['name']}: {row['summary']}"
                )

    driver.close()

    context = "\n\n".join(context_parts)

    # 3. Ask LLM
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": ASK_PROMPT.format(
                    context=context,
                    question=req.question
                )
            }],
            max_tokens=300,
            temperature=0.2
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"LLM error: {str(e)}"

    return {
        "answer":  answer,
        "sources": [r["name"] for r in results],
        "scores":  [r["score"] for r in results]
    }