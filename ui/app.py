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
_API_BASE = st.secrets.get("API_URL", "http://localhost:8000").rstrip("/")

def api(path: str) -> str:
    """Always produces clean URL regardless of slashes."""
    return f"{_API_BASE}/{path.lstrip('/')}"


def safe_get(path: str, default=None):
    # Ensure single slash between base and path
    url = api(path)

    """GET request with error handling."""
    try:
        resp = requests.get(url, timeout=30)
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


def safe_post(path: str, payload: dict, default=None):
    # Ensure single slash between base and path
    url = api(path)
    """POST request with error handling."""
    try:
        resp = requests.post(
            url,
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

def safe_delete(path: str):
    try:
        requests.delete(api(path), timeout=10)
    except Exception:
        pass
    except requests.exceptions.ConnectionError:
        st.error("❌ API not running. Start with: `uvicorn api.main:app --reload --port 8000`")
        return False
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. LLM may be slow — try again.")
        return False
    except Exception as e:
        st.error(f"❌ Request failed: {e}")
        return False
    return True

# ── PAGE CONFIG ────────────────────────────────────────────
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
        "🏛️ Suite Overview",
        "🔍 Class Explorer",
        "🔎 Semantic Search",
        "💬 Ask DeepWiki",
        "🔀 Flow Tracer",
        "📋 Plan & Tests",
        "📊 Token Metrics",
        "⚖️ Live Comparison",
        "📡 API Catalog",
        "📚 Knowledge Sources",
    ]
)

st.sidebar.divider()

# ── Suite selector ─────────────────────────────────────────
suites_data = safe_get("/suite", default={"suites": []})
suite_list  = suites_data.get("suites", []) if suites_data else []
suite_names = [s["name"] for s in suite_list] if suite_list else ["Pet Management Platform"]
suite_ids   = [s["id"]   for s in suite_list] if suite_list else ["pet-management-platform"]

selected_suite_name = st.sidebar.selectbox("Suite", suite_names, key="suite_selector")
selected_suite_idx  = suite_names.index(selected_suite_name) if selected_suite_name in suite_names else 0
selected_suite_id   = suite_ids[selected_suite_idx]
st.session_state["active_suite_id"] = selected_suite_id

st.sidebar.divider()
try:
    health = safe_get("/health")
    if health:
        st.sidebar.success("✅ API connected")
    else:
        st.sidebar.error("❌ API offline")
        st.sidebar.code("uvicorn api.main:app --reload --port 8000")
except Exception:
    st.sidebar.error("❌ API offline")
    st.sidebar.code("uvicorn api.main:app --reload --port 8000")
st.sidebar.caption(f"{selected_suite_name} · Local POC")

# ── OVERVIEW ──────────────────────────────────────────────
if page == "🏠 Overview":
    st.title("📚 DeepWiki — Codebase Knowledge Graph")

    # Stats
    try:
        # stats = requests.get(f"{API}/stats").json()s
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


