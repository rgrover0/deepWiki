"""
Iteration 13 — JavaParser Code Analysis Service

Verifies the service is running and tests it against OwnerController.java.

Before running:
  docker compose up code-analysis-service --build -d

Done when: POST /analyze with OwnerController.java returns correct classes,
           methods with CALLS edges, and annotation names.
"""

import json
from pipeline.ingestion.java_analysis_client import analyze_file, is_service_healthy

TEST_FILE = "repos/spring-petclinic/src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java"

print("=" * 60)
print("DeepWiki — Iteration 13: JavaParser Service Verification")
print("=" * 60)

# 1. Health check
print("\n[1/2] Checking service health...")
if not is_service_healthy():
    print("❌ code-analysis-service is not running.")
    print("   Start it with: docker compose up code-analysis-service --build -d")
    exit(1)
print("✅ Service healthy")

# 2. Analyze OwnerController.java
print(f"\n[2/2] Analyzing: {TEST_FILE}")
result = analyze_file(TEST_FILE)

print(f"\n  Package : {result.get('package', '')}")
print(f"  Classes : {len(result.get('classes', []))}")

for cls in result.get("classes", []):
    print(f"\n  ┌─ {cls['name']} [{cls['component_type']}]")
    print(f"  │  Annotations : {cls['annotations']}")
    print(f"  │  Extends     : {cls.get('extends')}")
    print(f"  │  Implements  : {cls.get('implements', [])}")
    print(f"  │  Fields      : {len(cls.get('fields', []))}")
    for f in cls.get("fields", []):
        print(f"  │    {f['type']} {f['name']}  {f['annotations']}")

    print(f"  │  Methods     : {len(cls.get('methods', []))}")
    for m in cls.get("methods", []):
        calls = m.get("calls", [])
        resolved = [c for c in calls if c["confidence"] == 1.0]
        print(f"  │    {m['return_type']} {m['name']}()  "
              f"[{len(calls)} calls, {len(resolved)} resolved]")
        for c in resolved:
            print(f"  │      → {c['target']} (line {c['line']})")

# CALLS summary
all_calls = [
    c
    for cls in result.get("classes", [])
    for m in cls.get("methods", [])
    for c in m.get("calls", [])
]
resolved = [c for c in all_calls if c["confidence"] == 1.0]

print(f"\n  CALLS total   : {len(all_calls)}")
print(f"  CALLS resolved: {len(resolved)} (confidence 1.0)")

print("\n" + "=" * 60)
if resolved:
    print("✅ Iteration 13 complete — CALLS edges extracted")
else:
    print("⚠️  No resolved CALLS found — check field injection in controller")
print("=" * 60)
