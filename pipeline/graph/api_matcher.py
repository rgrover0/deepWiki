"""
API Matcher — Iteration 19.

For each Angular HttpClient call (normalised path from ts-morph service),
match against APIContract nodes in Neo4j and create CONSUMES edges.

Match levels:
  1.0  exact   — method + canonicalized path identical
  0.7  fuzzy   — same segment count, path similarity ≥ 0.85
  0.0  unknown — no match (logged, no edge written)

Edge schema:
  (Repository)-[:CONSUMES {
      caller_class, caller_method, confidence, normalized_url, updated_at
  }]->(APIContract)
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Path helpers ───────────────────────────────────────────────────────────────

def _canonicalize(path: str) -> str:
    """Normalize any {param} placeholder to {x} and strip trailing slash."""
    normalized = re.sub(r'\{[^}]+\}', '{x}', path).lower().rstrip('/')
    return normalized or '/'


def path_similarity(a: str, b: str) -> float:
    """
    Compute path similarity between two URL paths.

    Identical after canonicalization → 1.0.
    Segment-level comparison on equal-length paths → fraction of matching segments.
    Different length → 0.0.
    """
    ca, cb = _canonicalize(a), _canonicalize(b)
    if ca == cb:
        return 1.0

    segs_a = [s for s in ca.split('/') if s]
    segs_b = [s for s in cb.split('/') if s]

    if not segs_a or not segs_b or len(segs_a) != len(segs_b):
        return 0.0

    matches = sum(1 for x, y in zip(segs_a, segs_b) if x == y)
    return matches / len(segs_a)


# ── Matching ───────────────────────────────────────────────────────────────────

def match_http_calls(
    http_calls: list[dict],
    contracts: list[dict],
) -> list[dict]:
    """
    Match Angular HttpClient calls against known APIContracts.

    Args:
        http_calls: [{method, normalized_url, source_method, url}]
        contracts:  [{id, http_method, path, controller_class, controller_method}]

    Returns:
        [{call, match, confidence}]
        match is the best-matching contract dict, or None if below threshold.
    """
    results = []
    for call in http_calls:
        method = call.get("method", "").upper()
        url    = call.get("normalized_url", "")

        best_match: Optional[dict] = None
        best_score = 0.0

        for contract in contracts:
            if contract.get("http_method", "").upper() != method:
                continue
            score = path_similarity(url, contract.get("path", ""))
            if score > best_score:
                best_score = score
                best_match = contract

        if best_score == 1.0:
            confidence = 1.0
        elif best_score >= 0.85:
            confidence = 0.7
        else:
            best_match = None
            confidence = 0.0

        results.append({
            "call":       call,
            "match":      best_match,
            "confidence": confidence,
        })

    return results


# ── Graph writer ───────────────────────────────────────────────────────────────

def write_consumes_edges(
    session,
    fe_repo_id: str,
    caller_class: str,
    matched_calls: list[dict],
) -> dict:
    """
    Write CONSUMES edges into Neo4j for all matched calls.

    The MERGE key is (repo_id, contract_id, caller_class, caller_method) so
    re-running is idempotent. Confidence and timestamp are always refreshed.

    Returns:
        {written, fuzzy, unknown}
        written = exact confidence 1.0
        fuzzy   = confidence 0.7 (still persisted, flagged for review)
        unknown = no match found (not persisted)
    """
    written = fuzzy = unknown = 0

    for item in matched_calls:
        match      = item.get("match")
        confidence = item.get("confidence", 0.0)
        call       = item.get("call", {})

        if not match or confidence == 0.0:
            logger.debug(
                "No match: %s %s (from %s.%s)",
                call.get("method"), call.get("normalized_url"),
                caller_class, call.get("source_method"),
            )
            unknown += 1
            continue

        session.run("""
            MATCH (r:Repository {id: $repo_id})
            MATCH (a:APIContract {id: $contract_id})
            MERGE (r)-[c:CONSUMES {
                caller_class:  $caller_class,
                caller_method: $caller_method
            }]->(a)
            SET c.confidence     = $confidence,
                c.normalized_url = $url,
                c.updated_at     = datetime()
        """,
            repo_id=fe_repo_id,
            contract_id=match["id"],
            caller_class=caller_class,
            caller_method=call.get("source_method", ""),
            confidence=confidence,
            url=call.get("normalized_url", ""),
        )
        logger.info(
            "CONSUMES [%.1f]: %s.%s -> %s %s",
            confidence, caller_class, call.get("source_method"),
            call.get("method"), call.get("normalized_url"),
        )

        if confidence == 1.0:
            written += 1
        else:
            fuzzy += 1

    return {"written": written, "fuzzy": fuzzy, "unknown": unknown}


# ── Full pipeline ──────────────────────────────────────────────────────────────

def run_api_matching(
    driver,
    fe_repo_id: str,
    be_repo_id: str,
    file_analysis_results: list[dict],
) -> dict:
    """
    Main entry point.

    For each Angular class with http_calls, load all APIContracts for be_repo_id,
    match, and write CONSUMES edges with the FE repo as the consumer.

    Returns:
        {written, fuzzy, unknown, classes_processed}
    """
    totals = {"written": 0, "fuzzy": 0, "unknown": 0, "classes_processed": 0}

    with driver.session() as session:
        rows = session.run("""
            MATCH (r:Repository {id: $repo_id})-[:EXPOSES]->(a:APIContract)
            RETURN a.id                 AS id,
                   a.http_method        AS http_method,
                   a.path               AS path,
                   a.controller_class   AS controller_class,
                   a.controller_method  AS controller_method
        """, repo_id=be_repo_id).data()

        contracts = list(rows)
        if not contracts:
            logger.warning("No APIContracts for backend repo '%s'. Run Iteration 15 first.", be_repo_id)
            return totals

        logger.info("Loaded %d API contracts from '%s'", len(contracts), be_repo_id)

        for file_result in file_analysis_results:
            for cls in file_result.get("classes", []):
                http_calls = cls.get("http_calls", [])
                if not http_calls:
                    continue

                caller_class = cls.get("name", "Unknown")
                matched      = match_http_calls(http_calls, contracts)
                stats        = write_consumes_edges(session, fe_repo_id, caller_class, matched)

                totals["written"]           += stats["written"]
                totals["fuzzy"]             += stats["fuzzy"]
                totals["unknown"]           += stats["unknown"]
                totals["classes_processed"] += 1

                logger.info(
                    "  %s — %d calls: %d exact, %d fuzzy, %d unknown",
                    caller_class,
                    len(http_calls),
                    stats["written"],
                    stats["fuzzy"],
                    stats["unknown"],
                )

    return totals
