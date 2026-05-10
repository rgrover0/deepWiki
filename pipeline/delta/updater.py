import os
import time
from pipeline.ingestion.static_analysis import analyze_file
from pipeline.graph.schema import get_driver
from pipeline.graph.writer import (
    write_class, write_methods, write_fields,
    write_package, write_dependencies
)
from pipeline.wiki.summarizer import summarize_class
from pipeline.wiki.diagram_gen import generate_wiki_page
from pipeline.embeddings.embedder import embed_text, build_class_text
from pipeline.embeddings.vector_store import get_client, COLLECTION
from qdrant_client.models import PointStruct


def update_neo4j_for_file(file_path: str) -> list[str]:
    """
    Re-analyze a changed file and update Neo4j.
    Returns list of updated class names.
    """
    result = analyze_file(file_path)
    if not result["classes"]:
        return []

    driver = get_driver()
    updated = []

    with driver.session() as session:
        package   = result.get("package", "")
        write_package(session, package)

        for cls in result["classes"]:
            # Remove old methods and fields before rewriting
            session.run("""
                MATCH (c:Class {name: $name})-[:HAS_METHOD]->(m:Method)
                DETACH DELETE m
            """, name=cls["name"])

            session.run("""
                MATCH (c:Class {name: $name})-[:HAS_FIELD]->(f:Field)
                DETACH DELETE f
            """, name=cls["name"])

            # Rewrite with fresh data
            write_class(session, cls, package, file_path)
            write_methods(session, cls)
            write_fields(session, cls)
            updated.append(cls["name"])

        write_dependencies(session, result)

    driver.close()
    return updated


def update_wiki_summary(cls: dict) -> str:
    """Regenerate LLM summary for a class."""
    summary = summarize_class(cls)

    driver = get_driver()
    with driver.session() as session:
        session.run(
            "MATCH (c:Class {name: $name}) SET c.wiki_summary = $summary",
            name=cls["name"], summary=summary
        )
    driver.close()

    # Regenerate wiki page file
    os.makedirs("output/wiki", exist_ok=True)
    page = generate_wiki_page(cls, summary)
    with open(f"output/wiki/{cls['name']}.md", "w", encoding="utf-8") as f:
        f.write(page)

    return summary


def update_qdrant_for_class(cls: dict, summary: str, point_id: int):
    """Update Qdrant embedding for a single class."""
    enriched_text = (
        f"{cls['name']}: {summary} "
        f"Methods: {', '.join(m['name'] for m in cls.get('methods', []))}. "
        f"Fields: {', '.join(f['name'] for f in cls.get('fields', []))}."
    )

    vector = embed_text(enriched_text)
    qdrant = get_client()

    qdrant.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "name":           cls["name"],
                "component_type": cls["component_type"],
                "package":        cls.get("package", ""),
                "file":           cls.get("file", ""),
                "annotations":    cls.get("annotations", []),
                "method_names":   [m["name"] for m in cls.get("methods", [])],
                "field_names":    [f["name"] for f in cls.get("fields", [])]
            }
        )]
    )


def get_qdrant_id_for_class(class_name: str) -> int:
    """Get existing Qdrant point ID for a class, or assign a new one."""
    qdrant = get_client()
    results = qdrant.scroll(
        collection_name=COLLECTION,
        scroll_filter=None,
        limit=100,
        with_payload=True
    )[0]

    for point in results:
        if point.payload.get("name") == class_name:
            return point.id

    # New class — use next available ID
    return len(results) + 1