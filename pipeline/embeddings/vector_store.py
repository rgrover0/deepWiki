import os
import zlib
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance, VectorParams,
    PointStruct, Filter,
    FieldCondition, MatchValue,
    PayloadSchemaType,
)
from dotenv import load_dotenv

load_dotenv()

COLLECTION  = "deepwiki_code_units"   # primary code collection (classes + methods)
VECTOR_SIZE = 384                      # all-MiniLM-L6-v2

ALL_COLLECTIONS = [
    "deepwiki_code_units",
    "deepwiki_api_contracts",
    "deepwiki_confluence_meeting_notes",
    "deepwiki_confluence_api_docs",
    "deepwiki_confluence_architecture",
    "deepwiki_confluence_general",
    "deepwiki_transcripts",
    "deepwiki_timeline",
]

# Fields used by filters in semantic/confluence search. Keep as keyword indexes.
FILTER_INDEXES = {
    "deepwiki_code_units": ["repo_id", "suite_id", "component_type", "unit_type", "class_name", "name"],
    "deepwiki_api_contracts": ["repo_id", "suite_id", "method", "endpoint"],
    "deepwiki_confluence_meeting_notes": ["suite_id", "content_type", "title"],
    "deepwiki_confluence_api_docs": ["suite_id", "content_type", "title"],
    "deepwiki_confluence_architecture": ["suite_id", "content_type", "title"],
    "deepwiki_confluence_general": ["suite_id", "content_type", "title"],
}


def get_client() -> QdrantClient:
    url     = os.getenv("QDRANT_HOST")
    api_key = os.getenv("QDRANT_API_KEY")

    if url and api_key:
        qdrant_client = QdrantClient(url=url, api_key=api_key)
        print(qdrant_client.get_collections())
        return qdrant_client
    else:
        qdrant_client_local = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        print(qdrant_client_local.get_collections())
        return qdrant_client_local


def setup_collection(client: QdrantClient):
    """Recreate the primary code-units collection (drops existing data)."""
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
        print(f"🗑️  Deleted existing collection: {COLLECTION}")

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )
    print(f"✅ Created collection: {COLLECTION}")


def setup_all_collections(client: QdrantClient):
    """Create all 8 fixed collections if they don't already exist."""
    existing = {c.name for c in client.get_collections().collections}

    for name in ALL_COLLECTIONS:
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
            print(f"✅ Created collection: {name}")
        else:
            print(f"   Already exists:    {name}")

    ensure_filter_indexes(client)


def ensure_required_collections(client: QdrantClient) -> None:
    """Idempotent guard for workflows that may run before startup bootstrap."""
    setup_all_collections(client)


def ensure_filter_indexes(client: QdrantClient) -> None:
    """Ensure payload indexes exist for fields used in filters."""
    existing = {c.name for c in client.get_collections().collections}
    for collection_name, fields in FILTER_INDEXES.items():
        if collection_name not in existing:
            continue
        for field in fields:
            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception as exc:
                # Safe to continue: index may already exist or backend may reject duplicates.
                print(f"Index ensure skipped for {collection_name}.{field}: {exc}")


