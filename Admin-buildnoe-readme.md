# Admin Build Now Feature — File Changes

## Angular — 4 files

| File | Change |
|---|---|
| src/app/core/services/admin.service.ts | NEW — HTTP calls to FastAPI pipeline |
| src/app/features/admin/admin.component.ts | UPDATED — Build Now + pipeline state |
| src/app/features/admin/admin.component.html | UPDATED — Build Now button + progress panel |
| src/app/features/admin/admin.component.scss | UPDATED — Pipeline panel styles |

## FastAPI — 1 new file

| File | Change |
|---|---|
| api/routes/admin_routes.py | NEW — /admin/onboard-repo, /admin/status/:id, /admin/reindex/:id |

## Wire up FastAPI (add to api/main.py)

```python
from api.routes.admin_routes import router as admin_router
app.include_router(admin_router)
```

## Admin password (environment.ts)

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  adminPassword: 'deepwiki2024',
};
```

## How Build Now works

1. User fills form (name, suite, tech stack, description, repo URL)
2. User clicks "Build Now" (yellow accent button)
3. Angular calls POST /admin/onboard-repo
4. FastAPI queues background task, returns repo_id immediately
5. Angular polls GET /admin/status/:repo_id every 2 seconds
6. Progress panel updates in real time (8 steps, 0–100%)
7. On done: stats shown, project added to portal
8. On fail: error shown, Retry button available

## How Re-index works (Manage Projects tab)

1. Click "Re-index" button next to any project with a repo URL
2. Angular calls POST /admin/reindex/:repo_id
3. Same polling mechanism as Build Now
4. Button shows "Indexing…" spinner while running

User fills form
      ↓
Clicks "Build Now" (yellow button)
      ↓
Angular → POST /admin/onboard-repo
FastAPI returns repo_id instantly (background task starts)
      ↓
Angular polls GET /admin/status/:repo_id every 2 seconds
Progress panel appears immediately:

  Building petclinic-backend…               98%
  ████████████████████████████████████░░  
  ✅ Cloning repository
  ✅ Parsing source files        87 files found
  ✅ Writing knowledge graph
  ✅ Generating wiki summaries   Calling LLM…
  ✅ Extracting API contracts
  ✅ Embedding to Qdrant
  ⏳ Matching API contracts      ← spinning
  🕐 Registering webhook

      ↓ (done)
  ✅ Build complete
  ████████████████████████████████████████  100%
  142 code units    12 API contracts
  ✅ Repo is live. Search and Ask DeepWiki are ready.