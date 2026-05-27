"""
Nightly APIContractImpact job — updated Iteration 19.

For each APIContract, aggregates all CONSUMES edges (from any repo,
including Angular FE repos added in Iteration 19) into an
APIContractImpact node.
"""


def run_api_impact_nightly(driver) -> int:
    """
    Build/refresh APIContractImpact nodes from CONSUMES edges.
    Returns count of contracts processed.
    """
    with driver.session() as session:
        contracts = session.run(
            "MATCH (a:APIContract) RETURN a.id AS id"
        ).data()

        for row in contracts:
            api_id    = row["id"]
            impact_id = f"impact:{api_id}"

            consumers = session.run("""
                MATCH (r:Repository)-[c:CONSUMES]->(a:APIContract {id: $api_id})
                RETURN r.id              AS repo_id,
                       r.language        AS language,
                       c.confidence      AS confidence,
                       c.caller_class    AS caller_class,
                       c.caller_method   AS caller_method
            """, api_id=api_id).data()

            session.run("""
                MERGE (i:APIContractImpact {id: $impact_id})
                SET i.consumer_count  = $count,
                    i.consumer_repos  = $repos,
                    i.consumer_callers = $callers,
                    i.updated_at      = datetime()
                WITH i
                MATCH (a:APIContract {id: $api_id})
                MERGE (a)-[:HAS_IMPACT]->(i)
            """,
                impact_id=impact_id,
                api_id=api_id,
                count=len(consumers),
                repos=[c["repo_id"] for c in consumers],
                callers=[
                    f"{c['caller_class']}.{c['caller_method']}()"
                    for c in consumers
                    if c.get("caller_class")
                ],
            )

    return len(contracts)