# ── SUITE OVERVIEW ─────────────────────────────────────────
elif page == "🏛️ Suite Overview":
    suite_id = st.session_state.get("active_suite_id", "pet-management-platform")
    suite    = safe_get(f"/suite/{suite_id}", default=None)

    if not suite:
        st.title("🏛️ Suite Overview")
        st.info(
            "No suite data found. Run `python run_iteration17.py` to bootstrap suites, "
            "or start Neo4j and call `POST /suite/bootstrap`."
        )
        st.stop()

    st.title(f"🏛️ {suite['name']}")
    st.caption(suite.get("description", ""))

    coverage = suite.get("coverage", {})
    total    = coverage.get("total_classes", 0)
    with_wiki = coverage.get("wiki_coverage", 0)
    cov_pct  = coverage.get("coverage_pct", 0)

    repos    = suite.get("repos", [])
    total_apis = sum(r.get("api_count", 0) for r in repos)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Repositories",    len(repos))
    col2.metric("API Endpoints",   total_apis)
    col3.metric("Classes",         total)
    col4.metric("Wiki Coverage",   f"{cov_pct}%",
                delta=f"{with_wiki}/{total} classes documented")

    st.divider()

    # Repository cards
    st.subheader("Repositories in Suite")
    for repo in repos:
        lang_badge = {"java": "☕ Java", "typescript": "🔷 TypeScript"}.get(
            repo.get("language", ""), repo.get("language", "?")
        )
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.markdown(f"**{repo['name']}**  \n`{repo['id']}`")
            col2.caption(lang_badge)
            col3.metric("Endpoints", repo.get("api_count", 0))

    st.divider()

    # Suite-level Ask
    st.subheader("💬 Ask Across Suite")
    suite_q = st.text_input(
        "Question (searches all repos in suite)",
        placeholder="How does owner creation work across services?"
    )
    if st.button("Ask Suite", type="primary") and suite_q:
        with st.spinner("Searching across suite..."):
            resp = safe_post("/ask", {
                "question": suite_q,
                "top_k":    6,
                "scope":    "suite",
                "suite_id": suite_id,
            }, default={"answer": "", "sources": [], "scores": []})
        if resp:
            st.success(resp.get("answer", "No answer."))
            sources = resp.get("sources", [])
            if sources:
                st.caption("Sources: " + ", ".join(f"`{s}`" for s in sources))
            st.caption(f"Intent: `{resp.get('intent', '?')}` · "
                       f"Tokens: {resp.get('token_count', 0)}")


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
    st.caption("Search classes and methods by meaning, not just keywords")

    query = st.text_input("Search query",
                          placeholder="Find methods that validate email")

    col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
    top_k      = col1.slider("Results", 1, 10, 5)
    unit_type  = col2.selectbox("Unit type",
                                ["Both", "Classes only", "Methods only"],
                                help="Filter by class or method")
    scope      = col3.selectbox("Scope",
                                ["repo", "suite", "cross_suite"],
                                format_func=lambda x: {
                                    "repo": "This repo",
                                    "suite": "Whole suite",
                                    "cross_suite": "All repos",
                                }[x])
    types_list = ["All", "REST_CONTROLLER", "SERVICE",
                  "REPOSITORY", "ENTITY", "COMPONENT"]
    filter_type = col4.selectbox("Class type filter", types_list)

    suite_id = st.session_state.get("active_suite_id", "pet-management-platform")

    if query:
        unit_type_param = None
        if unit_type == "Classes only":
            unit_type_param = "class"
        elif unit_type == "Methods only":
            unit_type_param = "method"

        payload = {
            "query":          query,
            "top_k":          top_k,
            "component_type": None if filter_type == "All" else filter_type,
            "unit_type":      unit_type_param,
            "scope":          scope,
            "suite_id":       suite_id,
        }
        resp = safe_post("/search", payload, default={"results": [], "count": 0})

        st.divider()
        st.subheader(f"Results for: *{query}*")
        st.caption(f"{resp.get('count', 0)} results · scope: `{scope}`")

        for i, r in enumerate(resp.get("results", []), 1):
            score_pct = int(r["score"] * 100)
            rtype     = r.get("unit_type", "class")

            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                if rtype == "method":
                    col1.markdown(
                        f"**{i}. `{r['class_name']}.{r['name']}()`**"
                    )
                    col2.caption("method")
                    col3.progress(score_pct, text=f"{score_pct}%")
                    if r.get("logic_summary"):
                        st.caption(r["logic_summary"])
                else:
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

    col_scope, col_topk = st.columns([2, 1])
    ask_scope  = col_scope.selectbox("Search scope", ["repo", "suite", "cross_suite"],
                                     format_func=lambda x: {
                                         "repo": "This repo",
                                         "suite": "Whole suite",
                                         "cross_suite": "All repos",
                                     }[x], key="ask_scope")
    ask_top_k  = col_topk.slider("Sources", 2, 6, 4, key="ask_top_k")
    suite_id   = st.session_state.get("active_suite_id", "pet-management-platform")

    if st.button("🔍 Ask", type="primary") and question:
        with st.spinner("Searching wiki and generating answer..."):
            resp = safe_post("/ask", {
                "question": question,
                "top_k":    ask_top_k,
                "scope":    ask_scope,
                "suite_id": suite_id,
            }, default={"answer": "", "sources": [], "scores": []})

        st.subheader("💡 Answer")
        st.success(resp.get("answer", ""))

        # ── Metadata row ───────────────────────────────────
        intent     = resp.get("intent", "")
        model_used = resp.get("model_used", "")
        query_id   = resp.get("query_id", "")
        token_count = resp.get("token_count", 0)
        if intent:
            st.caption(
                f"Intent: `{intent}` · Model: `{model_used}` · Tokens: {token_count}"
            )

        # ── Thumbs feedback ─────────────────────────────────
        if query_id:
            st.markdown("**Was this helpful?**")
            t1, t2, _ = st.columns([1, 1, 8])
            if t1.button("👍", key=f"up_{query_id}"):
                result = safe_post("/feedback", {"query_id": query_id, "thumbs_up": True})
                if result and result.get("ok"):
                    st.toast("Thanks! Feedback recorded.")
            if t2.button("👎", key=f"dn_{query_id}"):
                result = safe_post("/feedback", {"query_id": query_id, "thumbs_up": False})
                if result and result.get("ok"):
                    st.toast("Feedback recorded — we'll improve.")

        sources = resp.get("sources", [])
        scores  = resp.get("scores", [])
        if sources:
            st.subheader("📎 Sources")
            cols = st.columns(min(len(sources), 4))
            for col, src, score in zip(cols, sources, scores):
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
            resp = safe_post("/plan", {"requirement": requirement, "top_k": top_k, "generate_tests": gen_tests}, default={"relevant_classes": [], "plan": "", "token_usage": {}})

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
            resp = safe_post("/compare", {"query": query, "top_k": top_k, "model": selected_model, "mode": mode}, default={"raw": {}, "wiki": {}, "cache": {}, "summary": {}, "groq": {}, "saved_pct": 0})

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
            safe_delete("/compare/history")
            st.success("History cleared")
            st.rerun()

