"""
Nightly APIContractImpact job — Iteration 15.

For each APIContract, aggregates all CONSUMES edges into an
APIContractImpact node. No Angular repos exist yet (Iteration 19),
so this job pre-creates empty impact nodes ready for future use.
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
                RETURN r.id AS repo_id, c.confidence AS confidence,
                       c.caller_class AS caller_class
            """, api_id=api_id).data()

            session.run("""
                MERGE (i:APIContractImpact {id: $impact_id})
                SET i.consumer_count = $count,
                    i.consumer_repos = $repos,
                    i.updated_at     = datetime()
                WITH i
                MATCH (a:APIContract {id: $api_id})
                MERGE (a)-[:HAS_IMPACT]->(i)
            """,
                impact_id=impact_id,
                api_id=api_id,
                count=len(consumers),
                repos=[c["repo_id"] for c in consumers],
            )

    return len(contracts)
