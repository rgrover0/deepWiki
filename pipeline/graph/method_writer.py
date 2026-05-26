"""
Method-level Neo4j writer — Iteration 14.

Writes:
  - logic_summary onto Method nodes
  - (Method)-[:CALLS {line, confidence}]->(Method)  edges
  - (Class)-[:EXTENDS]->(Class)                      edges
  - (Class)-[:IMPLEMENTS_INTERFACE]->(Interface)     edges

READS/WRITES field-access edges are deferred — JavaParser service
does not yet return field-access expressions.
"""


def _mid(class_name: str, method_name: str) -> str:
    return f"{class_name}.{method_name}"


def update_method_logic(session, cls_name: str, method: dict, logic_summary: str):
    session.run("""
        MERGE (m:Method {id: $id})
        SET m.name          = $name,
            m.return_type   = $return_type,
            m.params        = $params,
            m.annotations   = $annotations,
            m.logic_summary = $logic_summary
    """,
        id=_mid(cls_name, method["name"]),
        name=method["name"],
        return_type=method.get("return_type", ""),
        params=method.get("parameters", []),
        annotations=method.get("annotations", []),
        logic_summary=logic_summary,
    )
    session.run("""
        MATCH (c:Class {name: $cls})
        MATCH (m:Method {id: $mid})
        MERGE (c)-[:HAS_METHOD]->(m)
    """, cls=cls_name, mid=_mid(cls_name, method["name"]))


def write_calls_edges(session, cls_name: str, methods: list[dict]):
    for method in methods:
        src_id = _mid(cls_name, method["name"])
        for call in method.get("calls", []):
            target = call.get("target", "")
            if "." not in target:
                continue  # bare internal call — can't resolve to a Method node
            target_class, _, target_method = target.partition(".")
            tgt_id = _mid(target_class, target_method)
            # MERGE target node so it exists even before its class is processed
            session.run("""
                MERGE (t:Method {id: $tgt_id})
                ON CREATE SET t.name = $tgt_method
            """, tgt_id=tgt_id, tgt_method=target_method)
            session.run("""
                MATCH (src:Method {id: $src_id})
                MATCH (tgt:Method {id: $tgt_id})
                MERGE (src)-[r:CALLS {line: $line}]->(tgt)
                SET r.confidence = $confidence
            """,
                src_id=src_id,
                tgt_id=tgt_id,
                line=call.get("line", 0),
                confidence=call.get("confidence", 0.5),
            )


def write_hierarchy_edges(session, cls: dict):
    cls_name = cls["name"]
    if cls.get("extends"):
        session.run("""
            MERGE (parent:Class {name: $parent})
            WITH parent
            MATCH (child:Class {name: $child})
            MERGE (child)-[:EXTENDS]->(parent)
        """, parent=cls["extends"], child=cls_name)

    for iface in cls.get("implements", []):
        session.run("""
            MERGE (i:Interface {name: $iface})
            WITH i
            MATCH (c:Class {name: $cls})
            MERGE (c)-[:IMPLEMENTS_INTERFACE]->(i)
        """, iface=iface, cls=cls_name)


def write_all_method_data(driver, analysis_results: list[dict],
                          method_summaries: dict[str, dict[str, str]]) -> dict:
    """
    analysis_results  — list of file dicts from java_analysis_client
    method_summaries  — {class_name: {method_name: logic_summary}}
    Returns counts dict.
    """
    logic_written = 0
    calls_written = 0

    with driver.session() as session:
        for file_result in analysis_results:
            for cls in file_result.get("classes", []):
                cls_name    = cls["name"]
                cls_methods = cls.get("methods", [])
                summaries   = method_summaries.get(cls_name, {})

                for method in cls_methods:
                    logic = summaries.get(method["name"], "")
                    update_method_logic(session, cls_name, method, logic)
                    if logic:
                        logic_written += 1

                write_calls_edges(session, cls_name, cls_methods)
                calls_written += sum(
                    len(m.get("calls", [])) for m in cls_methods
                )
                write_hierarchy_edges(session, cls)

    return {"logic_written": logic_written, "calls_attempted": calls_written}
