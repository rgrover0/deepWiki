import time
from pipeline.comparison.claude_runner import (
    run_claude_no_cache,
    run_claude_with_cache,
    run_multi_turn_session
)

QUERY = "How does the application manage pet owners?"

MULTI_TURN_QUERIES = [
    "How does the application manage pet owners?",
    "What methods does it expose for that?",
    "How would I add a phone validation to that?",
    "What test cases should I write for that change?",
]

print("=" * 65)
print("Claude Token Behavior — Three Scenarios")
print("=" * 65)

# ── SCENARIO 1: NO CACHE ───────────────────────────────────
print("\n[1/3] Claude — Wiki context, NO cache")
r1 = run_claude_no_cache(QUERY)
print(f"""
  Input tokens  : {r1['input_tokens']:,}
  Output tokens : {r1['output_tokens']:,}
  Total         : {r1['total_tokens']:,}
  Latency       : {r1['latency_sec']}s
  Answer        : {r1['answer'][:150]}...
""")

time.sleep(3)

# ── SCENARIO 2: WITH CACHE (Call 1) ────────────────────────
print("[2/3] Claude — Wiki context, WITH cache (Call 1 — creates cache)")
r2a = run_claude_with_cache(QUERY)
print(f"""
  Input tokens    : {r2a['input_tokens']:,}
  Cache created   : {r2a['cache_created']:,} tokens cached
  Cache read      : {r2a['cache_read']:,}
  Output tokens   : {r2a['output_tokens']:,}
  Total           : {r2a['total_tokens']:,}
  Latency         : {r2a['latency_sec']}s
""")

time.sleep(3)

# ── SCENARIO 2: WITH CACHE (Call 2 — reads from cache) ─────
print("[2/3] Claude — Wiki context, WITH cache (Call 2 — reads cache)")
r2b = run_claude_with_cache("What methods does Owner expose for managing pets?")
print(f"""
  Input tokens    : {r2b['input_tokens']:,}
  Cache created   : {r2b['cache_created']:,}
  Cache read      : {r2b['cache_read']:,}  ← context read from cache
  Output tokens   : {r2b['output_tokens']:,}
  Effective cost  : {r2b['effective_tokens']:,} tokens (cache = 10% price)
  Latency         : {r2b['latency_sec']}s
""")

time.sleep(3)

# ── SCENARIO 3: MULTI-TURN (no wiki, accumulating context) ─
print("[3/3] Multi-turn conversation — context grows each turn")
results = run_multi_turn_session(MULTI_TURN_QUERIES)
print(f"\n  {'Turn':<6} {'Input':>8} {'Output':>8} {'Total':>8} {'History':>10}")
print(f"  {'─'*50}")
for r in results:
    print(
        f"  {r['turn']:<6} "
        f"{r['input_tokens']:>8,} "
        f"{r['output_tokens']:>8,} "
        f"{r['total_tokens']:>8,} "
        f"{r['history_size']:>6} msgs"
    )

total_multi = sum(r["total_tokens"] for r in results)
print(f"\n  Total tokens for 4-turn conversation: {total_multi:,}")

# ── SUMMARY ────────────────────────────────────────────────
print(f"""
{'=' * 65}
COMPARISON SUMMARY — Same Question, Three Approaches
{'=' * 65}

  Wiki, No Cache    : {r1['total_tokens']:>6,} tokens  (paid every call)
  Wiki + Cache #1   : {r2a['total_tokens']:>6,} tokens  (creates cache)
  Wiki + Cache #2   : {r2b['total_tokens']:>6,} tokens  (reads cache, 10% cost)
  Multi-turn avg    : {total_multi // len(results):>6,} tokens/turn (grows each turn)

  ✅ VERIFY on Anthropic dashboard:
     console.anthropic.com → Usage
     Look for cache_creation_tokens and cache_read_tokens
     cache_read costs 10% of normal input price
""")