# Monorepo inventory (DW-R0.5)

**Branch:** `refactor/monorepo-packages` (from `refactor/monorepo-split`)  
**Issue:** https://github.com/rgrover0/deepWiki/issues/12

## Package buckets

| Path | Bucket | Notes |
|---|---|---|
| `pipeline/graph/schema.py` | **core** | Neo4j driver + constraints |
| `pipeline/embeddings/*` | **core** | Qdrant client + embedder |
| `api/model_router.py` | **core** | Shared LLM routing (pipeline already imports from api) |
| env / dotenv loading | **core** | `core.config` |
| job status store | **core** | Shared file-backed jobs for API↔CLI without imports |
| `api/*` (routes, main, feedback, intent) | **api** | FastAPI serving |
| `mcp-server/*` | api-adjacent | Keep sibling; HTTP to API |
| `pipeline/*` (ingestion, writers, delta, wiki, planner, comparison, bootstrap) | **pipeline** | Ingestion + orchestration |
| `run_iteration*.py`, `verify.py`, `run_claude_test.py` | **scripts** | One-off runners |
| `ui/*` | scripts/legacy | Streamlit; not part of package contracts |
| `code-analysis-service/`, `ts-analysis-service/`, `deepwiki-ui/` | leave | HTTP siblings |

## Cross-imports to sever

### api → pipeline (must become core.* or subprocess)

| Consumer | Import | Resolution |
|---|---|---|
| Most routes, `main`, `feedback` | `pipeline.graph.schema` | → `core.graph.schema` |
| ask, search, plan, main, admin | `pipeline.embeddings.*` | → `core.embeddings.*` |
| ask | `pipeline.ingestion.confluence_ingester.search_confluence` | → `core.confluence_search` |
| admin_routes | full ingestion stack | → `python -m pipeline.admin_cli onboard` |
| project | `pipeline.project_bootstrap` | → admin_cli `bootstrap` |
| plan | planner + metrics | → admin_cli `plan` |
| compare | comparison runners | → admin_cli `compare` |
| confluence | `ingest_page` | → admin_cli `confluence-ingest` |
| suite | `suite_writer` | → admin_cli `suite-bootstrap` |

### pipeline → api (must become core.*)

| Consumer | Import | Resolution |
|---|---|---|
| `pipeline/wiki/summarizer.py` | `api.model_router` | → `core.llm.model_router` |
| `pipeline/ingestion/confluence_ingester.py` | `api.model_router` | → `core.llm.model_router` |

## Dependency rule

```
api → core
pipeline → core
api ↛ pipeline (subprocess / job files only)
pipeline ↛ api
core ↛ api|pipeline
```
