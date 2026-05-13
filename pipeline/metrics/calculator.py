import os
from pathlib import Path

# Groq Llama 3.3 70B pricing (per million tokens)
PRICING = {
    "groq": {
        "input":  0.59,
        "output": 0.79,
        "label":  "Groq Llama 3.3 70B (Free tier used)"
    },
    "claude": {
        "input":  3.00,
        "output": 15.00,
        "label":  "Claude Sonnet (if used)"
    },
    "gpt4o": {
        "input":  5.00,
        "output": 15.00,
        "label":  "GPT-4o (if used)"
    }
}

AVG_OUTPUT_RATIO = 0.3   # output is ~30% of total tokens


def estimate_raw_tokens(source_files: list[str]) -> int:
    """
    Estimate tokens needed WITHOUT wiki.
    Without DeepWiki, a developer query would need to load
    the full source files into context.
    """
    total = 0
    for f in source_files:
        if f and os.path.exists(f):
            try:
                text = Path(f).read_text(encoding="utf-8", errors="replace")
                total += len(text) // 4   # chars/4 ≈ tokens
            except Exception:
                total += 2000             # fallback estimate
        else:
            total += 2000                 # file not available estimate
    return max(total, 5000)              # minimum realistic baseline


def calculate_savings(log: list[dict]) -> dict:
    """Calculate aggregate savings from token log."""
    if not log:
        return {}

    total_wiki_tokens = sum(e.get("wiki_tokens", 0) for e in log)
    total_raw_tokens  = sum(e.get("raw_tokens", 0)  for e in log)
    total_saved       = sum(e.get("saved_tokens", 0) for e in log)
    queries           = len(log)

    avg_wiki = total_wiki_tokens / queries if queries else 0
    avg_raw  = total_raw_tokens  / queries if queries else 0
    pct_saved = (
        (total_saved / total_raw_tokens * 100)
        if total_raw_tokens > 0 else 0
    )

    return {
        "queries":            queries,
        "total_wiki_tokens":  total_wiki_tokens,
        "total_raw_tokens":   total_raw_tokens,
        "total_saved":        total_saved,
        "avg_wiki_per_query": int(avg_wiki),
        "avg_raw_per_query":  int(avg_raw),
        "pct_saved":          round(pct_saved, 1),
    }


def calculate_cost(tokens: int, provider: str = "groq") -> float:
    """Calculate API cost in USD for given token count."""
    p = PRICING[provider]
    input_tokens  = tokens * (1 - AVG_OUTPUT_RATIO)
    output_tokens = tokens * AVG_OUTPUT_RATIO
    return (
        (input_tokens  / 1_000_000) * p["input"] +
        (output_tokens / 1_000_000) * p["output"]
    )


def calculate_roi(
    log: list[dict],
    team_size: int = 5,
    queries_per_dev_per_day: int = 20,
    work_days_per_year: int = 240,
    provider: str = "groq"
) -> dict:
    """Project annual team ROI."""
    savings = calculate_savings(log)
    if not savings:
        return {}

    avg_saved_per_query = (
        savings["total_saved"] / savings["queries"]
        if savings["queries"] else 0
    )

    annual_queries  = team_size * queries_per_dev_per_day * work_days_per_year
    annual_saved_t  = annual_queries * avg_saved_per_query
    annual_cost_raw  = calculate_cost(
        annual_queries * savings["avg_raw_per_query"],
        provider
    )
    annual_cost_wiki = calculate_cost(
        annual_queries * savings["avg_wiki_per_query"],
        provider
    )
    annual_savings_usd = annual_cost_raw - annual_cost_wiki

    return {
        "team_size":            team_size,
        "annual_queries":       annual_queries,
        "annual_tokens_saved":  int(annual_saved_t),
        "annual_cost_raw_usd":  round(annual_cost_raw, 2),
        "annual_cost_wiki_usd": round(annual_cost_wiki, 2),
        "annual_savings_usd":   round(annual_savings_usd, 2),
        "provider":             PRICING[provider]["label"]
    }