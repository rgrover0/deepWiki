"""
Pre-Phase 2 — Angular Frontend Scaffold (Iteration A from FRONTEND_PLAN.md)

Verifies:
  1. deepwiki-ui/ project exists with correct structure
  2. Core models exist (project, suite, wiki, graph)
  3. Core services exist (project, wiki, graph-data, d3-renderer)
  4. Shared components exist (badge, card, button, tabs, input, progress, pipes)
  5. Layout components exist (header, footer)
  6. Feature routes exist (projects, project-detail, search, graph)
  7. Angular build succeeds (zero errors)

Done when: ng serve starts at localhost:4200,
  / shows project cards, /graph shows D3 cosmos view,
  /project/spring-petclinic shows 5 tabs with Ask DeepWiki wired to FastAPI.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
UI   = ROOT / "deepwiki-ui"

print("=" * 60)
print("DeepWiki - Pre-Phase2: Angular Frontend Scaffold")
print("=" * 60)


def check(label: str, path: Path):
    exists = path.exists()
    print(f"  {'OK  ' if exists else 'MISS'}  {path.relative_to(ROOT)}")
    return exists


all_ok = True

# ── 1. Project root ────────────────────────────────────────
print("\n[1/7] Project root:")
for p in [
    UI / "package.json",
    UI / "tailwind.config.js",
    UI / "tsconfig.json",
    UI / "angular.json",
    UI / "src" / "styles.scss",
    UI / "src" / "environments" / "environment.ts",
    UI / "src" / "environments" / "environment.prod.ts",
]:
    all_ok &= check("", p)

# ── 2. Core models ─────────────────────────────────────────
print("\n[2/7] Core models:")
for p in [
    UI / "src/app/core/models/project.model.ts",
    UI / "src/app/core/models/suite.model.ts",
    UI / "src/app/core/models/wiki.model.ts",
    UI / "src/app/core/models/graph.model.ts",
    UI / "src/app/core/models/index.ts",
]:
    all_ok &= check("", p)

# ── 3. Services ────────────────────────────────────────────
print("\n[3/7] Core services:")
for p in [
    UI / "src/app/core/services/project.service.ts",
    UI / "src/app/core/services/wiki.service.ts",
    UI / "src/app/core/services/graph-data.service.ts",
    UI / "src/app/core/services/d3-renderer.service.ts",
    UI / "src/app/core/services/mock-data.ts",
]:
    all_ok &= check("", p)

# ── 4. Shared components ───────────────────────────────────
print("\n[4/7] Shared component library:")
for p in [
    UI / "src/app/shared/components/badge/badge.component.ts",
    UI / "src/app/shared/components/card/card.component.ts",
    UI / "src/app/shared/components/button/button.component.ts",
    UI / "src/app/shared/components/tabs/tabs.component.ts",
    UI / "src/app/shared/components/input/input.component.ts",
    UI / "src/app/shared/components/progress/progress.component.ts",
    UI / "src/app/shared/pipes/method-color.pipe.ts",
    UI / "src/app/shared/pipes/truncate.pipe.ts",
]:
    all_ok &= check("", p)

# ── 5. Layout ──────────────────────────────────────────────
print("\n[5/7] Layout components:")
for p in [
    UI / "src/app/layout/header/header.component.ts",
    UI / "src/app/layout/footer/footer.component.ts",
    UI / "src/app/app.ts",
    UI / "src/app/app.routes.ts",
    UI / "src/app/app.config.ts",
]:
    all_ok &= check("", p)

# ── 6. Feature routes ──────────────────────────────────────
print("\n[6/7] Feature components (lazy routes):")
for p in [
    UI / "src/app/features/projects/projects.component.ts",
    UI / "src/app/features/project-detail/project-detail.component.ts",
    UI / "src/app/features/search/search.component.ts",
    UI / "src/app/features/graph/graph.component.ts",
]:
    all_ok &= check("", p)

# ── 7. Build ───────────────────────────────────────────────
print("\n[7/7] Angular build (ng build --configuration development):")
result = subprocess.run(
    ["npx", "ng", "build", "--configuration", "development"],
    cwd=str(UI),
    capture_output=True, text=True, shell=True
)
if result.returncode == 0 and "Application bundle generation complete" in result.stdout + result.stderr:
    print("  Build: OK")
    dist = UI / "dist" / "deepwiki-ui"
    print(f"  Output: {dist}")
else:
    print("  Build FAILED")
    print(result.stderr[-500:] if result.stderr else result.stdout[-500:])
    all_ok = False

print("\n" + "=" * 60)
print(f"Pre-Phase 2: {'ALL CHECKS PASS' if all_ok else 'SOME CHECKS FAILED'}")
print()
print("  Start dev server:")
print("    cd deepwiki-ui && npx ng serve")
print()
print("  Done when:")
print("    / -> project cards for Pet Management Platform")
print("    /project/spring-petclinic -> 5 tabs, Ask wired to FastAPI")
print("    /graph -> D3 cosmos graph, drill-down works")
print("    /search -> semantic search via FastAPI /search")
print("=" * 60)
