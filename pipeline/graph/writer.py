def write_package(session, package_name: str):
    if not package_name:
        return
    session.run(
        "MERGE (p:Package {name: $name})",
        name=package_name
    )


def write_class(session, cls: dict, package: str, file_path: str):
    session.run("""
        MERGE (c:Class {name: $name})
        SET c.component_type = $component_type,
            c.package        = $package,
            c.file           = $file,
            c.annotations    = $annotations
    """,
        name=cls["name"],
        component_type=cls["component_type"],
        package=package,
        file=file_path,
        annotations=cls["annotations"]
    )

    # Link class → package
    if package:
        session.run("""
            MATCH (c:Class {name: $class_name})
            MATCH (p:Package {name: $package_name})
            MERGE (c)-[:IN_PACKAGE]->(p)
        """, class_name=cls["name"], package_name=package)

    # Link file → class
    session.run("""
        MERGE (f:JavaFile {path: $path})
        WITH f
        MATCH (c:Class {name: $class_name})
        MERGE (f)-[:CONTAINS]->(c)
    """, path=file_path, class_name=cls["name"])


def write_methods(session, cls: dict):
    for method in cls["methods"]:
        method_id = f"{cls['name']}.{method['name']}"

        session.run("""
    MERGE (m:Method {id: $id})
    SET m.name        = $name,
        m.return_type = $return_type,
        m.params      = $params,
        m.annotations = $annotations
""",
    id=method_id,
    name=method["name"],
    return_type=method.get("return_type", ""),
    params=method.get("parameters", []),
    annotations=method.get("annotations", [])
)

        session.run("""
            MATCH (c:Class {name: $class_name})
            MATCH (m:Method {id: $method_id})
            MERGE (c)-[:HAS_METHOD]->(m)
        """, class_name=cls["name"], method_id=method_id)


def write_fields(session, cls: dict):
    for field in cls["fields"]:
        field_id = f"{cls['name']}.{field['name']}"

        session.run("""
            MERGE (f:Field {id: $id})
            SET f.name        = $name,
                f.type        = $type,
                f.annotations = $annotations
        """,
            id=field_id,
            name=field["name"],
            type=field.get("type", ""),
            annotations=field.get("annotations", [])
        )

        session.run("""
            MATCH (c:Class {name: $class_name})
            MATCH (f:Field {id: $field_id})
            MERGE (c)-[:HAS_FIELD]->(f)
        """, class_name=cls["name"], field_id=field_id)


def write_dependencies(session, file_result: dict):
    """Link classes based on field types matching known class names."""
    for cls in file_result["classes"]:
        for field in cls["fields"]:
            session.run("""
                MATCH (source:Class {name: $source})
                MATCH (target:Class {name: $target})
                WHERE source.name <> target.name
                MERGE (source)-[:DEPENDS_ON]->(target)
            """, source=cls["name"], target=field["type"])


def write_analysis(driver, results: list[dict]):
    """Write all analysis results to Neo4j."""
    total_classes = 0
    total_methods = 0
    total_fields  = 0

    with driver.session() as session:
        for file_result in results:
            package   = file_result.get("package", "")
            file_path = file_result.get("file", "")

            # Write file node
            session.run(
                "MERGE (f:JavaFile {path: $path}) SET f.package = $package",
                path=file_path, package=package
            )

            write_package(session, package)

            for cls in file_result["classes"]:
                write_class(session, cls, package, file_path)
                write_methods(session, cls)
                write_fields(session, cls)
                total_classes += 1
                total_methods += len(cls["methods"])
                total_fields  += len(cls["fields"])

        # Second pass — write dependencies
        for file_result in results:
            write_dependencies(session, file_result)

    return {
        "classes": total_classes,
        "methods": total_methods,
        "fields":  total_fields
    }