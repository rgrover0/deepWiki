import streamlit as st
import requests

# ── PASSWORD GATE ──────────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("📚 DeepWiki")
        st.caption("Codebase Intelligence Platform")
        st.divider()

        pwd = st.text_input("Enter demo password:", type="password")
        if st.button("Enter", type="primary"):
            if pwd == st.secrets.get("DEMO_PASSWORD", "deepwiki2026"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return True

if not check_password():
    st.stop()

# ── API URL FROM SECRETS ────────────────────────────────────
API = st.secrets.get("API_URL", "http://localhost:8000").rstrip("/")


def safe_get(endpoint: str, default=None):
    # Ensure single slash between base and path
    url = f"{API}/{endpoint.lstrip('/')}"

    """GET request with error handling."""
    try:
        resp = requests.get(f"{API}{endpoint}", timeout=30)
        if resp.status_code == 200 and resp.text.strip():
            return resp.json()
        st.error(f"API error {resp.status_code}: {resp.text[:200]}")
        return default
    except requests.exceptions.ConnectionError:
        st.error("❌ API not running. Start with: `uvicorn api.main:app --reload --port 8000`")
        return default
    except Exception as e:
        st.error(f"❌ Request failed: {e}")
        return default


def safe_post(endpoint: str, payload: dict, default=None):
    # Ensure single slash between base and path
    url = f"{API}/{endpoint.lstrip('/')}"
    """POST request with error handling."""
    try:
        resp = requests.post(
            f"{API}{endpoint}",
            json=payload,
            timeout=120      # LLM calls can be slow
        )
        if resp.status_code == 200 and resp.text.strip():
            return resp.json()
        st.error(f"API error {resp.status_code}: {resp.text[:300]}")
        return default
    except requests.exceptions.ConnectionError:
        st.error("❌ API not running. Start with: `uvicorn api.main:app --reload --port 8000`")
        return default
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. LLM may be slow — try again.")
        return default
    except Exception as e:
        st.error(f"❌ Request failed: {e}")
        return default

st.set_page_config(
    page_title="DeepWiki",
    page_icon="📚",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("📚 DeepWiki")
st.sidebar.caption("Codebase Knowledge Portal")

page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Overview",
        "🔍 Class Explorer",
        "🔎 Semantic Search",
        "💬 Ask DeepWiki",
        "📋 Plan & Tests",
        "📊 Token Metrics",
        "⚖️ Live Comparison",    # ← add after Token Metrics
    ]
)

# Add to sidebar in ui/app.py after the navigation radio:
st.sidebar.divider()
try:
    health = requests.get(f"{API}/health", timeout=3).json()
    st.sidebar.success("✅ API connected")
except Exception:
    st.sidebar.error("❌ API offline")
    st.sidebar.code("uvicorn api.main:app --reload --port 8000")
st.sidebar.caption("Spring PetClinic · Local POC")


