# Monorepo refactor — Phase 0 green baseline

**Branch:** `refactor/monorepo-split`  
**Anchor tag:** `pre-refactor` → `09da259` (`feature/deepwiki_blueprint_phase1`)  
**Epic:** https://github.com/rgrover0/deepWiki/issues/10  
**Issue:** https://github.com/rgrover0/deepWiki/issues/11

## Checklist (runbook Phase 0)

| Check | Status (2026-08-06) | Notes |
|---|---|---|
| Working tree clean before branch | PASS | Branched from `feature/deepwiki_blueprint_phase1` |
| Tag `pre-refactor` pushed | PASS | Annotated tag at `09da259` |
| Branch `refactor/monorepo-split` pushed | PASS | Tracks `origin/refactor/monorepo-split` |
| `python admin.py status --suite "Pet Management Platform"` | N/A locally | No root `admin.py`; use `GET /admin/status/{repo_id}` / suite APIs after stack is up |
| FastAPI `/ask` known-good question | BLOCKED locally | No `.env`, no `fastapi`/`neo4j` in default Python 3.9 |
| Layer smoke tests exist | PASS | `tests/smoke/test_api_layer.py`, `tests/smoke/test_pipeline_layer.py` |

## How to complete live green (when Neo4j + Qdrant + keys available)

```bash
pip install -r requirements.txt httpx pytest
uvicorn api.main:app --host 0.0.0.0 --port 8000
# Health
curl -s localhost:8000/health
# Ask (adjust body to your API contract)
curl -s -X POST localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question":"<known-good PetClinic question>"}'
# Admin job poll after onboard
curl -s localhost:8000/admin/jobs
pytest tests/smoke -q
```

Record the live curl outputs as a comment on #11 before starting Phase 2 moves.

## Freeze

No feature work on this branch except monorepo refactor phases (DW-R0…DW-R6).
