def write_package(session, package_name: str):
    if not package_name:
        return
    session.run(
        "MERGE (p:Package {name: $name})",
        name=package_name
    )


def write_class(session, cls: dict, package: str, file_path: str,
                repo_id: str, suite_id: str = ""):
    session.run("""
        MERGE (c:Class {repo_id: $repo_id, name: $name})
        SET c.component_type = $component_type,
            c.package        = $package,
            c.file           = $file,
            c.annotations    = $annotations,
            c.suite_id       = $suite_id
    """,
        repo_id=repo_id,
        name=cls["name"],
        component_type=cls["component_type"],
        package=package,
        file=file_path,
        annotations=cls["annotations"],
        suite_id=suite_id,
    )

    # Link class → package
    if package:
        session.run("""
            MATCH (c:Class {repo_id: $repo_id, name: $class_name})
            MATCH (p:Package {name: $package_name})
            MERGE (c)-[:IN_PACKAGE]->(p)
        """, repo_id=repo_id, class_name=cls["name"], package_name=package)

    # Link file → class
    session.run("""
        MERGE (f:JavaFile {repo_id: $repo_id, path: $path})
        WITH f
        MATCH (c:Class {repo_id: $repo_id, name: $class_name})
        MERGE (f)-[:CONTAINS]->(c)
    """, repo_id=repo_id, path=file_path, class_name=cls["name"])

    # Link repository → class explicitly for repo-scoped traversal/search
    session.run("""
        MATCH (r:Repository {id: $repo_id})
        MATCH (c:Class {repo_id: $repo_id, name: $class_name})
        MERGE (r)-[:HAS_CLASS]->(c)
    """, repo_id=repo_id, class_name=cls["name"])


def write_methods(session, cls: dict, repo_id: str):
    for method in cls["methods"]:
        method_id = f"{repo_id}:{cls['name']}.{method['name']}"

        session.run("""
    MERGE (m:Method {id: $id})
    SET m.name        = $name,
        m.return_type = $return_type,
        m.params      = $params,
        m.annotations = $annotations,
        m.repo_id     = $repo_id
""",
    id=method_id,
    name=method["name"],
    return_type=method.get("return_type", ""),
    params=method.get("parameters", []),
    annotations=method.get("annotations", []),
    repo_id=repo_id,
)

        session.run("""
            MATCH (c:Class {repo_id: $repo_id, name: $class_name})
            MATCH (m:Method {id: $method_id})
            MERGE (c)-[:HAS_METHOD]->(m)
        """, repo_id=repo_id, class_name=cls["name"], method_id=method_id)


def write_fields(session, cls: dict, repo_id: str):
    for field in cls["fields"]:
        field_id = f"{repo_id}:{cls['name']}.{field['name']}"

        session.run("""
            MERGE (f:Field {id: $id})
            SET f.name        = $name,
                f.type        = $type,
                f.annotations = $annotations,
                f.repo_id     = $repo_id
        """,
            id=field_id,
            name=field["name"],
            type=field.get("type", ""),
            annotations=field.get("annotations", []),
            repo_id=repo_id,
        )

        session.run("""
            MATCH (c:Class {repo_id: $repo_id, name: $class_name})
            MATCH (f:Field {id: $field_id})
            MERGE (c)-[:HAS_FIELD]->(f)
        """, repo_id=repo_id, class_name=cls["name"], field_id=field_id)


def write_dependencies(session, file_result: dict, repo_id: str):
    """Link classes based on field types matching known class names."""
    for cls in file_result["classes"]:
        for field in cls["fields"]:
            session.run("""
                MATCH (source:Class {repo_id: $repo_id, name: $source})
                MATCH (target:Class {repo_id: $repo_id, name: $target})
                WHERE source.name <> target.name
                MERGE (source)-[:DEPENDS_ON]->(target)
            """, repo_id=repo_id, source=cls["name"], target=field["type"])


def write_analysis(driver, results: list[dict],
                   repo_id: str = "spring-petclinic",
                   suite_id: str = ""):
    """Write all analysis results to Neo4j."""
    total_classes = 0
    total_methods = 0
    total_fields  = 0

    with driver.session() as session:
        session.run("""
            MERGE (r:Repository {id: $repo_id})
            ON CREATE SET r.name = $repo_id
            SET r.suite_id = coalesce($suite_id, r.suite_id)
        """, repo_id=repo_id, suite_id=suite_id or None)

        for file_result in results:
            package   = file_result.get("package", "")
            file_path = file_result.get("file", "")

            # Write file node
            session.run(
                """
                MERGE (f:JavaFile {repo_id: $repo_id, path: $path})
                SET f.package = $package,
                    f.suite_id = $suite_id
                """,
                repo_id=repo_id,
                path=file_path,
                package=package,
                suite_id=suite_id,
            )

            session.run("""
                MATCH (r:Repository {id: $repo_id})
                MATCH (f:JavaFile {repo_id: $repo_id, path: $path})
                MERGE (r)-[:HAS_FILE]->(f)
            """, repo_id=repo_id, path=file_path)

            write_package(session, package)

            for cls in file_result["classes"]:
                write_class(session, cls, package, file_path, repo_id, suite_id)
                write_methods(session, cls, repo_id)
                write_fields(session, cls, repo_id)
                total_classes += 1
                total_methods += len(cls["methods"])
                total_fields  += len(cls["fields"])

        # Second pass — write dependencies
        for file_result in results:
            write_dependencies(session, file_result, repo_id)

    return {
        "classes": total_classes,
        "methods": total_methods,
        "fields":  total_fields
    }