# ── OVERVIEW ──────────────────────────────────────────────
if page == "🏠 Overview":
    st.title("📚 DeepWiki — Codebase Knowledge Graph")

    # Stats
    try:
        # stats = requests.get(f"{API}/stats").json()
        # AFTER (safe):
        stats = safe_get("/stats", default={"nodes": {}, "relationships": {}})
        if not stats:
            st.stop()

        nodes = stats.get("nodes", {})
        rels  = stats.get("relationships", {})

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Classes",       nodes.get("Class",  0))
        col2.metric("Methods",       nodes.get("Method", 0))
        col3.metric("Fields",        nodes.get("Field",  0))
        col4.metric("Relationships", sum(rels.values()))
    except Exception:
        st.warning("⚠️ API not reachable. Start the API first.")
        st.stop()

    st.divider()

    # Class list grouped by type
    classes = safe_get("/classes/", default=[])
    if not classes:
        st.stop()

    types = {}
    for cls in classes:
        t = cls["component_type"]
        types.setdefault(t, []).append(cls)

    for comp_type, items in sorted(types.items()):
        with st.expander(f"**{comp_type}** ({len(items)})", expanded=True):
            for item in items:
                col1, col2 = st.columns([2, 5])
                col1.code(item["name"])
                summary = item.get("wiki_summary") or "No summary yet."
                col2.caption(summary[:120] + "..." if len(summary) > 120 else summary)


    st.divider()
    st.subheader("🗺️ Architecture Diagram")
    arch = safe_get("/architecture", default={"diagram": ""})
    diagram = arch.get("diagram", "")

    if diagram:
        # Strip markdown fences if present
        mermaid_code = diagram
        for fence in ["```mermaid", "```"]:
            mermaid_code = mermaid_code.replace(fence, "")
        mermaid_code = mermaid_code.strip()

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0; background:white;">
        <div class="mermaid" style="padding:20px;">
{mermaid_code}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose'
            }});
        </script>
        </body>
        </html>
        """
        st.components.v1.html(html, height=700, scrolling=True)

        # Also show raw diagram as fallback
        with st.expander("📄 View raw Mermaid code"):
            st.code(mermaid_code, language="text")
    else:
        st.info("No architecture diagram found. Run Iteration 5 first.")


# ── CLASS EXPLORER ─────────────────────────────────────────
elif page == "🔍 Class Explorer":
    st.title("🔍 Class Explorer")

    classes = safe_get("/classes/", default=[])
    names   = [c["name"] for c in classes]

    selected = st.selectbox("Select a class", names)

    if selected:
        cls = safe_get(f"/classes/{selected}", default={})

        col1, col2 = st.columns([1, 2])
        col1.metric("Type",    cls["component_type"])
        col2.metric("Package", cls["package"] or "—")

        st.divider()

        # Wiki summary
        st.subheader("📖 Wiki Summary")
        st.info(cls.get("wiki_summary") or "No summary available.")

        # Methods + Fields side by side
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"⚙️ Methods ({len(cls['methods'])})")
            for m in cls["methods"]:
                with st.expander(f"`{m['name']}`"):
                    st.write(f"**Returns:** `{m.get('return_type','void')}`")
                    if m.get("params"):
                        st.write(f"**Params:** {', '.join(m['params'])}")
                    if m.get("annotations"):
                        st.write(f"**Annotations:** {', '.join(m['annotations'])}")

        with col2:
            st.subheader(f"📦 Fields ({len(cls['fields'])})")
            for f in cls["fields"]:
                with st.expander(f"`{f['name']}`"):
                    st.write(f"**Type:** `{f.get('type','?')}`")
                    if f.get("annotations"):
                        st.write(f"**Annotations:** {', '.join(f['annotations'])}")

        # Dependencies
        if cls.get("dependencies"):
            st.divider()
            st.subheader("🔗 Depends On")
            for dep in cls["dependencies"]:
                st.code(dep)


# ── SEMANTIC SEARCH ────────────────────────────────────────
elif page == "🔎 Semantic Search":
    st.title("🔎 Semantic Search")
    st.caption("Search classes by meaning, not just keywords")

    query = st.text_input("Search query", placeholder="Which class handles pet data?")

    col1, col2 = st.columns([1, 3])
    top_k = col1.slider("Results", 1, 10, 5)

    types_list = ["All", "REST_CONTROLLER", "SERVICE",
                  "REPOSITORY", "ENTITY", "COMPONENT"]
    filter_type = col2.selectbox("Filter by type", types_list)

    if query:
        payload = {
            "query": query,
            "top_k": top_k,
            "component_type": None if filter_type == "All" else filter_type
        }
        resp = safe_post("/search/", payload, default={"results": []})

        st.divider()
        st.subheader(f"Results for: *{query}*")

        for i, r in enumerate(resp["results"], 1):
            score_pct = int(r["score"] * 100)
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                col1.markdown(f"**{i}. {r['name']}**")
                col2.caption(f"`{r['component_type']}`")
                col3.progress(score_pct, text=f"{score_pct}%")

                if r.get("methods"):
                    st.caption(f"Methods: {', '.join(r['methods'][:5])}")
                st.divider()


# ── ASK DEEPWIKI ───────────────────────────────────────────
elif page == "💬 Ask DeepWiki":
    st.title("💬 Ask DeepWiki")
    st.caption("Ask anything about the codebase — answers grounded in the wiki")

    # Example questions
    examples = [
        "How does the application manage pet owners?",
        "Which classes handle REST API requests?",
        "How is data persisted in this application?",
        "What is the relationship between Pet and Owner?",
    ]

    st.subheader("💡 Example questions")
    cols = st.columns(2)
    for i, ex in enumerate(examples):
        if cols[i % 2].button(ex, use_container_width=True):
            st.session_state["question"] = ex

    st.divider()

    question = st.text_area(
        "Your question",
        value=st.session_state.get("question", ""),
        height=80,
        placeholder="Ask about any part of the codebase..."
    )

    if st.button("🔍 Ask", type="primary") and question:
        with st.spinner("Searching wiki and generating answer..."):
            resp = safe_post("/ask/", {"question": question, "top_k": 4}, default={"answer": "", "sources": [], "scores": []})

        st.subheader("💡 Answer")
        st.success(resp["answer"])

        st.subheader("📎 Sources")
        cols = st.columns(len(resp["sources"]))
        for col, src, score in zip(cols, resp["sources"], resp["scores"]):
            col.metric(src, f"{int(score * 100)}% match")

# ── PLAN & TESTS ───────────────────────────────────────────
elif page == "📋 Plan & Tests":
    st.title("📋 Requirement → Plan + Test Cases")
    st.caption("Describe what you want to build — get an implementation plan and test skeletons")

    examples = [
        "Add a phone number validation when creating a new owner",
        "Add an endpoint to get all pets by their type",
        "Add a method to calculate total number of visits for a pet",
        "Add email field to Owner and validate format on save",
    ]

    st.subheader("💡 Example requirements")
    cols = st.columns(2)
    for i, ex in enumerate(examples):
        if cols[i % 2].button(ex, use_container_width=True, key=f"ex_{i}"):
            st.session_state["requirement"] = ex

    st.divider()

    requirement = st.text_area(
        "Your requirement",
        value=st.session_state.get("requirement", ""),
        height=100,
        placeholder="Describe what needs to be built or changed..."
    )

    col1, col2 = st.columns(2)
    top_k       = col1.slider("Classes to search", 3, 8, 5)
    gen_tests   = col2.checkbox("Generate test cases", value=True)

    if st.button("🚀 Generate Plan", type="primary") and requirement:
        with st.spinner("🔍 Searching wiki... 🤖 Generating plan..."):
            resp = safe_post("/plan/", {"requirement": requirement, "top_k": top_k, "generate_tests": gen_tests}, default={"relevant_classes": [], "plan": "", "token_usage": {}})

        if "error" in resp:
            st.error(resp["error"])
            st.stop()

        # Relevant classes
        st.subheader("📦 Relevant Classes Found")
        for cls in resp["relevant_classes"]:
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.markdown(f"**{cls['name']}**")
            col2.caption(f"`{cls['type']}`")
            col3.progress(int(cls["score"] * 100),
                          text=f"{int(cls['score']*100)}%")

        st.divider()

        # Implementation plan
        st.subheader("🗺️ Implementation Plan")
        st.markdown(resp["plan"])

        # Token usage
        usage = resp.get("token_usage", {})
        plan_t = usage.get("plan", {}).get("total", 0)
        test_t = usage.get("tests", {}).get("total", 0)
        st.caption(
            f"🪙 Tokens used — Plan: {plan_t:,} | "
            f"Tests: {test_t:,} | "
            f"Total: {plan_t + test_t:,}"
        )

        # Test cases
        if gen_tests and "tests" in resp:
            st.divider()
            st.subheader("🧪 Generated Test Cases")
            st.markdown(resp["tests"])

            # Download button
            st.download_button(
                label="⬇️ Download Test Cases",
                data=resp["tests"],
                file_name=f"tests_{requirement[:30].replace(' ','_')}.md",
                mime="text/markdown"
            )

# ── TOKEN METRICS ──────────────────────────────────────────
elif page == "📊 Token Metrics":
    import pandas as pd
    from pipeline.metrics.token_tracker import load_metrics
    from pipeline.metrics.calculator import (
        calculate_savings, calculate_cost, calculate_roi
    )

    st.title("📊 Token Metrics — DeepWiki vs Raw Codebase")
    st.caption("Proving the value of pre-built knowledge graphs")

    log = load_metrics()
    if not log:
        st.warning("No metrics yet. Run queries in Ask or Plan pages first.")
        st.info("Or run `python run_iteration9.py` to seed demo data.")
        st.stop()

    savings = calculate_savings(log)
    roi     = calculate_roi(log, team_size=5)

    # ── TOP METRICS ────────────────────────────────────────
    st.subheader("📈 Session Summary")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Tokens WITH DeepWiki",
        f"{savings['total_wiki_tokens']:,}",
        delta=None
    )
    col2.metric(
        "Tokens WITHOUT DeepWiki",
        f"{savings['total_raw_tokens']:,}",
        delta=None
    )
    col3.metric(
        "Total Tokens Saved",
        f"{savings['total_saved']:,}",
        delta=f"{savings['pct_saved']}% reduction",
        delta_color="normal"
    )
    col4.metric(
        "Queries Logged",
        savings["queries"]
    )

    st.divider()

    # ── PER QUERY CHART ────────────────────────────────────
    st.subheader("🔍 Per Query: Wiki Tokens vs Raw Tokens")

    df = pd.DataFrame([
        {
            "Query":      e["query"][:35] + "...",
            "With Wiki":  e["wiki_tokens"],
            "Without Wiki": e["raw_tokens"],
            "Saved":      e["saved_tokens"]
        }
        for e in log
    ])

    st.bar_chart(
        df.set_index("Query")[["With Wiki", "Without Wiki"]],
        color=["#2ecc71", "#e74c3c"],
        height=350
    )

    st.divider()

    # ── CUMULATIVE SAVINGS ─────────────────────────────────
    st.subheader("📈 Cumulative Token Savings Over Queries")

    cumulative = []
    running    = 0
    for e in log:
        running += e["saved_tokens"]
        cumulative.append({
            "Query #":         len(cumulative) + 1,
            "Cumulative Saved": running
        })

    df_cum = pd.DataFrame(cumulative).set_index("Query #")
    st.line_chart(df_cum, height=250, color="#2ecc71")

    st.divider()

    # ── COST COMPARISON ────────────────────────────────────
    st.subheader("💰 Cost Comparison")

    providers = {
        "Groq (Llama 70B)":  ("groq",   "#2ecc71"),
        "Claude Sonnet":     ("claude",  "#3498db"),
        "GPT-4o":            ("gpt4o",   "#9b59b6"),
    }

    cols = st.columns(len(providers))
    for col, (label, (key, color)) in zip(cols, providers.items()):
        cost_wiki = calculate_cost(savings["total_wiki_tokens"], key)
        cost_raw  = calculate_cost(savings["total_raw_tokens"],  key)
        saved_usd = cost_raw - cost_wiki

        col.metric(
            label=label,
            value=f"${cost_wiki:.4f} with wiki",
            delta=f"${saved_usd:.4f} saved vs ${cost_raw:.4f}",
            delta_color="normal"
        )

    st.divider()

    # ── ROI PROJECTION ─────────────────────────────────────
    st.subheader("🚀 Annual Team ROI Projection")

    col1, col2 = st.columns(2)
    team_size  = col1.slider("Team size (devs)", 1, 50, 5)
    daily_q    = col2.slider("Queries per dev per day", 5, 100, 20)

    roi = calculate_roi(
        log,
        team_size=team_size,
        queries_per_dev_per_day=daily_q
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Annual Queries",       f"{roi['annual_queries']:,}")
    col2.metric("Annual Tokens Saved",  f"{roi['annual_tokens_saved']:,}")
    col3.metric("Annual Cost Savings",  f"${roi['annual_savings_usd']:,.2f}")

    st.divider()

    # ── QUERY LOG TABLE ────────────────────────────────────
    st.subheader("📋 Query Log")
    df_log = pd.DataFrame([
        {
            "Query":          e["query"][:50],
            "Wiki Tokens":    e["wiki_tokens"],
            "Raw Tokens":     e["raw_tokens"],
            "Saved":          e["saved_tokens"],
            "Reduction":      f"{int(e['saved_tokens']/e['raw_tokens']*100) if e['raw_tokens'] > 0 else 0}%",
            "Time":           e["timestamp"][:16]
        }
        for e in log
    ])
    st.dataframe(df_log, use_container_width=True, hide_index=True)

    # ── DOWNLOAD ───────────────────────────────────────────
    st.download_button(
        "⬇️ Export Metrics CSV",
        data=df_log.to_csv(index=False),
        file_name="deepwiki_metrics.csv",
        mime="text/csv"
    )

# ── LIVE COMPARISON ────────────────────────────────────────
elif page == "⚖️ Live Comparison":
    import pandas as pd

    st.title("⚖️ Live Token Comparison")
    st.caption(
        "Same query. Three Claude keys. Verify each on "
        "console.anthropic.com → Usage."
    )

    # ── SETTINGS ───────────────────────────────────────────
    with st.expander("⚙️ Settings", expanded=True):
        col1, col2, col3 = st.columns(3)

        models_resp = safe_get("/compare/models", default={})
        model_options = {
            v["label"]: k for k, v in models_resp.items()
        }
        selected_label = col1.selectbox("Model", list(model_options.keys()))
        selected_model = model_options[selected_label]

        mode = col2.selectbox(
            "Comparison Mode",
            ["claude", "groq", "all"],
            format_func=lambda x: {
                "claude": "Claude (3 keys)",
                "groq":   "Groq (2 keys)",
                "all":    "All (Claude + Groq)"
            }[x]
        )
        top_k = col3.slider("Classes to retrieve", 2, 6, 4)

    # ── QUERY INPUT ────────────────────────────────────────
    examples = [
        "How does the application manage pet owners?",
        "Which class handles creating a new pet?",
        "How is data persisted in this application?",
        "What REST endpoints exist for vets?",
    ]

    cols = st.columns(2)
    for i, ex in enumerate(examples):
        if cols[i % 2].button(ex, key=f"cmp_{i}", use_container_width=True):
            st.session_state["cmp_query"] = ex

    query = st.text_input(
        "Query:",
        value=st.session_state.get("cmp_query", "")
    )

    if st.button("▶️ Run Comparison", type="primary") and query:

        with st.spinner("Running comparison across all keys..."):
            resp = safe_post("/compare/", {"query": query, "top_k": top_k, "model": selected_model, "mode": mode}, default={"raw": {}, "wiki": {}, "cache": {}, "summary": {}, "groq": {}, "saved_pct": 0})

        st.divider()

        # ── CLAUDE RESULTS ─────────────────────────────────
        if mode in ("claude", "all"):
            claude = resp if mode == "claude" else resp.get("claude", {})
            raw    = claude.get("raw",   {})
            wiki   = claude.get("wiki",  {})
            cache  = claude.get("cache", {})
            summ   = claude.get("summary", {})

            st.subheader(f"🤖 Claude Comparison — {selected_label}")

            # Three columns — one per key
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### 📄 Raw Source")
                st.caption("`ANTHROPIC_RAW_KEY`")
                st.metric("Input",  f"{raw.get('input_tokens',0):,}")
                st.metric("Output", f"{raw.get('output_tokens',0):,}")
                st.metric("Total",  f"{raw.get('total_tokens',0):,}")
                st.metric("Cost",   f"${raw.get('cost',{}).get('total_cost',0):.6f}")
                st.metric("Latency",f"{raw.get('latency_sec',0)}s")
                with st.expander("Answer"):
                    st.write(raw.get("answer", ""))

            with col2:
                st.markdown("#### 📚 Wiki, No Cache")
                st.caption("`ANTHROPIC_WIKI_KEY`")
                st.metric("Input",  f"{wiki.get('input_tokens',0):,}")
                st.metric("Output", f"{wiki.get('output_tokens',0):,}")
                st.metric("Total",  f"{wiki.get('total_tokens',0):,}",
                          delta=f"{summ.get('wiki_vs_raw_saving_pct',0)}% vs raw",
                          delta_color="normal")
                st.metric("Cost",   f"${wiki.get('cost',{}).get('total_cost',0):.6f}")
                st.metric("Latency",f"{wiki.get('latency_sec',0)}s")
                with st.expander("Answer"):
                    st.write(wiki.get("answer", ""))

            with col3:
                st.markdown("#### ⚡ Wiki + Cache")
                st.caption("`ANTHROPIC_CACHE_KEY`")
                st.metric("Input",      f"{cache.get('input_tokens',0):,}")
                st.metric("Cache Created", f"{cache.get('cache_created',0):,}")
                st.metric("Cache Read", f"{cache.get('cache_read',0):,}")
                st.metric("Output",     f"{cache.get('output_tokens',0):,}")
                cost_delta = f"{summ.get('cache_vs_raw_saving_pct',0)}% vs raw"
                st.metric(
                    "Cost",
                    f"${cache.get('cost',{}).get('total_cost',0):.6f}",
                    delta=cost_delta,
                    delta_color="normal"
                )
                is_hit = cache.get("is_cache_hit", False)
                st.success("✅ Cache HIT" if is_hit else "⚠️ Cache MISS (first call)")
                with st.expander("Answer"):
                    st.write(cache.get("answer", ""))

            # Token comparison chart
            st.divider()
            st.subheader("📊 Token Comparison")
            df_tokens = pd.DataFrame({
                "Approach": ["Raw", "Wiki", "Cache"],
                "Input":    [
                    raw.get("input_tokens", 0),
                    wiki.get("input_tokens", 0),
                    cache.get("input_tokens", 0)
                ],
                "Output":   [
                    raw.get("output_tokens", 0),
                    wiki.get("output_tokens", 0),
                    cache.get("output_tokens", 0)
                ]
            }).set_index("Approach")
            st.bar_chart(df_tokens, color=["#3498db", "#2ecc71"], height=280)

            # Cost comparison chart
            st.subheader("💰 Cost Comparison")
            df_cost = pd.DataFrame({
                "Approach": ["Raw", "Wiki", "Cache"],
                "Cost ($)": [
                    raw.get("cost",  {}).get("total_cost", 0),
                    wiki.get("cost", {}).get("total_cost", 0),
                    cache.get("cost",{}).get("total_cost", 0),
                ]
            }).set_index("Approach")
            st.bar_chart(df_cost, color="#e74c3c", height=220)

        # ── GROQ RESULTS ────────────────────────────────────
        if mode in ("groq", "all"):
            groq = resp if mode == "groq" else resp.get("groq", {})
            if groq:
                st.divider()
                st.subheader("⚡ Groq Comparison")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 📄 Groq Raw")
                    st.caption("`GROQ_RAW_KEY`")
                    r = groq.get("raw", {})
                    st.metric("Total Tokens", f"{r.get('total_tokens',0):,}")
                    st.metric("Latency", f"{r.get('latency_sec',0)}s")
                    with st.expander("Answer"):
                        st.write(r.get("answer", ""))

                with col2:
                    st.markdown("#### 📚 Groq DeepWiki")
                    st.caption("`GROQ_DEEPWIKI_KEY`")
                    d = groq.get("deepwiki", {})
                    st.metric(
                        "Total Tokens",
                        f"{d.get('total_tokens',0):,}",
                        delta=f"{groq.get('saved_pct',0)}% saved",
                        delta_color="normal"
                    )
                    st.metric("Latency", f"{d.get('latency_sec',0)}s")
                    with st.expander("Answer"):
                        st.write(d.get("answer", ""))

        # ── DASHBOARD VERIFICATION ─────────────────────────
        st.divider()
        with st.expander("🔍 Verify on Anthropic Dashboard"):
            raw_t   = resp.get("raw",  {}).get("total_tokens", 0) if mode == "claude" else 0
            wiki_t  = resp.get("wiki", {}).get("total_tokens", 0) if mode == "claude" else 0
            cache_t = resp.get("cache",{}).get("total_tokens", 0) if mode == "claude" else 0
            cache_r = resp.get("cache",{}).get("cache_read", 0)   if mode == "claude" else 0

            st.markdown(f"""
