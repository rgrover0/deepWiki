from pipeline.comparison.runner import compare

QUERIES = [
    "How does the application manage pet owners?",
    "Which class handles creating a new pet?",
    "How is data persisted in this application?",
]

print("=" * 65)
print("DeepWiki — Iteration 10: Real Token Comparison")
print("=" * 65)
print(f"\nModel: llama-3.3-70b-versatile (Groq)")
print("Both calls use the SAME model — only context differs")
print("Token counts match Groq Usage Dashboard exactly")
print("=" * 65)

all_results = []

for i, query in enumerate(QUERIES, 1):
    print(f"\n[{i}/{len(QUERIES)}] Query: '{query}'")
    result = compare(query, top_k=4)
    all_results.append(result)

    dw  = result["deepwiki"]
    raw = result["raw"]

    print(f"""
  ┌─────────────────────────┬──────────────────┬──────────────────┐
  │ Metric                  │ DeepWiki         │ Raw Source       │
  ├─────────────────────────┼──────────────────┼──────────────────┤
  │ Prompt tokens           │ {dw['prompt_tokens']:>10,}       │ {raw['prompt_tokens']:>10,}       │
  │ Output tokens           │ {dw['output_tokens']:>10,}       │ {raw['output_tokens']:>10,}       │
  │ TOTAL tokens            │ {dw['total_tokens']:>10,}       │ {raw['total_tokens']:>10,}       │
  │ Latency                 │ {dw['latency_sec']:>9.2f}s      │ {raw['latency_sec']:>9.2f}s      │
  │ Context size (chars)    │ {dw['context_chars']:>10,}       │ {raw['context_chars']:>10,}       │
  └─────────────────────────┴──────────────────┴──────────────────┘
  Tokens saved  : {result['saved_tokens']:,} ({result['saved_pct']}% reduction)
  Cost saved    : ${result['cost_saved']:.6f}
  """)

    print("  📖 DeepWiki Answer:")
    print(f"  {dw['answer'][:200]}...")
    print("\n  📄 Raw Answer:")
    print(f"  {raw['answer'][:200]}...")

    if i < len(QUERIES):
        import time
        print("\n  ⏳ Waiting 5s between queries (rate limit)...")
        time.sleep(5)

# ── SUMMARY ────────────────────────────────────────────────
print(f"\n{'=' * 65}")
print("AGGREGATE SUMMARY")
print(f"{'=' * 65}")

total_wiki_t = sum(r["deepwiki"]["total_tokens"] for r in all_results)
total_raw_t  = sum(r["raw"]["total_tokens"]      for r in all_results)
total_saved  = sum(r["saved_tokens"]             for r in all_results)
avg_pct      = sum(r["saved_pct"] for r in all_results) / len(all_results)

print(f"""
  Queries run             : {len(all_results)}
  Total tokens - DeepWiki : {total_wiki_t:,}
  Total tokens - Raw      : {total_raw_t:,}
  Total tokens saved      : {total_saved:,}
  Average reduction       : {avg_pct:.1f}%

  ✅ VERIFY THESE NUMBERS:
     → Groq dashboard : console.groq.com → Usage tab
     → Look for {len(all_results) * 2} API calls to {all_results[0]['model']}
     → Total should show ~{total_wiki_t + total_raw_t:,} tokens used
     → DeepWiki calls will be consistently smaller
""")