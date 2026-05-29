# DeepWiki — Pipeline Gap Analysis & Wiring Plan
> What exists, what is missing, and exactly what to build next

---

## 1. Honest State of Each Layer

```
LAYER              WHAT EXISTS                           WHAT IS MISSING
─────────────────────────────────────────────────────────────────────────
admin.py (CLI)     Full 8-step pipeline:                 Not callable from web.
                   clone → parse → Neo4j →               Not an HTTP endpoint.
                   wiki → APIcontracts →                 Outputs to terminal only.
                   embed → webhook

FastAPI backend    /ask /search /classes                  No /admin/* endpoints.
                   /flow /plan /compare /stats            admin.py never called.

Angular Admin tab  Form saves to in-memory signal.        Does not call FastAPI.
                   Nothing reaches any database.          No progress feedback.
                   No real submission.                    No status polling.

Extension modules  Designed in architecture doc.          Zero code written.
(EXT-1 to EXT-8)  Ready to slot in.                     Not started.
```

---

## 2. The 3 Specific Gaps You Identified

### Gap A — Repo Cloning / Scanning Does Not Trigger from Admin

**What exists:**

```python
# admin.py — works perfectly from terminal
python admin.py add-repo \
  --url https://github.com/org/petclinic-backend \
  --language java \
  --suite "Pet Management Platform"
# → clones, parses, writes Neo4j, generates wikis, embeds, registers webhook
```

**What does NOT happen when admin tab submits:**

```typescript
// admin.component.ts — submit() today
submit(): void {
  this.projectService.add({ id: ..., name: this.form.name, ... });
  // ↑ Only updates the in-memory Angular signal.
  //   No HTTP call. No clone. No parse. No Neo4j write.
}
```

**Consequence:** Adding a repo via the UI only changes what the browser sees. The databases are unchanged. A page refresh loses everything.

---

### Gap B — Wiki / API Contracts / Flow Traces / Embeddings Not Regenerated

When a new repo is added via admin UI:

| Pipeline Step | admin.py CLI | Angular Admin today |
|---|---|---|
| Sparse clone GitHub | ✅ `_scan_repo()` | ❌ |
| Parse source files | ✅ JavaParser / ts-morph | ❌ |
| Write Neo4j nodes | ✅ `_write_code_units()` | ❌ |
| Generate wiki summaries (LLM) | ✅ `_generate_wikis()` | ❌ |
| Extract APIContracts | ✅ `_extract_api_contracts()` | ❌ |
| Embed to Qdrant | ✅ `_embed_code_units()` | ❌ |
| Run API matching across suite | ✅ `_run_api_matching()` | ❌ |
| Register webhook | ✅ `_register_webhook()` | ❌ |

---

### Gap C — Historical Iterations Have No Automated Re-Run

Iterations 1–11 were each run as one-off Python scripts:

```bash
python run_iteration3.py   # ran once, Spring PetClinic
python run_iteration4.py   # ran once
python run_iteration5.py   # ran once
```

There is no command that:
- Re-runs the full pipeline for an existing repo from scratch
- Runs all steps on a new repo in the correct order
- Produces an audit log of what ran and what succeeded

`admin.py reindex` covers this for a single repo but is not triggered from the UI.

---

## 3. What Needs to Be Built — Iteration 25

> **Name:** Admin Pipeline Wiring  
> **Time:** 4–5 days  
> **Goal:** Submitting the Admin form triggers the full 8-step pipeline. Status is shown in real time.

---

### Step 1 — FastAPI: `/admin/onboard-repo` endpoint