# ── FLOW TRACER ────────────────────────────────────────────
elif page == "🔀 Flow Tracer":
    st.title("🔀 Flow Viewer")
    st.caption(
        "End-to-end execution trace — Angular frontend → API Contract → Spring Boot → Database"
    )

    # ── Layer color + repo label config ────────────────────
    LAYER_COLOR = {
        "Angular": "#9b59b6",
        "API":     "#1abc9c",
        "HTTP":    "#3498db",
        "Service": "#2ecc71",
        "Data":    "#e67e22",
        "Config":  "#95a5a6",
        "Code":    "#7f8c8d",
    }
    REPO_LABEL = {
        "frontend": "Angular FE",
        "backend":  "Spring Boot",
        "contract": "API Contract",
        None:       "",
    }

    # ── Example buttons ─────────────────────────────────────
    EXAMPLES = [
        "createOwner",
        "processCreationForm",
        "getPets",
        "findOwner",
    ]
    st.markdown("**Quick examples:**")
    cols = st.columns(4)
    for i, ex in enumerate(EXAMPLES):
        if cols[i].button(ex, use_container_width=True, key=f"flow_ex_{i}"):
            st.session_state["flow_entry"] = ex

    st.divider()

    # ── Input row ───────────────────────────────────────────
    c1, c2, c3 = st.columns([3, 1, 1])
    entry    = c1.text_input(
        "Entry point (class name, method name, or keyword)",
        value=st.session_state.get("flow_entry", ""),
        placeholder="createOwner  or  PetService  or  owner creation",
    )
    max_hops = c2.slider("Max hops", 2, 10, 8)
    mode     = c3.selectbox("Mode", ["auto", "cross_repo", "be_only"], index=0)

    if st.button("🔍 Trace Flow", type="primary") and entry:
        payload = {
            "entry_point": entry,
            "max_hops":    max_hops,
        }

        with st.spinner("Tracing end-to-end flow..."):
            flow = safe_post("/flow", payload, default={})

        steps      = flow.get("steps", [])
        trace_mode = flow.get("trace_mode", "none")

        if not steps:
            st.warning(
                f"No flow found for **{entry}**.\n\n"
                "- For cross-repo traces: run Iteration 19 to populate CONSUMES edges\n"
                "- For BE-only traces: run Iteration 14 to populate CALLS edges"
            )
        else:
            # ── Path breadcrumb ─────────────────────────────
            layers_seen = list(dict.fromkeys(s["layer"] for s in steps))
            breadcrumb  = " → ".join(layers_seen)
            mode_label  = "🔗 Cross-Repo (FE→BE)" if trace_mode == "cross_repo" else "⚙️ Backend-Only"
            st.markdown(
                f"<div style='padding:10px 14px;background:#1e2a38;"
                f"border-radius:8px;margin-bottom:16px'>"
                f"<span style='color:#7ec8e3;font-size:0.85rem'>{mode_label}</span>"
                f"&nbsp;&nbsp;·&nbsp;&nbsp;"
                f"<span style='color:#b0d4ee;font-weight:500'>{breadcrumb}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # ── Step cards ──────────────────────────────────
            prev_repo_type = None
            for step in steps:
                layer     = step.get("layer", "Code")
                repo_type = step.get("repo_type")
                repo_id   = step.get("repo_id") or ""
                color     = LAYER_COLOR.get(layer, "#7f8c8d")

                # Repo boundary separator
                if repo_type != prev_repo_type and prev_repo_type is not None:
                    repo_lbl = REPO_LABEL.get(repo_type, repo_type or "")
                    st.markdown(
                        f"<div style='text-align:center;margin:4px 0;"
                        f"color:#507898;font-size:0.8rem'>▼ {repo_lbl}</div>",
                        unsafe_allow_html=True,
                    )
                prev_repo_type = repo_type

                layer_badge = (
                    f"<span style='background:{color};color:white;"
                    f"padding:2px 8px;border-radius:4px;font-size:0.78em;"
                    f"font-weight:bold'>{layer}</span>"
                )
                repo_badge = (
                    f"<span style='background:#1a3a5c;color:#7ec8e3;"
                    f"padding:2px 7px;border-radius:10px;font-size:0.72em;"
                    f"margin-left:6px'>{repo_id}</span>"
                    if repo_id else ""
                )

                with st.container():
                    st.markdown(
                        f"{layer_badge}{repo_badge} "
                        f"**Step {step['step']}: "
                        f"`{step['class_name']}.{step['method_name']}()`**",
                        unsafe_allow_html=True,
                    )
                    logic = step.get("logic_summary", "")
                    if logic:
                        st.caption(logic)
                    else:
                        st.caption("_No logic summary yet — run Iterations 14–16 to populate_")
                    st.divider()

            # ── LLM Explanation ─────────────────────────────
            st.subheader("💬 Explanation")
            explanation = flow.get("explanation", "")
            if explanation:
                st.success(explanation)

            # ── Token metrics ────────────────────────────────
            token_count  = flow.get("token_count", 0)
            raw_estimate = flow.get("raw_token_estimate", 0)

            st.subheader("📊 Token Usage")
            mcol1, mcol2, mcol3 = st.columns(3)
            mcol1.metric("DeepWiki tokens", f"{token_count:,}", help="Tokens used for this answer")
            mcol2.metric("Raw approach", f"{raw_estimate:,}", help="Estimated tokens to load all source files")
            if raw_estimate > 0:
                savings_pct = round((1 - token_count / raw_estimate) * 100)
                mcol3.metric("Savings", f"{savings_pct}%", delta=f"-{raw_estimate - token_count:,} tokens")

            if token_count > 0:
                st.progress(
                    min(token_count / 600, 1.0),
                    text=f"Context budget: {token_count} / 600 tokens used"
                )


# ── API CATALOG ────────────────────────────────────────────
elif page == "📡 API Catalog":
    import pandas as pd

    st.title("📡 API Catalog")
    st.caption("All HTTP endpoints exposed and consumed by this repository")

    repo_id = st.sidebar.text_input("Repository ID", value="spring-petclinic")

    # ── EXPOSED ENDPOINTS ──────────────────────────────────
    st.subheader("Endpoints Exposed")
    data = safe_get(f"/contracts?repo_id={repo_id}", default={"contracts": [], "count": 0})
    contracts = data.get("contracts", [])

    if contracts:
        st.caption(f"{data['count']} endpoints found")

        METHOD_COLORS = {
            "GET":    "#2ecc71",
            "POST":   "#3498db",
            "PUT":    "#e67e22",
            "DELETE": "#e74c3c",
            "PATCH":  "#9b59b6",
        }

        for c in contracts:
            method      = c.get("http_method", "")
            color       = METHOD_COLORS.get(method, "#95a5a6")
            contract_id = c.get("id", "")
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                col1.markdown(
                    f"<span style='background:{color};color:white;"
                    f"padding:2px 8px;border-radius:4px;font-weight:bold'>"
                    f"{method}</span>",
                    unsafe_allow_html=True,
                )
                col2.code(c.get("path", ""), language=None)
                col3.caption(c.get("controller_class", ""))
                col4.caption(c.get("controller_method", ""))

            # ── Consumed-by badge (Iteration 19) ────────────
            if contract_id:
                consumers_data = safe_get(
                    f"/contracts/{contract_id}/consumers",
                    default={"consumers": [], "count": 0}
                )
                consumers = (consumers_data or {}).get("consumers", [])
                if consumers:
                    badges = " ".join(
                        f"<span style='background:#1a3a5c;color:#7ec8e3;"
                        f"padding:1px 7px;border-radius:10px;font-size:0.72rem;"
                        f"margin-right:4px'>"
                        f"{con['caller_class']}.{con['caller_method']}() "
                        f"[{int(con.get('confidence', 0) * 100)}%]</span>"
                        for con in consumers
                    )
                    st.markdown(
                        f"<div style='margin:-4px 0 8px 0;padding-left:4px'>"
                        f"<span style='color:#507898;font-size:0.75rem'>Consumed by:</span> "
                        f"{badges}</div>",
                        unsafe_allow_html=True,
                    )

        st.divider()

        # Downloadable table
        df = pd.DataFrame([
            {
                "Method":       c.get("http_method", ""),
                "Path":         c.get("path", ""),
                "Controller":   c.get("controller_class", ""),
                "Action":       c.get("controller_method", ""),
                "Returns":      c.get("return_type", ""),
                "Request Body": c.get("request_body_type") or "—",
            }
            for c in contracts
        ])
        with st.expander("View as table"):
            st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Export CSV",
            data=df.to_csv(index=False),
            file_name=f"{repo_id}_api_catalog.csv",
            mime="text/csv",
        )
    else:
        st.info(
            "No API contracts found. Run `python run_iteration15.py` to extract endpoints."
        )

    # ── CONSUMED ENDPOINTS ─────────────────────────────────
    st.subheader("Endpoints Consumed")
    consumed = safe_get(
        f"/contracts/consumers?repo_id={repo_id}",
        default={"consumed": [], "count": 0}
    )
    consumed_list = consumed.get("consumed", [])

    if consumed_list:
        st.caption(f"{consumed['count']} consumed endpoints")
        df_c = pd.DataFrame([
            {
                "Method":      c.get("http_method", ""),
                "Path":        c.get("path", ""),
                "Provider":    c.get("controller_class", ""),
                "Caller":      c.get("caller_class", ""),
                "Confidence":  f"{int(c.get('confidence', 0) * 100)}%",
            }
            for c in consumed_list
        ])
        st.dataframe(df_c, use_container_width=True, hide_index=True)
    else:
        st.info("No consumed endpoints yet. Angular analysis (Iteration 18) will populate this.")
