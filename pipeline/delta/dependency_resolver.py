from pipeline.graph.schema import get_driver


def get_affected_classes(changed_class_names: list[str]) -> dict:
    """
    Given changed class names, find all affected classes:
    - The changed classes themselves
    - Classes that DEPEND_ON the changed classes (dependents)
    Returns dict with direct and dependent class names.
    """
    driver = get_driver()
    affected = {
        "direct":     set(changed_class_names),
        "dependents": set()
    }

    with driver.session() as session:
        for name in changed_class_names:
            # Find classes that depend on this class
            result = session.run("""
                MATCH (dependent:Class)-[:DEPENDS_ON]->(changed:Class {name: $name})
                RETURN dependent.name AS name
            """, name=name)

            for row in result:
                affected["dependents"].add(row["name"])

            # Find classes this class depends on (for context)
            result2 = session.run("""
                MATCH (changed:Class {name: $name})-[:DEPENDS_ON]->(dep:Class)
                RETURN dep.name AS name
            """, name=name)

            for row in result2:
                affected["dependents"].add(row["name"])

    driver.close()

    # Remove direct from dependents to keep sets clean
    affected["dependents"] -= affected["direct"]
    affected["all"] = affected["direct"] | affected["dependents"]

    return {k: list(v) for k, v in affected.items()}


def get_class_details_from_neo4j(class_names: list[str]) -> list[dict]:
    """Fetch full class details from Neo4j for re-summarization."""
    driver = get_driver()
    classes = []

    with driver.session() as session:
        for name in class_names:
            result = session.run("""
                MATCH (c:Class {name: $name})
                OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
                OPTIONAL MATCH (c)-[:HAS_FIELD]->(f:Field)
                RETURN
                    c.name           AS name,
                    c.component_type AS component_type,
                    c.package        AS package,
                    c.file           AS file,
                    c.annotations    AS annotations,
                    collect(DISTINCT {
                        name: m.name,
                        return_type: m.return_type,
                        params: m.params,
                        annotations: m.annotations
                    }) AS methods,
                    collect(DISTINCT {
                        name: f.name,
                        type: f.type,
                        annotations: f.annotations
                    }) AS fields
            """, name=name).single()

            if result:
                data = dict(result)
                data["methods"] = [
                    m for m in data["methods"] if m["name"]
                ]
                data["fields"] = [
                    f for f in data["fields"] if f["name"]
                ]
                classes.append(data)

    driver.close()
    return classes