**Go to:** `console.anthropic.com` → **Usage** → **API Keys**

You will see 3 separate rows:

| Key | Tokens | What to look for |
|-----|--------|-----------------|
| `deepwiki-raw`   | ~{raw_t:,}  | Highest — full source files |
| `deepwiki-wiki`  | ~{wiki_t:,} | Lower — wiki summaries only |
| `deepwiki-cache` | ~{cache_t:,} | Lowest effective cost — `cache_read_input_tokens: {cache_r:,}` |

**Cache read tokens** cost **10% of normal input price**.  
Run the same query again — `deepwiki-cache` row stays flat 
while answer quality remains identical.
            """)

    # ── HISTORY TABLE ──────────────────────────────────────
    st.divider()
    st.subheader("📋 Query History")
    history = safe_get("/compare/history", default=[])

    if history:
        rows = []
        for h in history:
            if "summary" in h:
                rows.append({
                    "Query":       h["query"][:40],
                    "Model":       h.get("model", ""),
                    "Raw Tokens":  h["summary"].get("raw_tokens", 0),
                    "Wiki Tokens": h["summary"].get("wiki_tokens", 0),
                    "Cache Tokens":h["summary"].get("cache_tokens", 0),
                    "Wiki Saving": f"{h['summary'].get('wiki_vs_raw_saving_pct',0)}%",
                    "Cache Saving":f"{h['summary'].get('cache_vs_raw_saving_pct',0)}%",
                })

        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

        if st.button("🗑️ Clear History"):
            requests.delete(f"{API}/compare/history")
            st.rerun()