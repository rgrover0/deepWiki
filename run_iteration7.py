import time
from pipeline.delta.git_monitor import (
    get_changed_java_files,
    extract_class_names_from_paths
)
from pipeline.delta.dependency_resolver import (
    get_affected_classes,
    get_class_details_from_neo4j
)
from pipeline.delta.updater import (
    update_neo4j_for_file,
    update_wiki_summary,
    update_qdrant_for_class,
    get_qdrant_id_for_class
)

REPO_PATH = "repos/spring-petclinic"

print("=" * 55)
print("DeepWiki — Iteration 7: Delta Update Pipeline")
print("=" * 55)

# 1. Detect changed files
print("\n🔍 Scanning for changes...")
changes = get_changed_java_files(REPO_PATH)

all_changed = changes["modified"] + changes["added"]
deleted     = changes["deleted"]

if not all_changed and not deleted:
    print("✅ No changes detected. Modify a Java file to test.")
    exit(0)

print(f"\n📝 Changes detected:")
for f in changes["modified"]:
    print(f"   Modified : {f.split('spring-petclinic')[-1]}")
for f in changes["added"]:
    print(f"   Added    : {f.split('spring-petclinic')[-1]}")
for f in changes["deleted"]:
    print(f"   Deleted  : {f.split('spring-petclinic')[-1]}")

# 2. Extract class names from changed files
changed_class_names = extract_class_names_from_paths(all_changed)
print(f"\n📦 Directly changed classes: {changed_class_names}")

# 3. Resolve dependency cone
print("\n🕸️  Resolving dependency cone...")
affected = get_affected_classes(changed_class_names)

print(f"   Direct    : {affected['direct']}")
print(f"   Dependents: {affected['dependents']}")
print(f"   Total affected: {len(affected['all'])} classes")

# 4. Update Neo4j for changed files
print("\n🔄 Updating Neo4j graph...")
updated_classes = []
for file_path in all_changed:
    print(f"   Re-analyzing: {file_path.split('spring-petclinic')[-1]}")
    updated = update_neo4j_for_file(file_path)
    updated_classes.extend(updated)
    print(f"   ✅ Updated: {updated}")

# 5. Fetch updated class details
print("\n📂 Fetching updated class details...")
classes_to_update = get_class_details_from_neo4j(list(affected["all"]))
print(f"✅ Fetched {len(classes_to_update)} class details")

# 6. Regenerate wiki summaries
print("\n🤖 Regenerating wiki summaries...")
for i, cls in enumerate(classes_to_update, 1):
    print(f"   [{i}/{len(classes_to_update)}] {cls['name']}...")
    summary = update_wiki_summary(cls)

    # Update Qdrant
    point_id = get_qdrant_id_for_class(cls["name"])
    update_qdrant_for_class(cls, summary, point_id)
    print(f"   ✅ Wiki + embeddings updated")

    if i < len(classes_to_update):
        time.sleep(2)  # Rate limit

# 7. Summary report
print("\n" + "=" * 55)
print("DELTA UPDATE REPORT")
print("=" * 55)
print(f"""
Files changed:         {len(all_changed)}
Classes directly changed:  {len(affected['direct'])}
Dependent classes updated: {len(affected['dependents'])}
Total classes updated:     {len(affected['all'])}

Classes NOT touched:   {18 - len(affected['all'])} (efficiency gain)

Updated wiki pages:
""")

for cls in classes_to_update:
    print(f"  ✅ output/wiki/{cls['name']}.md")

print(f"\n✅ Iteration 7 complete")
print(f"Next: Iteration 8 — Jira story → Implementation plan")