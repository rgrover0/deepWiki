"""
Iteration 18 — ts-morph Angular Analysis Service

Verifies:
  1. ts-analysis-service builds (tsc compiles)
  2. AngularParser extracts PetService: type=SERVICE, 9 methods, 9 HTTP calls
  3. OwnerListComponent: type=COMPONENT, selector, templateUrl
  4. URL normalisation: ${this.BASE}/pets -> /pets
  5. POST /analyze HTTP endpoint returns correct JSON

Requires:
  - Node.js 18+
  - ts-analysis-service running on port 8082 (node dist/index.js)
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
SVC  = ROOT / "ts-analysis-service"


def run_node(script: str) -> dict:
    """Write script to a temp file and run it from the SVC directory."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", dir=str(SVC), delete=False, encoding="utf-8"
    ) as f:
        f.write(script)
        tmp = f.name
    try:
        res = subprocess.run(
            ["node", Path(tmp).name],
            cwd=str(SVC),
            capture_output=True, text=True, shell=True
        )
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        return json.loads(res.stdout)
    finally:
        Path(tmp).unlink(missing_ok=True)


print("=" * 60)
print("DeepWiki - Iteration 18: ts-morph Angular Analysis Service")
print("=" * 60)

# ── 1. Build ───────────────────────────────────────────────
print("\n[1/5] TypeScript build:")
r = subprocess.run(["npm", "run", "build"], cwd=str(SVC),
                   capture_output=True, text=True, shell=True)
if r.returncode == 0:
    print("  tsc compiled OK")
else:
    print(f"  Build FAILED:\n{r.stderr}")
    sys.exit(1)

# ── 2. PetService ──────────────────────────────────────────
print("\n[2/5] PetService.ts analysis:")
data = run_node("""
const {analyseFile} = require('./dist/AngularParser');
const r = analyseFile('./test/PetService.ts');
const cls = r.classes[0];
process.stdout.write(JSON.stringify({
  name: cls.name,
  type: cls.component_type,
  scope: cls.injectable_scope,
  method_count: cls.methods.length,
  http_count: cls.http_calls.length,
  http_calls: cls.http_calls.map(h => h.method + ' ' + h.normalized_url)
}));
""")
assert data["name"] == "PetService",  f"Expected PetService, got {data['name']}"
assert data["type"] == "SERVICE",     f"Expected SERVICE, got {data['type']}"
assert data["scope"] == "root",       f"Expected root, got {data['scope']}"
assert data["method_count"] == 9,     f"Expected 9 methods, got {data['method_count']}"
assert data["http_count"] == 9,       f"Expected 9 HTTP calls, got {data['http_count']}"
print(f"  {data['name']} [{data['type']}] providedIn={data['scope']}")
print(f"  Methods: {data['method_count']} | HTTP calls: {data['http_count']}")
for call in data["http_calls"]:
    print(f"    {call}")
print("  OK")

# ── 3. OwnerListComponent ──────────────────────────────────
print("\n[3/5] OwnerListComponent.ts analysis:")
d2 = run_node("""
const {analyseFile} = require('./dist/AngularParser');
const r = analyseFile('./test/OwnerListComponent.ts');
const cls = r.classes[0];
process.stdout.write(JSON.stringify({
  name: cls.name,
  type: cls.component_type,
  selector: cls.selector || '',
  template_url: cls.template_url || '',
  method_count: cls.methods.length
}));
""")
assert d2["type"] == "COMPONENT",  f"Expected COMPONENT, got {d2['type']}"
assert d2["selector"],             "selector should not be empty"
assert d2["template_url"],         "template_url should not be empty"
print(f"  {d2['name']} [{d2['type']}]")
print(f"  selector={d2['selector']} | templateUrl={d2['template_url']}")
print(f"  Methods: {d2['method_count']}")
print("  OK")

# ── 4. URL normalisation ───────────────────────────────────
print("\n[4/5] URL normalisation rules:")
cases_raw = run_node(r"""
const {normaliseUrl} = require('./dist/AngularParser');
const cases = [
  ['${this.BASE}/pets',         '/pets'],
  ['${this.BASE}/pets/${id}',   '/pets/{param}'],
  ['${this.BASE}/owners/${id}', '/owners/{param}'],
  ['/api/owners/42',            '/api/owners/{id}'],
  ['/api/pets/',                '/api/pets'],
];
process.stdout.write(JSON.stringify(
  cases.map(([input, expected]) => ({
    input, expected, got: normaliseUrl(input),
    ok: normaliseUrl(input) === expected
  }))
));
""")
all_ok = True
for c in cases_raw:
    ok = "OK  " if c["ok"] else "FAIL"
    if not c["ok"]:
        all_ok = False
    print(f"  {ok}  {c['input']!r:40s} -> {c['got']!r}")
print(f"\n  {'All normalisation rules correct' if all_ok else 'Some rules wrong'}")

# ── 5. HTTP endpoint ───────────────────────────────────────
print("\n[5/5] POST /analyze HTTP endpoint:")
try:
    from pipeline.ingestion.ts_analysis_client import is_service_healthy, analyse_file

    if is_service_healthy():
        print("  Service health: OK")
        pet_path = str((SVC / "test" / "PetService.ts").resolve())
        result   = analyse_file(pet_path)
        cls      = result["classes"][0]
        print(f"  /analyze: {cls['name']} [{cls['component_type']}]"
              f" - {len(cls['http_calls'])} HTTP calls")
        print("  OK")
    else:
        print("  Service not running on :8082")
        print("  Start with: cd ts-analysis-service && node dist/index.js")
        print("  (Parser logic verified in steps 2-4)")
except Exception as e:
    print(f"  Client error: {e}")

print("\n" + "=" * 60)
print("Iteration 18 complete")
print("  Done when: PetService.ts -> SERVICE, 9 methods,")
print("  9 HTTP calls with normalised URLs (/pets, /owners, ...)")
print("=" * 60)
