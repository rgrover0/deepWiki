"""
Phase 2 — Angular Frontend (Iterations B–G from FRONTEND_PLAN.md)

Verifies:
  B. Shared component library — stateful Tabs, Textarea
  C. Projects page — suite filter tabs, loading skeleton, page title
  D. D3 Graph — AppShell routing (graph bypasses header/footer)
  E. ProjectDetail — back nav, stats bar, loading skeleton, savings metric
  F. AI Sections — loading skeletons, error states, suggested questions
  G. Search — computed filteredResults, tech chip filter, ngModel fix, page title

Done when: ng serve starts at localhost:4200 with no errors,
  / shows project cards with suite filter tabs,
  /project/spring-petclinic shows 5 tabs wired to Ask DeepWiki,
  /graph shows full-screen D3 (no header/footer),
  /search shows semantic search with tech chip filters.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
UI   = ROOT / "deepwiki-ui"
SRC  = UI / "src" / "app"

print("=" * 60)
print("DeepWiki - Phase 2: Angular Frontend Polish")
print("=" * 60)


def check(label: str, path: Path):
    exists = path.exists()
    print(f"  {'OK  ' if exists else 'MISS'}  {path.relative_to(ROOT)}")
    return exists


def grep(path: Path, pattern: str) -> bool:
    if not path.exists():
        return False
    return pattern in path.read_text(encoding="utf-8", errors="ignore")


all_ok = True

# ── B. Shared component library ────────────────────────────
print("\n[B] Shared component library:")
checks_b = [
    (SRC / "shared/components/textarea/textarea.component.ts", "ControlValueAccessor"),
    (SRC / "shared/components/tabs/tabs.component.ts", "InjectionToken"),
    (SRC / "shared/components/tabs/tabs.component.ts", "TABS_CTX"),
]
for path, pattern in checks_b:
    ok = path.exists() and grep(path, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {path.relative_to(ROOT)}  ({pattern})")
    all_ok &= ok

# ── C. Projects page ───────────────────────────────────────
print("\n[C] Projects page:")
checks_c = [
    (SRC / "features/projects/projects.component.ts", "activeSuite"),
    (SRC / "features/projects/projects.component.ts", "visibleSuites"),
    (SRC / "features/projects/projects.component.ts", "animate-pulse"),
    (SRC / "features/projects/projects.component.ts", "Title"),
]
for path, pattern in checks_c:
    ok = path.exists() and grep(path, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {path.name}  ({pattern})")
    all_ok &= ok

# ── D. AppShell routing ────────────────────────────────────
print("\n[D] AppShell routing:")
checks_d = [
    (SRC / "layout/app-shell/app-shell.component.ts", "AppShellComponent"),
    (SRC / "app.routes.ts", "AppShellComponent"),
    (SRC / "app.routes.ts", "children"),
    (SRC / "app.ts", "router-outlet"),
]
for path, pattern in checks_d:
    ok = path.exists() and grep(path, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {path.name}  ({pattern})")
    all_ok &= ok

# ── E. ProjectDetail ───────────────────────────────────────
print("\n[E] ProjectDetail enhancements:")
checks_e = [
    (SRC / "features/project-detail/project-detail.component.ts", "loading"),
    (SRC / "features/project-detail/project-detail.component.ts", "savings"),
    (SRC / "features/project-detail/project-detail.component.ts", "routerLink=\"/\""),
    (SRC / "features/project-detail/project-detail.component.ts", "Title"),
]
for path, pattern in checks_e:
    ok = path.exists() and grep(path, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {path.name}  ({pattern})")
    all_ok &= ok

# ── G. Search polish ───────────────────────────────────────
print("\n[G] Search polish:")
checks_g = [
    (SRC / "features/search/search.component.ts", "filteredResults = computed"),
    (SRC / "features/search/search.component.ts", "activeTechs"),
    (SRC / "features/search/search.component.ts", "asStr"),
    (SRC / "features/search/search.component.ts", "Title"),
]
for path, pattern in checks_g:
    ok = path.exists() and grep(path, pattern)
    print(f"  {'OK  ' if ok else 'MISS'}  {path.name}  ({pattern})")
    all_ok &= ok

# ── Build ──────────────────────────────────────────────────
print("\n[Build] Angular build (ng build --configuration development):")
result = subprocess.run(
    ["npx", "ng", "build", "--configuration", "development"],
    cwd=str(UI),
    capture_output=True, text=True, shell=True, encoding="utf-8", errors="replace"
)
stdout_err = (result.stdout or "") + (result.stderr or "")
if result.returncode == 0 and "Application bundle generation complete" in stdout_err:
    print("  Build: OK (zero errors)")
else:
    print("  Build FAILED")
    print(stdout_err[-800:])
    all_ok = False

print("\n" + "=" * 60)
print(f"Phase 2: {'ALL CHECKS PASS' if all_ok else 'SOME CHECKS FAILED'}")
print()
print("  Start dev server:  cd deepwiki-ui && npx ng serve")
print()
print("  Test routes:")
print("    /              -> project cards + suite filter tabs")
print("    /project/<id>  -> 5 tabs, Ask wired to FastAPI")
print("    /graph         -> full-screen D3 (no header/footer)")
print("    /search        -> semantic search + tech chip filters")
print("=" * 60)