def migrate_from_legacy(client: QdrantClient, legacy_name: str = "deepwiki_classes",
                        repo_id: str = "spring-petclinic"):
    """
    Copy all points from the old per-collection design into deepwiki_code_units,
    adding repo_id and unit_type to each payload. Deletes the legacy collection
    on completion.
    """
    existing = {c.name for c in client.get_collections().collections}
    if legacy_name not in existing:
        print(f"   No legacy collection '{legacy_name}' found — skipping migration.")
        return

    offset = None
    migrated = 0

    while True:
        batch, next_offset = client.scroll(
            collection_name=legacy_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        if not batch:
            break

        points = []
        for p in batch:
            payload = dict(p.payload)
            payload.setdefault("repo_id", repo_id)
            payload.setdefault("unit_type", "class")
            points.append(PointStruct(id=p.id, vector=p.vector, payload=payload))

        client.upsert(collection_name=COLLECTION, points=points)
        migrated += len(points)

        if next_offset is None:
            break
        offset = next_offset

    client.delete_collection(legacy_name)
    print(f"✅ Migrated {migrated} points from '{legacy_name}' → '{COLLECTION}'")
    print(f"🗑️  Deleted legacy collection: {legacy_name}")


def store_class_embeddings(
    client: QdrantClient,
    classes: list[dict],
    embeddings: list[list[float]],
    repo_id: str = "spring-petclinic",
    suite_id: str = "pet-management-platform",
):
    """Store class embeddings with metadata as payload."""
    points = []
    for idx, (cls, vector) in enumerate(zip(classes, embeddings)):
        points.append(PointStruct(
            id=idx,
            vector=vector,
            payload={
                "name":           cls["name"],
                "component_type": cls["component_type"],
                "package":        cls.get("package", ""),
                "file":           cls.get("file", ""),
                "annotations":    cls.get("annotations", []),
                "method_names":   [m["name"] for m in cls.get("methods", [])],
                "field_names":    [f["name"] for f in cls.get("fields", [])],
                "repo_id":        repo_id,
                "suite_id":       suite_id,
                "unit_type":      "class",
            }
        ))

    client.upsert(collection_name=COLLECTION, points=points)
    print(f"✅ Stored {len(points)} class embeddings")


def store_method_embeddings(
    client: QdrantClient,
    method_data: list[dict],
    embeddings: list[list[float]],
    repo_id: str = "spring-petclinic",
    suite_id: str = "pet-management-platform",
):
    """Store method-level embeddings in deepwiki_code_units.

    method_data items: {cls_name, method (dict), logic_summary (str)}
    IDs are stable CRC32 hashes — collision-safe at petclinic scale.
    """
    points = []
    for m_data, vector in zip(method_data, embeddings):
        cls_name = m_data["cls_name"]
        method   = m_data["method"]
        point_id = zlib.crc32(f"m:{cls_name}.{method['name']}".encode()) & 0x7FFFFFFF

        points.append(PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "name":          method["name"],
                "class_name":    cls_name,
                "return_type":   method.get("return_type", ""),
                "annotations":   method.get("annotations", []),
                "logic_summary": m_data.get("logic_summary", ""),
                "repo_id":       repo_id,
                "suite_id":      suite_id,
                "unit_type":     "method",
            }
        ))

    client.upsert(collection_name=COLLECTION, points=points)
    print(f"Stored {len(points)} method embeddings")


def semantic_search(
    client: QdrantClient,
    query_vector: list[float],
    top_k: int = 5,
    component_type: str = None,
    repo_id: str = None,
    suite_id: str = None,
    unit_type: str = None,
) -> list[dict]:
    """Search code units by vector similarity. Returns classes or methods."""
    must_conditions = []

    if component_type:
        must_conditions.append(FieldCondition(
            key="component_type",
            match=MatchValue(value=component_type)
        ))
    if repo_id:
        must_conditions.append(FieldCondition(
            key="repo_id",
            match=MatchValue(value=repo_id)
        ))
    if suite_id:
        must_conditions.append(FieldCondition(
            key="suite_id",
            match=MatchValue(value=suite_id)
        ))
    if unit_type:
        must_conditions.append(FieldCondition(
            key="unit_type",
            match=MatchValue(value=unit_type)
        ))

    search_filter = Filter(must=must_conditions) if must_conditions else None

    try:
        results = client.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            limit=top_k,
            query_filter=search_filter,
            with_payload=True,
        ).points
    except UnexpectedResponse as exc:
        error_text = str(exc).lower()
        if "index required" in error_text or "doesn't exist" in error_text or "not found" in error_text:
            # Self-heal older/missing collections for local cold starts.
            ensure_required_collections(client)
            results = client.query_points(
                collection_name=COLLECTION,
                query=query_vector,
                limit=top_k,
                query_filter=search_filter,
                with_payload=True,
            ).points
        else:
            raise

    return [
        {
            "name":          r.payload.get("name", ""),
            "repo_id":       r.payload.get("repo_id", ""),
            "suite_id":      r.payload.get("suite_id", ""),
            "component_type": r.payload.get("component_type", ""),
            "package":       r.payload.get("package", ""),
            "methods":       r.payload.get("method_names", []),
            "unit_type":     r.payload.get("unit_type", "class"),
            "class_name":    r.payload.get("class_name", ""),
            "logic_summary": r.payload.get("logic_summary", ""),
            "score":         round(r.score, 4),
        }
        for r in results
    ]