```python
# api/routes/admin.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])

class OnboardRepoRequest(BaseModel):
    repo_url:  str
    language:  str          # java | typescript | kotlin | swift
    suite:     str          # suite name or id
    new_suite: str = ""     # if creating new suite

class OnboardStatus(BaseModel):
    repo_id: str
    status:  str            # queued | running | done | failed
    step:    str            # current step name
    progress: int           # 0–100
    message: str = ""

# In-memory job store (swap for Redis in prod)
_jobs: dict[str, OnboardStatus] = {}

@router.post("/onboard-repo")
async def onboard_repo(
    req: OnboardRepoRequest,
    background_tasks: BackgroundTasks,
):
    repo_id = req.repo_url.rstrip("/").split("/")[-1].replace(".git", "").lower()

    _jobs[repo_id] = OnboardStatus(
        repo_id=repo_id, status="queued",
        step="Queued", progress=0
    )

    background_tasks.add_task(_run_pipeline, repo_id, req)

    return {"repo_id": repo_id, "message": "Pipeline started"}


@router.get("/status/{repo_id}")
async def get_status(repo_id: str):
    job = _jobs.get(repo_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def _run_pipeline(repo_id: str, req: OnboardRepoRequest):
    """Runs the full 8-step onboarding pipeline in the background."""
    from pipeline.ingestion.repo_scanner import scan_repo
    from pipeline.graph.code_writer    import write_code_units
    from pipeline.wiki.summarizer      import generate_wikis
    from pipeline.graph.api_writer     import extract_api_contracts
    from pipeline.embeddings.writer    import embed_code_units
    from pipeline.graph.api_matcher    import run_api_matching
    from adapters.factory              import get_vcs

    steps = [
        ("Cloning repository",          10),
        ("Parsing source files",         25),
        ("Writing knowledge graph",      40),
        ("Generating wiki summaries",    55),
        ("Extracting API contracts",     68),
        ("Generating embeddings",        80),
        ("Matching API contracts",       90),
        ("Registering webhook",         100),
    ]

    def update(i: int, extra: str = ""):
        label, progress = steps[i]
        _jobs[repo_id] = OnboardStatus(
            repo_id=repo_id, status="running",
            step=label, progress=progress, message=extra
        )

    try:
        suite_id = (req.new_suite or req.suite).lower().replace(" ", "-")

        update(0)
        code_units = scan_repo(req.repo_url, req.language, repo_id)

        update(1, f"{len(code_units)} files found")
        # parse already done inside scan_repo

        update(2)
        write_code_units(code_units, repo_id, suite_id)

        update(3)
        generate_wikis(code_units, repo_id)

        update(4)
        contracts = extract_api_contracts(code_units, repo_id)

        update(5, f"{len(contracts)} contracts found")
        embed_code_units(code_units, repo_id, suite_id)

        update(6)
        run_api_matching(suite_id)

        update(7)
        vcs = get_vcs()
        vcs.register_webhook(req.repo_url, repo_id,
                             "https://your-api.railway.app/webhook")

        _jobs[repo_id] = OnboardStatus(
            repo_id=repo_id, status="done",
            step="Complete", progress=100,
            message=f"{len(code_units)} units · {len(contracts)} APIs"
        )

    except Exception as e:
        _jobs[repo_id] = OnboardStatus(
            repo_id=repo_id, status="failed",
            step="Error", progress=0, message=str(e)
        )
```

Register in `api/main.py`:

```python
from api.routes.admin import router as admin_router
app.include_router(admin_router)
```

---

### Step 2 — Angular: `AdminService` calling the real API

```typescript
// core/services/admin.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient }          from '@angular/common/http';
import { environment }         from '../../environments/environment';
import { interval, switchMap, takeWhile } from 'rxjs';

export interface OnboardStatus {
  repo_id:  string;
  status:   'queued' | 'running' | 'done' | 'failed';
  step:     string;
  progress: number;
  message:  string;
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private http   = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  onboardRepo(payload: {
    repo_url: string;
    language: string;
    suite:    string;
    new_suite?: string;
  }) {
    return this.http.post<{ repo_id: string; message: string }>(
      `${this.apiUrl}/admin/onboard-repo`, payload
    );
  }

  /** Polls every 2 seconds until status is 'done' or 'failed'. */
  pollStatus(repoId: string) {
    return interval(2000).pipe(
      switchMap(() =>
        this.http.get<OnboardStatus>(`${this.apiUrl}/admin/status/${repoId}`)
      ),
      takeWhile(s => s.status !== 'done' && s.status !== 'failed', true)
    );
  }
}
```

