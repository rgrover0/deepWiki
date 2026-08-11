import json
import os
from collections import Counter
from pipeline.ingestion.git_reader import clone_repo, get_java_files, get_repo_metadata
from pipeline.ingestion.static_analysis import analyze_files

REPO_URL = "https://github.com/spring-projects/spring-petclinic"
REPO_DIR = "repos/spring-petclinic"
OUTPUT_FILE = "output/analysis.json"

os.makedirs("repos", exist_ok=True)
os.makedirs("output", exist_ok=True)

print("=" * 50)
print("DeepWiki — Iteration 2: Static Analysis")
print("=" * 50)

# 1. Clone repo
clone_repo(REPO_URL, REPO_DIR)

# 2. Get metadata
meta = get_repo_metadata(REPO_DIR)
print(f"\n📁 Repo: {meta['path']}")
print(f"🌿 Branch: {meta['branch']}")
print(f"📝 Last commit: {meta['last_commit']} — {meta['last_commit_message']}")

# 3. Get Java files
java_files = get_java_files(REPO_DIR)
print(f"\n📄 Found {len(java_files)} Java files (excluding tests)")

# 4. Run static analysis
print("\n🔍 Running static analysis...")
results = analyze_files(java_files)
print(f"✅ Analyzed {len(results)} files with classes")

# 5. Save output
with open(OUTPUT_FILE, "w") as f:
    json.dump(results, f, indent=2)
print(f"\n💾 Saved to {OUTPUT_FILE}")

# 6. Print summary
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)

all_classes = []
for r in results:
    for cls in r["classes"]:
        all_classes.append(cls)

component_counts = Counter(c["component_type"] for c in all_classes)
print(f"\n📦 Total classes found: {len(all_classes)}")
print("\nComponent breakdown:")
for comp_type, count in component_counts.most_common():
    print(f"  {comp_type:20s}: {count}")

print("\n📋 Classes found:")
for r in results:
    for cls in r["classes"]:
        file_name = os.path.basename(r["file"])
        methods = len(cls["methods"])
        fields = len(cls["fields"])
        print(f"  [{cls['component_type']:18s}] {cls['name']:30s} "
              f"| {methods} methods | {fields} fields")