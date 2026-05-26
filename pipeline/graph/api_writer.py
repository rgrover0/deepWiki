"""
APIContract graph writer — Iteration 15.

Creates:
  (Repository {id})  -[:EXPOSES]->           (APIContract)
  (Class)            -[:IMPLEMENTS_CONTRACT]->(APIContract)
"""


def _contract_id(repo_id: str, http_method: str, path: str) -> str:
    return f"{repo_id}:{http_method}:{path}"


def ensure_repository_node(session, repo_id: str = "spring-petclinic",
                            repo_name: str = "Spring PetClinic"):
    session.run("""
        MERGE (r:Repository {id: $id})
        SET r.name      = $name,
            r.language  = 'java',
            r.framework = 'spring-boot'
    """, id=repo_id, name=repo_name)


def write_api_contract(session, contract: dict, repo_id: str):
    cid = _contract_id(repo_id, contract["http_method"], contract["path"])
    session.run("""
        MERGE (a:APIContract {id: $id})
        SET a.http_method        = $http_method,
            a.path               = $path,
            a.path_variables     = $path_variables,
            a.return_type        = $return_type,
            a.controller_method  = $controller_method,
            a.controller_class   = $controller_class,
            a.request_body_type  = $request_body_type
    """,
        id=cid,
        http_method=contract["http_method"],
        path=contract["path"],
        path_variables=contract.get("path_variables", []),
        return_type=contract.get("return_type", ""),
        controller_method=contract.get("controller_method", ""),
        controller_class=contract.get("controller_class", ""),
        request_body_type=contract.get("request_body_type"),
    )
    session.run("""
        MATCH (r:Repository {id: $repo_id})
        MATCH (a:APIContract {id: $cid})
        MERGE (r)-[:EXPOSES]->(a)
    """, repo_id=repo_id, cid=cid)
    # Link to implementing controller class
    if contract.get("controller_class"):
        session.run("""
            MATCH (c:Class {name: $cls})
            MATCH (a:APIContract {id: $cid})
            MERGE (c)-[:IMPLEMENTS_CONTRACT]->(a)
        """, cls=contract["controller_class"], cid=cid)


def write_all_api_contracts(driver, analysis_results: list[dict],
                             repo_id: str = "spring-petclinic") -> int:
    total = 0
    with driver.session() as session:
        ensure_repository_node(session, repo_id)
        for file_result in analysis_results:
            for cls in file_result.get("classes", []):
                for contract in cls.get("api_contracts", []):
                    write_api_contract(session, contract, repo_id)
                    total += 1
    return total
