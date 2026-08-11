# deepWiki

Generates DeepWiki knowledge graphs and semantic answers over any codebase.

## Package layout

```
core/       shared clients (Neo4j, Qdrant, LLM router, config, job store)
api/        FastAPI serving layer  → depends on core only
pipeline/   ingestion + orchestration → depends on core only
scripts/    one-off iteration / verify runners
```

**Rule:** `api → core`, `pipeline → core`. Never `api ↔ pipeline` via import — the API triggers ingestion with:

```bash
python -m pipeline.admin_cli onboard --repo-id … --suite-id … --repo-url …
```

## Run

```bash
pip install -e ".[dev]"
cp .env.example .env   # fill credentials

# API
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Ingestion CLI (also used by Admin "Build Now" via subprocess)
python -m pipeline.admin_cli --help
```

## Tests

```bash
pytest tests/unit -q
lint-imports
```

## Railway

API start command (already in `railway.toml`):

`uvicorn api.main:app --host 0.0.0.0 --port $PORT`

Pipeline is a separate conceptual worker; for the demo the API spawns `pipeline.admin_cli` as a subprocess and polls `core.jobs`.
