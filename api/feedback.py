"""
Feedback — Iteration 21.

Stores query feedback (thumbs up/down) in Neo4j as Feedback nodes.

Lifecycle:
  1. ask.py calls record_query() when generating an answer  →  creates Feedback node
  2. User clicks thumbs up/down                            →  POST /feedback updates it
  3. GET /feedback/stats aggregates thumbs-up ratios per strategy

Node schema:
  (:Feedback {
      id:                  str,       12-char uuid hex
      question:            str,       truncated to 500 chars
      retrieval_strategy:  str,       e.g. "CLASS_LOOKUP:groq/llama-3.3-70b-versatile"
      model_used:          str,       e.g. "groq/llama-3.3-70b-versatile"
      was_helpful:         bool|null, null until user votes
      created_at:          datetime,
      updated_at:          datetime,
  })
"""

import logging
import uuid

from fastapi import APIRouter
from pydantic import BaseModel
from pipeline.graph.schema import get_driver

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

def new_query_id() -> str:
    return uuid.uuid4().hex[:12]


def record_query(
    query_id:           str,
    question:           str,
    retrieval_strategy: str,
    model_used:         str,
) -> None:
    """
    Persist an initial Feedback node.
    Swallows all errors — feedback must never break the answer path.
    """
    try:
        driver = get_driver()
        with driver.session() as session:
            session.run("""
                MERGE (f:Feedback {id: $id})
                ON CREATE SET
                    f.question           = $question,
                    f.retrieval_strategy = $strategy,
                    f.model_used         = $model,
                    f.was_helpful        = null,
                    f.created_at         = datetime(),
                    f.updated_at         = datetime()
                ON MATCH SET
                    f.updated_at         = datetime()
            """,
                id       = query_id,
                question = question[:500],
                strategy = retrieval_strategy,
                model    = model_used,
            )
        driver.close()
    except Exception as e:
        logger.warning("record_query failed (non-fatal): %s", e)


# ── Routes ─────────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    query_id:  str
    thumbs_up: bool


@router.post("")
def submit_feedback(req: FeedbackRequest):
    """Record a thumbs-up or thumbs-down vote on a past query."""
    try:
        driver = get_driver()
        with driver.session() as session:
            result = session.run("""
                MATCH (f:Feedback {id: $id})
                SET f.was_helpful = $helpful,
                    f.updated_at  = datetime()
                RETURN f.id AS id
            """, id=req.query_id, helpful=req.thumbs_up).single()
        driver.close()

        if result:
            return {"ok": True, "query_id": req.query_id, "was_helpful": req.thumbs_up}
        return {"ok": False, "reason": "query_id not found — answer may not have been recorded yet"}

    except Exception as e:
        return {"ok": False, "reason": str(e)}


@router.get("/stats")
def feedback_stats():
    """Thumbs-up ratio grouped by retrieval strategy — useful for A/B comparison."""
    try:
        driver = get_driver()
        with driver.session() as session:
            rows = session.run("""
                MATCH (f:Feedback)
                WHERE f.was_helpful IS NOT NULL
                RETURN f.retrieval_strategy                          AS strategy,
                       count(f)                                      AS total,
                       sum(CASE WHEN f.was_helpful THEN 1 ELSE 0 END) AS helpful
                ORDER BY total DESC
            """).data()
        driver.close()
        return {
            "strategies": [
                {
                    "strategy": r["strategy"],
                    "total":    r["total"],
                    "helpful":  r["helpful"],
                    "score":    round(r["helpful"] / r["total"], 2) if r["total"] else 0.0,
                }
                for r in rows
            ]
        }
    except Exception as e:
        return {"strategies": [], "error": str(e)}
