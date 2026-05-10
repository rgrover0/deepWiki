import json
import os
from datetime import datetime, timedelta
from pipeline.metrics.token_tracker import load_metrics, log_token_usage, METRICS_FILE
from pipeline.metrics.calculator import calculate_savings, calculate_cost, calculate_roi

REPO_PATH = "repos/spring-petclinic"

print("=" * 60)
print("DeepWiki — Iteration 9: Token Metrics")
print("=" * 60)

# ── SEED DEMO DATA ─────────────────────────────────────────
# Simulate realistic queries a dev team would make
DEMO_QUERIES = [
    {
        "query": "How does the application manage pet owners?",
        "wiki_tokens": 2840,
        "source_files": [
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/Owner.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java",
        ]
    },
    {
        "query": "Which classes handle REST API requests?",
        "wiki_tokens": 1920,
        "source_files": [
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/PetController.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/vet/VetController.java",
        ]
    },
    {
        "query": "Add email validation to Owner",
        "wiki_tokens": 4200,
        "source_files": [
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/Owner.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java",
        ]
    },
    {
        "query": "How is pet visit history tracked?",
        "wiki_tokens": 2100,
        "source_files": [
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/Pet.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/Visit.java",
        ]
    },
    {
        "query": "Add endpoint to list all vets by specialty",
        "wiki_tokens": 5100,
        "source_files": [
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/vet/Vet.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/vet/VetController.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/vet/VetRepository.java",
        ]
    },
    {
        "query": "Where is data persistence configured?",
        "wiki_tokens": 1650,
        "source_files": [
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/OwnerRepository.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/vet/VetRepository.java",
        ]
    },
    {
        "query": "Add pet count validation per owner",
        "wiki_tokens": 4800,
        "source_files": [
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/Owner.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/Pet.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/PetController.java",
        ]
    },
    {
        "query": "What is the relationship between Pet and Owner?",
        "wiki_tokens": 1780,
        "source_files": [
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/Owner.java",
            f"{REPO_PATH}/src/main/java/org/springframework/samples/petclinic/owner/Pet.java",
        ]
    },
]

# Seed demo data if log is sparse
existing = load_metrics()
if len(existing) < 4:
    print("\n📊 Seeding demo metrics data...")
    base_time = datetime.now() - timedelta(hours=len(DEMO_QUERIES))

    for i, demo in enumerate(DEMO_QUERIES):
        entry = log_token_usage(
            query=demo["query"],
            wiki_tokens=demo["wiki_tokens"],
            source_files=demo["source_files"]
        )
        print(f"   Logged: '{demo['query'][:45]}...'")

    print(f"✅ Seeded {len(DEMO_QUERIES)} demo queries")
else:
    print(f"✅ Using {len(existing)} existing logged queries")

# ── LOAD AND CALCULATE ─────────────────────────────────────
log = load_metrics()
savings = calculate_savings(log)
roi = calculate_roi(log, team_size=5, queries_per_dev_per_day=20)

# ── PRINT REPORT ───────────────────────────────────────────
print(f"""
{'=' * 60}
TOKEN SAVINGS REPORT
{'=' * 60}

📊 SESSION SUMMARY
   Total queries logged  : {savings['queries']}
   Total tokens WITH wiki: {savings['total_wiki_tokens']:,}
   Total tokens WITHOUT  : {savings['total_raw_tokens']:,}
   Total tokens SAVED    : {savings['total_saved']:,}
   Reduction             : {savings['pct_saved']}%

📈 PER QUERY AVERAGE
   With DeepWiki    : {savings['avg_wiki_per_query']:,} tokens
   Without DeepWiki : {savings['avg_raw_per_query']:,} tokens
   Saved per query  : {savings['avg_raw_per_query'] - savings['avg_wiki_per_query']:,} tokens

💰 COST COMPARISON (Groq Llama 70B)
   Cost WITH wiki   : ${calculate_cost(savings['total_wiki_tokens']):.4f}
   Cost WITHOUT     : ${calculate_cost(savings['total_raw_tokens']):.4f}
   Saved this session: ${calculate_cost(savings['total_saved']):.4f}

🚀 PROJECTED ANNUAL ROI (Team of 5, 20 queries/dev/day)
   Annual queries      : {roi['annual_queries']:,}
   Annual tokens saved : {roi['annual_tokens_saved']:,}
   Annual cost WITHOUT : ${roi['annual_cost_raw_usd']:,.2f}
   Annual cost WITH    : ${roi['annual_cost_wiki_usd']:,.2f}
   Annual savings      : ${roi['annual_savings_usd']:,.2f}
   Provider            : {roi['provider']}

{'=' * 60}
""")

# Per-query breakdown
print("📋 PER QUERY BREAKDOWN")
print(f"{'Query':<45} {'Wiki':>8} {'Raw':>8} {'Saved':>8} {'%':>6}")
print("-" * 80)
for entry in log:
    saved_pct = (
        entry['saved_tokens'] / entry['raw_tokens'] * 100
        if entry['raw_tokens'] > 0 else 0
    )
    print(
        f"{entry['query'][:44]:<45} "
        f"{entry['wiki_tokens']:>8,} "
        f"{entry['raw_tokens']:>8,} "
        f"{entry['saved_tokens']:>8,} "
        f"{saved_pct:>5.0f}%"
    )

print(f"\n✅ Metrics saved to: {METRICS_FILE}")
print("✅ Open Streamlit → 📊 Token Metrics to see the dashboard")