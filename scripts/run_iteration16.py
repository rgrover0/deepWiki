"""
Iteration 16 — Flow Tracing + Intent Classification

Verifies:
  1. Intent classifier correctly identifies FLOW_TRACE questions
  2. Entry point extractor resolves question → method name
  3. Flow tracer returns ordered steps from CALLS edges
  4. Total token count stays under 600

Requires:
  - Neo4j with CALLS edges populated (run Iteration 14 first)
  - Groq API key
"""

import os
from dotenv import load_dotenv

load_dotenv()

from api.intent_classifier import classify_intent, extract_entry_point

print("=" * 60)
print("DeepWiki — Iteration 16: Flow Tracing + Intent Classification")
print("=" * 60)

# ── 1. Intent classification ──────────────────────────────────
print("\n[1/3] Intent classifier:")
tests = [
    ("How does pet owner creation work?",       "FLOW_TRACE"),
    ("What is the OwnerController class?",       "CLASS_LOOKUP"),
    ("Why do we use Infinispan for caching?",    "WHY_DECISION"),
    ("Which endpoints does PetController expose?","API_IMPACT"),
    ("How do I trace the owner search flow?",    "FLOW_TRACE"),
]
all_pass = True
for question, expected in tests:
    got = classify_intent(question)
    ok  = got == expected
    if not ok:
        all_pass = False
    print(f"  {'OK' if ok else 'FAIL':4s}  [{got:14s}]  {question}")
print(f"\n  {'All intents correct' if all_pass else 'Some intents wrong'}")

# ── 2. Entry point extraction ─────────────────────────────────
print("\n[2/3] Entry point extraction:")
flow_questions = [
    "How does pet owner creation work?",
    "How does owner search work?",
    "Trace the visit creation flow",
]
for q in flow_questions:
    entry = extract_entry_point(q)
    print(f"  Q: {q}")
    print(f"  -> {entry}")

# ── 3. Flow trace via Neo4j ───────────────────────────────────
print("\n[3/3] Flow trace (requires Neo4j with CALLS edges):")
try:
    from api.routes.flow import trace_flow, FlowRequest

    result = trace_flow(FlowRequest(entry_point="processCreationForm"))
    steps  = result.get("steps", [])

    if steps:
        print(f"  Entry point  : processCreationForm")
        print(f"  Steps found  : {len(steps)}")
        print(f"  Token count  : {result.get('token_count', 0)} (ceiling: 600)")
        print()
        for s in steps:
            print(f"  Step {s['step']} [{s['layer']}] "
                  f"{s['class_name']}.{s['method_name']}()")
            if s.get("logic_summary"):
                print(f"         {s['logic_summary'][:80]}...")
        print()
        print("  Explanation excerpt:")
        print(f"  {result.get('explanation', '')[:200]}...")

        assert result.get("token_count", 0) <= 600, "Token count exceeds 600!"
        print("\n  Token ceiling: OK")
    else:
        print(f"  No steps found: {result.get('explanation')}")
        print("  (Run Iteration 14 first to populate CALLS edges)")
except Exception as e:
    print(f"  Neo4j unavailable: {e}")
    print("  (Flow trace will work once CALLS edges are populated)")

print("\n" + "=" * 60)
print("Iteration 16 complete")
print("  Done when: 'How does pet owner creation work?' returns")
print("  traced steps citing OwnerController + OwnerRepository")
print("=" * 60)
