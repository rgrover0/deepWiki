# DeepWiki — Architecture & Build Instructions
> Like IKEA furniture: read the full guide before touching a screw.  
> Version 3.0 · May 2026 · Rohit Grover

---

## 📦 What You Are Building

**DeepWiki** — A Codebase Intelligence Platform.

It reads your code, builds a knowledge graph, generates wiki summaries, and serves pre-built context to developers — reducing AI token usage by 87%+ and preserving institutional memory.

```
WITHOUT DeepWiki:  question → load raw files → 15,000 tokens → slow + expensive
WITH    DeepWiki:  question → pre-built wiki  →    600 tokens → fast + cheap
```

---

## 🗂️ Table of Contents

1. [Parts List](#1-parts-list)
2. [Tools Required](#2-tools-required)
3. [What Is Already Built](#3-what-is-already-built)
4. [How the Parts Connect](#4-how-the-parts-connect)
5. [Data Schema](#5-data-schema)
6. [Provider Adapters](#6-provider-adapters)
7. [Assembly Instructions — Phase 1](#7-phase-1-java-foundation)
8. [Assembly Instructions — Phase 2](#8-phase-2-angular--flow-tracing)
9. [Assembly Instructions — Phase 3](#9-phase-3-copilot--knowledge)
10. [Extension Modules](#10-extension-modules-add-later)
11. [What Good Looks Like](#11-definition-of-done-per-phase)
12. [⛔ Do Not Build](#12-do-not-build)
13. [✅ Decisions Already Made](#13-decisions-already-made-do-not-revisit)

---

## 1. Parts List

### 1A — Core Parts (Must Build)

| Part | What It Does | Built When |
|---|---|---|
| `VCSAdapter` | Reads repos (GitHub / Bitbucket) without touching raw code | Phase 1 |
| `code-analysis-service` | JavaParser Spring Boot microservice — extracts classes, methods, CALLS edges | Phase 1 |
| `wiki-pipeline` | LangGraph — LLM generates wiki summaries per class and method | Phase 1 |
| `Neo4j schema` | Knowledge graph — full hierarchy + method linkage | Phase 1 |
| `Qdrant collections` | 8 fixed collections with payload filter — NOT per-repo | Phase 1 |
| `FastAPI query-api` | Intent → graph → vector → LLM → answer | Phase 1 |
| `Streamlit portal` | Developer-facing web UI | Phase 1 |
| `APIContract nodes` | Extracted from @GetMapping etc. — bridge between FE and BE | Phase 1 |
| `ts-analysis-service` | ts-morph Node.js microservice — Angular analysis | Phase 2 |
| `flow-tracer` | Follows CALLS edges graph traversal — method-level flow | Phase 2 |
| `MCP server` | 5 tools for GitHub Copilot @deepwiki | Phase 3 |
| `Confluence ingestion` | Atlassian MCP → typed collections | Phase 3 |

### 1B — Extension Parts (Add Later, Architecture Ready)

| Part | Add When |
|---|---|
| Android Kotlin parser | Extension |
| iOS Swift parser | Extension |
| Video transcript RAG | Extension |
| Architecture diagram Vision extraction | Extension |
| Cross-suite impact dashboard | Extension |
| Slack notifications | Extension |
| VS Code extension | Extension |
| IntelliJ plugin | Extension |

---

## 2. Tools Required

### Runtime Stack

```
Java 17+            → JavaParser code-analysis-service
Node.js 20+         → ts-morph TypeScript analysis
Python 3.11+        → LangGraph, FastAPI, Streamlit, embeddings

Neo4j 5.x           → Knowledge graph (demo: AuraDB free tier)
Qdrant              → Vector store (demo: Qdrant Cloud free tier)

Groq API            → Fast LLM for bulk wiki generation
Anthropic Claude    → Quality LLM for synthesis and analysis
AWS Bedrock         → LLM for org environment (same Claude, IAM auth)
```

### Environment Variables (Two Configs)

```env
# .env.demo — for development and demo
VCS_PROVIDER=github
LLM_PROVIDER=groq
GRAPH_DB=neo4j
VECTOR_DB=qdrant
AGENT_RUNTIME=langgraph

GITHUB_APP_ID=
GROQ_API_KEY=
ANTHROPIC_API_KEY=
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_PASSWORD=
QDRANT_URL=https://xxx.cloud.qdrant.io
QDRANT_API_KEY=
HF_TOKEN=                        # HuggingFace, for cloud embedding fallback
USE_LOCAL_EMBEDDINGS=false

# .env.org — for organization (AWS stack)
VCS_PROVIDER=bitbucket
LLM_PROVIDER=bedrock
GRAPH_DB=neptune
VECTOR_DB=opensearch
AGENT_RUNTIME=agentcore

BITBUCKET_WORKSPACE=
BITBUCKET_USER=svc-deepwiki
BITBUCKET_APP_PASSWORD=
AWS_REGION=us-east-1
NEPTUNE_ENDPOINT=
OPENSEARCH_ENDPOINT=
# No LLM keys needed — IAM role authenticates to Bedrock
```

⚠️ **Switching environments = changing .env file only. Zero code change.**

---

## 3. What Is Already Built

> Iterations 1–11 complete. Do not rebuild these.

```
✅ Git reader + javalang static analysis (Spring PetClinic)
✅ Neo4j basic schema (Class, Method, Field, Package nodes)
✅ Qdrant embeddings (all-MiniLM-L6-v2, class-level)
✅ Wiki generation via Groq Llama 70B
✅ FastAPI REST API (6 routes)
✅ Streamlit portal (6 pages)
✅ Delta pipeline (LangGraph, webhook-triggered)
✅ Token comparison (3-key demo: raw vs wiki vs cache)
✅ Cloud deployment:
     Neo4j  → AuraDB (free tier, always on)
     Qdrant → Qdrant Cloud (free tier, always on)
     API    → Railway ($5/month, no cold start)
     UI     → Streamlit Community Cloud (free, password gated)
```

---

## 4. How the Parts Connect

```
REPOS                   VCS ADAPTER              SCAN ENGINE
(GitHub/Bitbucket) ──▶  (one interface,   ──▶   Sparse clone (initial)
                          many providers)         API fetch (delta)
                                │                 In-memory parse
                                ▼                 WIPE immediately
                    Language-Agnostic JSON
                    { name, methods, fields,
                      annotations, calls[] }
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
        code-analysis     ts-analysis       swift-analysis
          (JavaParser,     (ts-morph,       (SourceKitten,
           Java svc)       Node.js svc)      Python bridge)
               │                │                │
               └────────────────┴────────────────┘
                                │
                        INTELLIGENCE PIPELINE
                        (Python · LangGraph)
                   ┌────────────────────────────┐
                   │ LLM annotation extraction  │
                   │ + semantic cache           │
                   │ Module auto-detection      │
                   │ Owner detection            │
                   │ APIContract extraction     │
                   │ logic_summary per method   │
                   │ Wiki generation            │
                   └────────────────────────────┘
                          │           │
                    ┌─────┘           └──────┐
                    ▼                        ▼
                 NEO4J                   QDRANT
              (graph store)          (vector store)
              8 collections,
              payload filter
                    │                        │
                    └─────────┬──────────────┘
                              ▼
                       QUERY API (FastAPI)
                  Intent → Graph → Vector → LLM
                       600-token ceiling
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         Streamlit       Copilot MCP      VS Code ext
          Portal          @deepwiki        (future)
```

---

## 5. Data Schema

### 5A — Neo4j Node Hierarchy

```
Organization
  └── ApplicationSuite        { id, name, repo_ids[] }
        └── Repository        { id, name, repo_url, language, framework, suite_id }
              └── Module      { id, name, domain, coverage_score }
                    └── Package { name, module_id }
                          └── Class { name, component_type, wiki_summary,
                                       updated_at, human_confirmed }
                                ├── Method { name, return_type, params[],
                                │            annotations[], logic_summary,
                                │            throws[], reads_fields[],
                                │            writes_fields[], lines_of_code }
                                └── Field  { name, type, annotations[] }
```

### 5B — Key Neo4j Relationships

```cypher
# Structural (always created automatically)
(Suite)   -[:HAS_REPO]          ->(Repository)
(Module)  -[:HAS_PACKAGE]       ->(Package)
(Package) -[:BELONGS_TO]        ->(Module)          ← explicit, bidirectional
(Package) -[:CONTAINS_CLASS]    ->(Class)
(Class)   -[:HAS_METHOD]        ->(Method)
(Class)   -[:HAS_FIELD]         ->(Field)
(Class)   -[:IN_MODULE]         ->(Module)          ← derived, for fast queries
(Class)   -[:EXTENDS]           ->(Class)
(Class)   -[:IMPLEMENTS_INTERFACE]->(Interface)

# THE key new relationship — powers flow tracing
(Method)  -[:CALLS { call_site_line, confidence }]->(Method)
(Method)  -[:READS  { line }]   ->(Field)
(Method)  -[:WRITES { line }]   ->(Field)

# API catalog — bridge between FE and BE
(Repo)    -[:EXPOSES { controller, since_commit }]  ->(APIContract)
(Repo)    -[:CONSUMES { caller_class, confidence }] ->(APIContract)

# Pre-computed (never traverse at query time)
(APIContract)-[:HAS_IMPACT]->(APIContractImpact)    ← nightly batch

# Knowledge sources (human-curated)
(ConfluencePage)-[:DOCUMENTS { alignment_score, category }]->(Module)
(Module)        -[:HAS_DECISION]->(Decision)
```

### 5C — Qdrant Collections (8 Fixed — Never Per-Repo)

```
Collection name                     | Filter keys used at query time
────────────────────────────────────┼───────────────────────────────
deepwiki_code_units                 | repo_id, suite_id, unit_type
deepwiki_api_contracts              | repo_id, method, version
deepwiki_confluence_meeting_notes   | suite_id, category
deepwiki_confluence_api_docs        | suite_id, alignment_score
deepwiki_confluence_architecture    | suite_id
deepwiki_confluence_general         | suite_id, category
deepwiki_transcripts                | suite_id, video_id
deepwiki_timeline                   | suite_id, event_type
```

⚠️ `unit_type` in `deepwiki_code_units` = `"class"` OR `"method"` — both go in same collection.

---

## 6. Provider Adapters

> Every external service goes through an adapter. Core code never imports GitHub, Neo4j, Qdrant, or Groq directly.

### 6A — Adapter Interfaces

```python
# adapters/interfaces.py

class VCSAdapter(ABC):
    def get_file_tree(repo_id, branch, extensions) -> list[str]
    def get_file_content(repo_id, path, ref) -> str
    def get_changed_files(repo_id, commit_sha) -> dict   # {added, modified, deleted}
    def shallow_clone(repo_id, target_dir, branch) -> None

class LLMAdapter(ABC):
    def complete(prompt, task_type, max_tokens) -> str
    def embed(texts: list[str]) -> list[list[float]]

class GraphDBAdapter(ABC):
    def run(query, params) -> list
    def run_write(query, params) -> None

class VectorAdapter(ABC):
    def upsert(collection, points) -> None
    def search(collection, vector, filter_dict, limit) -> list
    def delete(collection, ids) -> None

class AgentAdapter(ABC):
    def run_wiki_pipeline(code_units, repo_id) -> dict
    def run_delta_pipeline(changed_files, repo_id) -> dict
```

### 6B — Implementations Matrix

| Interface | Demo | Organization |
|---|---|---|
| `VCSAdapter` | `GitHubAdapter` (GitHub App) | `BitbucketAdapter` (App Password / PAT) |
| `LLMAdapter` | `GroqAdapter` + `AnthropicDirectAdapter` | `BedrockAdapter` (IAM, no keys) |
| `GraphDBAdapter` | `Neo4jAdapter` (bolt+s://) | `NeptuneAdapter` (openCypher, Sig V4) |
| `VectorAdapter` | `QdrantVectorAdapter` (API key) | `OpenSearchVectorAdapter` (IAM) |
| `AgentAdapter` | `LangGraphAgentAdapter` | `AgentCoreAdapter` |

### 6C — Factory (One Call to Get the Right Provider)

```python
# adapters/factory.py
from adapters import (GitHubAdapter, BitbucketAdapter,
                       GroqAdapter, BedrockAdapter,
                       Neo4jAdapter, NeptuneAdapter,
                       QdrantVectorAdapter, OpenSearchVectorAdapter,
                       LangGraphAgentAdapter, AgentCoreAdapter)

PROVIDERS = {
    "vcs":    {"github": GitHubAdapter,    "bitbucket": BitbucketAdapter},
    "llm":    {"groq":   GroqAdapter,      "bedrock":   BedrockAdapter},
    "graph":  {"neo4j":  Neo4jAdapter,     "neptune":   NeptuneAdapter},
    "vector": {"qdrant": QdrantVectorAdapter, "opensearch": OpenSearchVectorAdapter},
    "agent":  {"langgraph": LangGraphAgentAdapter, "agentcore": AgentCoreAdapter},
}

get_vcs    = lambda: PROVIDERS["vcs"]   [os.getenv("VCS_PROVIDER",    "github")]()
get_llm    = lambda: PROVIDERS["llm"]   [os.getenv("LLM_PROVIDER",    "groq")]()
get_graph  = lambda: PROVIDERS["graph"] [os.getenv("GRAPH_DB",        "neo4j")]()
get_vector = lambda: PROVIDERS["vector"][os.getenv("VECTOR_DB",       "qdrant")]()
get_agent  = lambda: PROVIDERS["agent"] [os.getenv("AGENT_RUNTIME",   "langgraph")]()
```

### 6D — Neptune vs Neo4j Cypher Rules

```
✅ Safe on both (write all queries this way):
   MATCH, CREATE, MERGE, SET, DELETE, DETACH DELETE
   WITH, UNWIND, RETURN, ORDER BY, LIMIT, SKIP
   Basic string, math, list functions

⛔ Neo4j only — never use (breaks on Neptune):
   apoc.*  procedures
   db.index.fulltext.*
   USE (multi-database)
   CALL {} IN TRANSACTIONS
```

---

## 7. Phase 1 — Java Foundation

> **Goal:** Demo-ready. Java Spring Boot. Method flow tracing. API catalog. Token proof.  
> **Time:** ~5 weeks at 2-3 hrs/day.  
> **Demo target:** Week 5.

---

### Iteration 12 — Schema Upgrade + Qdrant Migration
**Time:** 3-4 days

**Before starting:** Cloud deployment running (Iteration 11 ✅)

Steps:
1. Add nodes to Neo4j: `ApplicationSuite`, `Repository`, `Module`, `APIContract`, `APIContractImpact`
2. Add relationships: `BELONGS_TO`, `IN_MODULE`, `CALLS`, `READS`, `WRITES`, `EXPOSES`, `CONSUMES`
3. Migrate Qdrant from per-collection to `deepwiki_code_units` with `repo_id` in payload
4. Add `unit_type` field (`"class"` or `"method"`) to all Qdrant payloads
5. Run `verify.py` — confirm all connections and schema

**Done when:** `verify.py` shows all 8 Qdrant collections + Neo4j new nodes exist.

---

### Iteration 13 — JavaParser Code Analysis Service
**Time:** 4-5 days

**Before starting:** Iteration 12 ✅

Steps:
1. Create `code-analysis-service/` — Spring Boot project, Maven, Java 17
2. Add dependency: `com.github.javaparser:javaparser-symbol-solver-core:3.25.x`
3. Implement `JavaFileParser.java`:
   - Input: Java source file as String
   - Output: Language-agnostic JSON (classes, methods, fields, annotations, extends, implements)
4. Implement `MethodCallExtractor.java`:
   - Traverse method body AST
   - Extract all method call expressions
   - Resolve caller object type from field map
   - Output: `[{target: "OwnerService.save", line: 42, confidence: 1.0}]`
5. Implement `AnnotationExtractor.java`:
   - Extract annotation name + arguments per class and method
   - No framework knowledge here — just structural extraction
6. Expose REST endpoint: `POST /analyze` → accepts `{file_content, filename}` → returns JSON
7. Add to `docker-compose.yaml` / Railway deployment

**Done when:** `POST /analyze` with `OwnerController.java` content returns correct classes, methods with CALLS, and annotation names.

---

### Iteration 14 — Method Logic + CALLS Edges
**Time:** 3-4 days

**Before starting:** Iteration 13 ✅

Steps:
1. Create `METHOD_LOGIC_PROMPT` in `pipeline/wiki/summarizer.py`:
   - Input: method body + class wiki summary
   - Output: 2-3 sentence `logic_summary`
   - Skip trivial methods: getters, setters, constructors < 5 lines
2. Add semantic cache for method logic (hash of method body → summary)
3. Write `pipeline/graph/method_writer.py`:
   - Create `Method` nodes with `logic_summary`, `throws[]`, `reads_fields[]`, `writes_fields[]`
   - Create `CALLS` edges: `(Method)-[:CALLS {line, confidence}]->(Method)`
   - Create `READS`/`WRITES` edges for field access
4. Create `EXTENDS` and `IMPLEMENTS_INTERFACE` edges between Class nodes
5. Add method-level Qdrant embeddings to `deepwiki_code_units` (`unit_type: "method"`)
6. Method embedding text format:
   ```
   Method: {class}.{name}. Returns: {return_type}. Params: {params}.
   Annotations: {annotations}. Logic: {logic_summary}.
   ```

**Done when:** Neo4j shows CALLS chains. `MATCH (m:Method)-[:CALLS]->(called) RETURN m.name, called.name` returns actual call chain.

---

### Iteration 15 — APIContract Extraction
**Time:** 3-4 days

**Before starting:** Iteration 14 ✅

Steps:
1. Extend `JavaFileParser.java`:
   - Detect `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@RequestMapping`
   - Extract: HTTP method, path pattern, path variables, `@RequestBody` type, return type
   - Use LLM annotation extractor for non-standard annotations (cached)
2. Create `pipeline/graph/api_writer.py`:
   - Create `APIContract` node per endpoint
   - Create `(Repository)-[:EXPOSES]->(APIContract)` edges
3. Create `pipeline/graph/api_impact.py` (nightly job):
   - For each `APIContract`, find all `CONSUMES` edges
   - Create/update `APIContractImpact` node
4. Add `deepwiki_api_contracts` Qdrant collection
5. Add "API Catalog" page to Streamlit:
   - Table: all endpoints this repo exposes
   - Table: all endpoints this repo consumes
   - For each: method, path, auth_required, consuming repos

**Done when:** Spring PetClinic's 12 API endpoints appear in portal. Each shows which classes implement it.

---

### Iteration 16 — Flow Tracing + Intent Classification
**Time:** 3-4 days

**Before starting:** Iteration 15 ✅

Steps:
1. Create `api/routes/flow.py`:
   - Input: `{entry_point: "createOwner", repo_id: "..."}`
   - Graph query: follow `CALLS` edges up to 6 hops from entry method
   - Collect `logic_summary` from each `Method` node traversed
   - Stop at: DB boundary (Repository class), External API, or 6 hops
2. Create `api/intent_classifier.py`:
   - Input: developer question
   - Classify: `FLOW_TRACE | CLASS_LOOKUP | API_IMPACT | WHY_DECISION | HISTORY`
   - Simple: keyword detection + LLM for ambiguous cases
3. Update `api/routes/ask.py`:
   - Route to correct retrieval strategy based on intent
   - Enforce 600-token hard ceiling on all context
4. Add flow explanation to Streamlit:
   - Input: "Explain how owner creation works"
   - Output: step-by-step trace with class names, method names, logic at each step

**Flow explanation prompt:**
```
Given these flow steps (traced from actual code):
Step 1 [Angular · OwnerFormComponent]: {wiki}
Step 2 [API · POST /api/v1/owners]: {contract}
Step 3 [Spring · OwnerController.createOwner()]: {logic_summary}
...
Explain the flow step by step. Reference actual class and method names. Under 300 words.
```

**Done when:** "How does pet owner creation work?" returns traced answer citing `OwnerController`, `OwnerService`, `OwnerRepository` with logic descriptions. Total context: under 600 tokens.

---

### Iteration 17 — ApplicationSuite + Portal Upgrade
**Time:** 2-3 days

**Before starting:** Iteration 16 ✅

Steps:
1. Create `ApplicationSuite` node in Neo4j
2. Add `Repository` nodes (replaces bare Class → repo_id tracking)
3. Link `(Suite)-[:HAS_REPO]->(Repository)` edges
4. Update query API to accept `scope` param: `repo | suite | cross_suite`
5. Add suite-level Qdrant filter: `suite_id` payload field
6. Update Streamlit:
   - Suite selector in sidebar
   - Suite overview: all repos + their API counts + coverage scores
   - Method-level semantic search ("find methods that validate email")

**Done when:** Streamlit shows "Pet Management Platform" suite with backend repo. Suite-level "Ask" question searches across all repos in suite.

---

## 8. Phase 2 — Angular + Flow Tracing

> **Goal:** FE and BE linked. End-to-end flow from Angular form to database visible.  
> **Time:** ~4 weeks at 2-3 hrs/day.  
> **Demo target:** Week 9.

---

### Iteration 18 — ts-morph Angular Analysis Service
**Time:** 4-5 days

**Before starting:** Phase 1 ✅

Steps:
1. Create `ts-analysis-service/` — Node.js project
2. Install: `npm install ts-morph express`
3. Implement `AngularParser.ts`:
   - Extract `@Component`: selector, templateUrl, route
   - Extract `@Injectable`: scope, imported services
   - Extract `@NgModule`: routing config
   - Extract `HttpClient` calls: method + URL string → normalise
4. URL normalisation function:
   ```typescript
   function normaliseUrl(raw: string): string {
     return raw
       .replace(/\$\{[^}]+\}/g, '{param}')  // template literals
       .replace(/'\s*\+\s*\w+/g, '/{param}') // concatenation
       .replace(/\/\d+/g, '/{id}')            // literal numbers
       .replace(/\/$/, '');                   // trailing slash
   }
   ```
5. Output: same language-agnostic JSON format as Java service
6. Expose: `POST /analyze` endpoint
7. Add to deployment stack

**Done when:** Angular `PetService.ts` analyzed. Outputs component + service + HTTP calls with normalised URL patterns.

---

### Iteration 19 — FE-BE Suite Link + CONSUMES Edges
**Time:** 2-3 days

**Before starting:** Iteration 18 ✅

Steps:
1. Create `pipeline/graph/api_matcher.py`:
   - For each Angular `HttpClient` call (normalised path), search `APIContract` nodes
   - Exact match (method + path): confidence 1.0 → auto-create `CONSUMES` edge
   - Fuzzy match (path similarity > 0.85): confidence 0.7 → human review queue
   - No match: store as `unknown_call` for manual review
2. Create `(Repository)-[:CONSUMES {caller_class, confidence}]->(APIContract)` edges
3. Update API impact nightly job to include `CONSUMES` edges from FE repos
4. Add to Streamlit "API Catalog" page:
   - For each endpoint: show "Consumed by: AngularService.getPets() [confidence: 100%]"

**Done when:** `MATCH (r:Repository)-[:CONSUMES]->(api:APIContract)<-[:EXPOSES]-(be:Repository)` returns Angular → API → Spring Boot chain.

---

### Iteration 20 — End-to-End Flow Portal
**Time:** 2-3 days

**Before starting:** Iteration 19 ✅

Steps:
1. Update `flow-tracer` to start from Angular `Component` or `Service` as entry point
2. Flow now spans FE → API Contract → BE Controller → Service → Repository → DB
3. Add "Flow Viewer" page to Streamlit:
   - Input: feature name or class name
   - Output: visual step-by-step trace with repo labels
   - Show: [Angular] → [API] → [Spring Boot] → [DB]
4. Add token counter on flow page: "This answer used 640 tokens. Raw approach: 18,200 tokens."

**Done when:** "How does owner creation work?" traces from Angular form component through to JPA repository in one answer.

---

### Iteration 21 — Adaptive Retrieval + Model Router
**Time:** 2-3 days

**Before starting:** Iteration 20 ✅

Steps:
1. Create `api/feedback.py`:
   - Store: `{query_id, retrieval_strategy, was_helpful}` per query
   - Endpoint: `POST /feedback {query_id, thumbs_up: bool}`
2. Add thumbs up/down buttons to Streamlit "Ask" page
3. Create `api/model_router.py`:
   ```python
   TASK_MODEL_MAP = {
     "annotation_extraction": ["local", "groq", "bedrock"],
     "wiki_generation":       ["groq", "bedrock"],
     "architecture_analysis": ["claude", "bedrock_claude"],
   }
   def route(task, content_size) -> LLMAdapter: ...
   ```
4. Plug model router into wiki pipeline and query API

**Done when:** System logs which model handled each request. Feedback thumbs recorded in Neo4j.

---

## 9. Phase 3 — Copilot + Knowledge Sources

> **Goal:** @deepwiki in GitHub Copilot. Confluence decisions linked to code.  
> **Time:** ~3 weeks at 2-3 hrs/day.  
> **Demo target:** Week 12.

---

### Iteration 22 — GitHub Copilot MCP Server
**Time:** 3-4 days

**Before starting:** Phase 2 ✅

Steps:
1. Create `mcp-server/` — FastAPI app (separate deployment)
2. Implement 5 tools (MCP spec):

| Tool | Input | Output |
|---|---|---|
| `deepwiki_search` | `query, repo_id?, suite_id?` | Top class/method wikis |
| `deepwiki_get_class` | `class_name` | Full class wiki + method signatures |
| `deepwiki_get_flow` | `entry_point` | End-to-end flow trace |
| `deepwiki_get_api_consumers` | `method, path` | All repos consuming this API |
| `deepwiki_get_decisions` | `module_name` | ADRs and decisions for module |

3. Register MCP server in `.github/copilot-instructions.md`:
   ```markdown
   Use @deepwiki before reading any source file.
   deepwiki_search reduces token usage by 87%.
   ```
4. Deploy MCP server to Railway (separate service)
5. Test: `@deepwiki explain how authentication works`

**Done when:** Copilot agent mode shows `@deepwiki` tool. Query returns wiki context without reading any raw files.

---

### Iteration 23 — Confluence MCP Ingestion
**Time:** 3-4 days

**Before starting:** Iteration 22 ✅

Steps:
1. Install Atlassian MCP server: `@atlassian/mcp-atlassian`
2. Create `pipeline/ingestion/confluence_ingester.py`:
   - Fetch page via Atlassian MCP
   - Classify content type (auto + human confirm):
     ```
     meeting_notes → deepwiki_confluence_meeting_notes
     api_docs      → deepwiki_confluence_api_docs
     architecture  → extract via Claude Vision → Neo4j (NOT Qdrant)
     user_flows    → deepwiki_confluence_general
     server/db     → VAULT ONLY, never Qdrant
     general       → deepwiki_confluence_general
     ```
3. Create human submission form in Streamlit "Knowledge Sources" page:
   - URL input + category selector + module tags
   - Categories: `historical | current | upcoming | update`
4. Implement alignment scoring:
   - Compare confluence content to class wiki summaries
   - Score: -1.0 to +1.0
   - Create `ContradictionFlag` if score < -0.3 and category = `current`
5. Create `(ConfluencePage)-[:DOCUMENTS {alignment_score, category}]->(Module)` edges

**Done when:** Submit Confluence "Auth Design" page. It appears in "Ask" answers about auth with link to original page. Alignment score shown in portal.

---

### Iteration 24 — Human-in-Loop Review Portal
**Time:** 3-4 days

**Before starting:** Iteration 23 ✅

Steps:
1. Create `pipeline/module_detector.py`:
   ```python
   # com.xyz.petclinic.owner.controller → "Owner Module"
   # Strip layer suffixes: controller, service, repository, domain, dto
   def detect_module(package: str) -> str: ...
   ```
2. Create `pipeline/owner_detector.py` (multi-signal):
   - Signal 1: Parse `CODEOWNERS` file (confidence: 0.95)
   - Signal 2: `git log --pretty='%ae' -- module_path` (confidence: 0.70)
   - Signal 3: Confluence page author for this module (confidence: 0.65)
   - Aggregate → suggest owner, flag if signals disagree
3. Create `Person` nodes in Neo4j. Link: `(Module)-[:OWNED_BY]->(Person)`
4. Create "Module Review" page in Streamlit:
   - Show: module wiki draft + suggested owner + confidence
   - Buttons: ✅ Approve | ✏️ Edit | ❌ Reassign
   - Status badge: `confirmed | unconfirmed | needs_review`
5. Create review request trigger conditions:
   - New module detected
   - `>30 commits` since last review AND `coverage_score < 0.7`
   - Contradiction flag severity = HIGH

**Done when:** "Owner Module" shows wiki with "Owner: Sarah Chen (95% confidence from CODEOWNERS)". Approve button marks it confirmed.

---

## 10. Extension Modules (Add Later)

> Each extension is self-contained. Add in any order. Architecture is ready.

### EXT-1: Android Kotlin Parser
**Time:** 3-4 days  
**Steps:** Add `tree-sitter-kotlin` to Java `code-analysis-service`. Same JSON output format. Retrofit `@GET`/`@POST` annotations → exact API match (no normalisation needed). Add `kotlin` to `SCAN_CONFIG`.

### EXT-2: iOS Swift Parser  
**Time:** 4-5 days  
**Steps:** New Python microservice. SourceKitten via subprocess. Extract `UIViewController`, `ObservableObject`, `URLSession`/Alamofire calls. URL normalisation for Swift string interpolation `\(id)`.

### EXT-3: Video Transcript RAG
**Time:** 3-4 days  
**Steps:** Ingest video URL. Transcribe via AssemblyAI (diarization) or Whisper. Topic segmentation (sliding window cosine similarity). Chunk into segments. Embed → `deepwiki_transcripts`. Payload: `{video_url, start_sec, end_sec, speaker}`. Deep link: `video_url#t={start_sec}`.

### EXT-4: Architecture Diagram Vision
**Time:** 2-3 days  
**Steps:** Submit image via portal. Claude Vision extracts `{components[], relationships[], data_flows[]}` as JSON. Store as Neo4j nodes. NOT embedded in Qdrant. Appears in architecture queries via graph traversal.

### EXT-5: Cross-Suite Impact Dashboard
**Time:** 3-4 days  
**Steps:** Nightly job scans all `APIContract` nodes across all suites. `APIContractImpact` node lists affected repos across suites. New Streamlit page: "Change Risk". Input: API endpoint → output: all repos across all suites that consume it.

### EXT-6: Staleness Decay + Auto-Demotion
**Time:** 2-3 days  
**Steps:** Add nightly job: `confidence = original_score × 0.997^days`. Store `decayed_confidence` on source nodes. Auto-demote: `decayed_confidence < 0.5` → `category: needs_review`. Show staleness in portal ("⚠️ This source is 34 commits old").

### EXT-7: Slack Notifications
**Time:** 1-2 days  
**Steps:** Slack webhook URL in env. Trigger on: new module review request, high-severity contradiction (score < -0.7), owner confidence < 0.6. Message includes: module name, reason, portal link. Weekly digest for medium/low severity.

### EXT-8: VS Code Extension
**Time:** 4-5 days  
**Steps:** VS Code extension sidebar. On file open: call `deepwiki_get_class` for active class. Display wiki + caller chain + related decisions in sidebar. Auto-updates as developer navigates files.

---

## 11. Definition of Done Per Phase

### DEMO 1 Ready (End of Phase 1 — Week 5)
```
✅ Spring PetClinic analyzed at method level (not just class)
✅ CALLS edges visible: createOwner → save → repository.save
✅ Method logic_summary on all non-trivial methods
✅ APIContract catalog: all 12 Spring Boot endpoints listed
✅ "How does owner creation work?" returns traced flow under 600 tokens
✅ Token comparison: DeepWiki (800 tokens) vs Raw (15,800 tokens)
✅ ApplicationSuite + Repository nodes in Neo4j
✅ Cloud deployment stable: Railway API + Streamlit portal
```

### DEMO 2 Ready (End of Phase 2 — Week 9)
```
✅ Angular petclinic-web analyzed (components, services, HTTP calls)
✅ CONSUMES edges: AngularService → APIContract ← SpringController
✅ Flow trace spans FE to DB: "owner form → POST /api/v1/owners → controller → service → repo"
✅ Suite query: ask about "Pet Management Platform" searches both repos
✅ Thumbs up/down feedback captured
✅ Model router routing annotation extraction to cheapest model
```

### DEMO 3 Ready (End of Phase 3 — Week 12)
```
✅ @deepwiki active in GitHub Copilot agent mode
✅ deepwiki_search returns wiki without Copilot reading raw files
✅ Confluence page submitted, classified, aligned to module
✅ "Why do we use Infinispan?" returns Confluence decision with link
✅ Module review portal: approve/edit/reject wiki
✅ Suggested owner shown with confidence for each module
✅ ContradictionFlag raised for stale/wrong Confluence content
```

---

## 12. ⛔ Do Not Build

These items are explicitly out of scope. Do not add them.

```
⛔ Struts parser            — legacy stack, being migrated off
⛔ Spring 4 Remoting parser — legacy stack, being replaced
⛔ YAML annotation configs  — LLM is the config, zero maintenance needed
⛔ Per-repo Qdrant collections — payload filter scales better, always
⛔ Hardcoded RETRIEVAL_STRATEGIES — usage learning handles this
⛔ Real-time impact traversal at query time — nightly cache only
⛔ DB credentials in Qdrant or Neo4j — vault only, never searchable
⛔ Block wiki display until human confirms — utility first always
⛔ ContradictionFlag dashboard (undifferentiated list) — triage system only
⛔ Fine-tuning own LLM — use Groq/Bedrock/Claude
⛔ Custom Confluence scraper — use Atlassian MCP server
⛔ IntelliJ plugin before MCP proven — MCP first, plugin in Phase 5
```

---

## 13. ✅ Decisions Already Made (Do Not Revisit)

| # | Decision | Rule |
|---|---|---|
| D1 | VCS auth | GitHub App (demo), Bitbucket App Password (org). No individual PATs. |
| D2 | Scan strategy | Clone (initial, ephemeral, wiped). API fetch (delta, in-memory). |
| D3 | Code persistence | Zero. Raw code lives on server < 15 minutes. Never in Neo4j/Qdrant. |
| D4 | Annotation parsing | LLM + semantic cache. No YAML configs. Self-updating. |
| D5 | Qdrant design | 8 fixed collections. payload filter. Never per-repo. |
| D6 | Impact analysis | Pre-computed nightly. Single node lookup at query time. |
| D7 | Token ceiling | 600 tokens max context. Hard limit. Enforced at API layer. |
| D8 | Method logic | `logic_summary` on every non-trivial Method node. LLM-generated. |
| D9 | CALLS edges | Extracted from method bodies. Powers flow tracing. Required for Phase 2. |
| D10 | Package→Module | Explicit `BELONGS_TO` edge. Auto-detected from package prefix. |
| D11 | APIContract | First-class Neo4j node. Bridge between FE and BE. |
| D12 | Decision scope | Decision node at Module level. Not Class level. |
| D13 | Confluence typing | 6 typed collections. Meeting notes ≠ API docs ≠ architecture. |
| D14 | Language order | Java first (Phase 1). Angular (Phase 2). Others are extensions. |
| D15 | Cross-suite | Deferred to Extension phase. Within-suite covers 90% of value. |
| D16 | Wiki display | Immediate, tagged `unconfirmed`. Human confirmation = quality, not gate. |
| D17 | Retrieval | Usage-based learning. No manual strategy dictionary. |
| D18 | Model router | In from day one. Local LLM = one env var change when ready. |
| D19 | Neptune Cypher | Write all queries to openCypher subset. No APOC. Works on both. |
| D20 | AgentCore role | Tool gateway + session memory only. Not replacing Neptune or OpenSearch. |

---

## 📍 Quick Reference — Where Things Live

```
deepwiki/
├── code-analysis-service/      Java Spring Boot — JavaParser, method CALLS
├── ts-analysis-service/        Node.js — ts-morph, Angular analysis
├── swift-analysis-service/     Python — SourceKitten bridge (extension)
├── pipeline/
│   ├── ingestion/              VCS adapter, file scanner, Confluence ingester
│   ├── graph/                  Neo4j writers (classes, methods, api, module)
│   ├── embeddings/             Qdrant writer, embedding service
│   ├── wiki/                   Wiki generation (Groq/Claude/Bedrock)
│   ├── delta/                  Webhook handler, dependency resolver
│   └── planner/                Plan + test generation
├── adapters/
│   ├── interfaces.py           Abstract base classes (VCS, LLM, Graph, Vector)
│   ├── vcs/                    github.py, bitbucket.py, gitlab.py, azure.py
│   ├── llm/                    groq.py, anthropic.py, bedrock.py
│   ├── graph/                  neo4j.py, neptune.py
│   ├── vector/                 qdrant.py, opensearch.py
│   └── factory.py              get_vcs(), get_llm(), get_graph(), get_vector()
├── api/
│   ├── main.py                 FastAPI app, adapter injection
│   ├── routes/                 ask, search, flow, classes, plan, compare
│   └── intent_classifier.py    FLOW_TRACE | CLASS_LOOKUP | API_IMPACT | ...
├── mcp-server/                 Copilot MCP — 5 tools
├── ui/
│   └── app.py                  Streamlit portal
├── output/
│   ├── wiki/                   Per-class markdown pages
│   └── metrics/                Token logs
├── .env.demo                   GitHub + Neo4j + Qdrant + Groq
├── .env.org                    Bitbucket + Bedrock + Neptune + OpenSearch
├── verify.py                   Connection checks for all services
└── ARCHITECTURE.md             This file
```

---

*Last updated: May 2026. Update this file when a decision in Section 13 changes.*