---

### Step 3 — Angular Admin: Replace `submit()` with real pipeline call

```typescript
// admin.component.ts — replace submit() entirely

import { AdminService, OnboardStatus } from '../../core/services/admin.service';

// Add to constructor:
private adminService = inject(AdminService);

// New state signals:
pipelineStatus = signal<OnboardStatus | null>(null);
submitting     = signal(false);

submit(): void {
  if (!this.form.name || !this.form.description) {
    this.notify('Name and Description are required.'); return;
  }
  const suite = this.newSuiteMode ? this.form.newSuite : this.form.suite;
  if (!suite) { this.notify('Please select or create a suite.'); return; }
  if (!this.form.repositoryUrl) { this.notify('Repository URL is required.'); return; }

  this.submitting.set(true);
  this.pipelineStatus.set({ repo_id: '', status: 'queued',
                             step: 'Queued', progress: 0, message: '' });

  this.adminService.onboardRepo({
    repo_url:  this.form.repositoryUrl,
    language:  this.detectedLanguage(),   // from tech stack or dropdown
    suite,
    new_suite: this.newSuiteMode ? this.form.newSuite : '',
  }).subscribe({
    next: ({ repo_id }) => {
      this.adminService.pollStatus(repo_id).subscribe({
        next:     (status) => this.pipelineStatus.set(status),
        complete: ()       => { this.submitting.set(false); this.reset(); },
        error:    (err)    => { this.notify(`Pipeline failed: ${err.message}`);
                               this.submitting.set(false); },
      });
    },
    error: (err) => {
      this.notify(`Could not start pipeline: ${err.message}`);
      this.submitting.set(false);
    },
  });
}

detectedLanguage(): string {
  const ts = this.form.techStack.map(t => t.toLowerCase());
  if (ts.some(t => t.includes('java') || t.includes('spring'))) return 'java';
  if (ts.some(t => t.includes('angular') || t.includes('typescript') || t.includes('react'))) return 'typescript';
  if (ts.some(t => t.includes('kotlin') || t.includes('android'))) return 'kotlin';
  if (ts.some(t => t.includes('swift') || t.includes('ios'))) return 'swift';
  return 'java'; // default
}
```

---

### Step 4 — Angular Admin: Progress UI

**Add to `admin.component.html`** (below the submit button, inside Add Project tab):

```html
<!-- Pipeline progress — shown after submission -->
@if (pipelineStatus(); as job) {
  <div class="pipeline-status" [class.failed]="job.status === 'failed'">

    <div class="flex items-center justify-between mb-2">
      <span class="text-sm font-medium">{{ job.step }}</span>
      <span class="text-sm text-muted-foreground">{{ job.progress }}%</span>
    </div>

    <div class="progress-track mb-3">
      <div class="progress-fill"
           [class.bg-destructive]="job.status === 'failed'"
           [style.width.%]="job.progress"
           style="transition: width 0.5s ease">
      </div>
    </div>

    @if (job.message) {
      <p class="text-xs text-muted-foreground">{{ job.message }}</p>
    }

    @switch (job.status) {
      @case ('done') {
        <p class="text-sm text-green-600 font-medium mt-2">
          ✅ Repository indexed successfully — available in portal
        </p>
      }
      @case ('failed') {
        <p class="text-sm text-destructive font-medium mt-2">
          ❌ Pipeline failed. Check FastAPI logs.
        </p>
      }
      @case ('running') {
        <p class="text-xs text-muted-foreground animate-pulse mt-1">
          Running… do not close this tab
        </p>
      }
    }
  </div>
}
```