# ── KNOWLEDGE SOURCES ──────────────────────────────────────
elif page == "📚 Knowledge Sources":
    st.title("📚 Knowledge Sources — Confluence Integration")
    st.caption("Submit Confluence pages to ground DeepWiki answers in design decisions and meeting notes.")

    # ── Submit form ────────────────────────────────────────
    with st.expander("Submit a Confluence page", expanded=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            conf_url = st.text_input(
                "Confluence page URL or ID",
                placeholder="https://your-org.atlassian.net/wiki/spaces/ENG/pages/123456/Auth+Design",
            )
        with col2:
            conf_category = st.selectbox(
                "Category",
                ["current", "historical", "upcoming", "update"],
                help="current = active design; historical = past decisions; upcoming = planned; update = changelog",
            )

        module_input = st.text_input(
            "Module tags (comma-separated)",
            placeholder="owner-module, auth-module",
            help="Module IDs this page documents — used for alignment scoring",
        )
        module_tags = [t.strip() for t in module_input.split(",") if t.strip()]

        suite_id_input = st.text_input("Suite ID (optional)", value=selected_suite_id)

        if st.button("Ingest page", type="primary", disabled=not conf_url):
            with st.spinner("Fetching, classifying, embedding..."):
                result = safe_post("/confluence/ingest", {
                    "url":         conf_url,
                    "category":    conf_category,
                    "module_tags": module_tags,
                    "suite_id":    suite_id_input,
                })
            if result and result.get("ok"):
                r = result["result"]
                st.success(f"Ingested: **{r.get('title', '?')}**")
                cols = st.columns(3)
                cols[0].metric("Content type", r.get("content_type", "?"))
                cols[1].metric("Collection",   r.get("collection") or "vault (not stored)")
                cols[2].metric("Flags raised",  len(r.get("flags", [])))
                if r.get("alignment"):
                    st.markdown("**Alignment scores:**")
                    for mod, score in r["alignment"].items():
                        colour = "normal" if score >= 0 else "inverse"
                        st.metric(mod, f"{score:+.3f}", delta_color=colour)
                if r.get("flags"):
                    st.warning(f"ContradictionFlags raised: {r['flags']}")

    st.divider()

    # ── Ingested pages table ────────────────────────────────
    st.subheader("Ingested pages")
    pages_data = safe_get("/confluence/pages", default={"pages": [], "count": 0})
    pages_list = pages_data.get("pages", []) if pages_data else []

    if pages_list:
        st.caption(f"{pages_data.get('count', 0)} page(s) in knowledge graph")
        for p in pages_list:
            badge = {
                "meeting_notes": "Meeting Notes",
                "api_docs":      "API Docs",
                "architecture":  "Architecture",
                "user_flows":    "User Flows",
                "general":       "General",
                "server_db":     "Vault Only",
            }.get(p.get("content_type", ""), p.get("content_type", "?"))

            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    url = p.get("page_url", "")
                    title = p.get("title", "Untitled")
                    if url:
                        st.markdown(f"**[{title}]({url})**")
                    else:
                        st.markdown(f"**{title}**")
                    if p.get("modules"):
                        for m in p["modules"]:
                            score = m.get("score", 0) or 0
                            colour = ":green[+]" if score >= 0 else ":red[-]"
                            st.caption(f"Module: {m.get('module_id', '?')}  alignment {colour}{abs(score):.3f}")
                with c2:
                    st.caption(badge)
                    st.caption(p.get("category", ""))
                with c3:
                    st.caption(f"ID: {p.get('page_id', '?')}")
    else:
        st.info("No Confluence pages ingested yet. Submit one above.")

    st.divider()

    # ── Contradiction flags ─────────────────────────────────
    st.subheader("Contradiction Flags")
    flags_data = safe_get("/confluence/flags", default={"flags": [], "count": 0})
    flags_list = flags_data.get("flags", []) if flags_data else []

    if flags_list:
        st.warning(f"{len(flags_list)} unresolved contradiction(s) detected.")
        for f in flags_list:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    url = f.get("page_url", "")
                    title = f.get("page_title", f.get("page_id", "?"))
                    if url:
                        st.markdown(f"[{title}]({url})")
                    else:
                        st.markdown(title)
                    st.caption(f"Module: {f.get('module_id', '?')}  |  alignment: {f.get('alignment_score', 0):.3f}")
                with c2:
                    severity = f.get("severity", "MEDIUM")
                    if severity == "HIGH":
                        st.error(severity)
                    else:
                        st.warning(severity)
                with c3:
                    if st.button("Resolve", key=f"resolve_{f['flag_id']}"):
                        safe_post(f"/confluence/flags/{f['flag_id']}/resolve", {})
                        st.rerun()
    else:
        st.success("No open contradiction flags.")