**Add to `admin.component.scss`**:

```scss
.pipeline-status {
  @apply border rounded-lg p-4 space-y-1 bg-secondary;
  &.failed { @apply border-destructive/40 bg-destructive/5; }
}
```

---

### Step 5 — FastAPI: `/admin/reindex` endpoint (historical re-run)

```python
# api/routes/admin.py — add this endpoint

@router.post("/reindex/{repo_id}")
async def reindex_repo(repo_id: str, background_tasks: BackgroundTasks):
    """Re-runs the full pipeline for an existing repo. Deletes and rebuilds its nodes."""
    graph = get_graph()

    repo = graph.run("MATCH (r:Repository {id:$id}) RETURN r", {"id": repo_id})
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repo '{repo_id}' not found")

    r = repo[0]["r"]

    # Build a fake request object from stored data
    req = OnboardRepoRequest(
        repo_url  = r["repo_url"],
        language  = r["language"],
        suite     = r.get("suite_id", ""),
    )

    # Wipe existing nodes for this repo only
    graph.run_write("""
        MATCH (r:Repository {id:$id})-[:HAS_MODULE*]->(n)
        DETACH DELETE n
    """, {"id": repo_id})

    _jobs[repo_id] = OnboardStatus(repo_id=repo_id, status="queued",
                                    step="Re-index queued", progress=0)

    background_tasks.add_task(_run_pipeline, repo_id, req)

    return {"repo_id": repo_id, "message": "Re-index started"}
```

---

## 4. Extension Modules — Honest Status

Every extension module is:
- **Fully designed** in `ARCHITECTURE.md` (steps, time, dependencies)
- **Zero code written** — not started

```
EXT-1  Android Kotlin Parser        📋 Planned  ❌ Not started
EXT-2  iOS Swift Parser             📋 Planned  ❌ Not started
EXT-3  Video Transcript RAG         📋 Planned  ❌ Not started
EXT-4  Architecture Diagram Vision  📋 Planned  ❌ Not started
EXT-5  Cross-Suite Impact Dashboard 📋 Planned  ❌ Not started
EXT-6  Staleness Decay              📋 Planned  ❌ Not started
EXT-7  Slack Notifications          📋 Planned  ❌ Not started
EXT-8  VS Code Extension            📋 Planned  ❌ Not started
```

---

## 5. Complete Iteration Sequence Going Forward

```
It 24  Human-in-Loop Review Portal             ← current next
It 25  Admin Pipeline Wiring                   ← this document
         /admin/onboard-repo FastAPI endpoint
         AdminService Angular
         Progress UI in admin tab
         /admin/reindex endpoint

Then Extensions (pick order based on business need):
  EXT-6  Staleness Decay + Auto-Demotion       2–3 days
  EXT-7  Slack Notifications                   1–2 days
  EXT-5  Cross-Suite Impact Dashboard          3–4 days
  EXT-1  Android Kotlin Parser                 3–4 days
  EXT-4  Architecture Diagram Vision           2–3 days
  EXT-3  Video Transcript RAG                  3–4 days
  EXT-2  iOS Swift Parser                      4–5 days
  EXT-8  VS Code Extension                     4–5 days
```

---

## 6. What Works Right Now (No Changes Needed)

```
✅ python admin.py add-repo --url <url> --language java --suite <suite>
   → Full 8-step pipeline runs from terminal
   → Data lands in Neo4j AuraDB + Qdrant Cloud
   → FastAPI /ask, /search, /flow, /plan immediately return answers

✅ Webhook registered → future code pushes trigger delta pipeline automatically

✅ python admin.py add-doc --url <confluence_url> --type api_docs --suite <suite>
   → Ingests document, embeds, scores alignment

✅ python admin.py status --suite "Pet Management Platform"
   → Shows all repos, modules, class count
```

The CLI is fully functional. Iteration 25 wires it to the web UI so non-developers can use it without touching the terminal.
