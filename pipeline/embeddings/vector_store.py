import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    PointStruct, Filter,
    FieldCondition, MatchValue
)
from dotenv import load_dotenv

load_dotenv()

COLLECTION   = "deepwiki_classes"
VECTOR_SIZE  = 384  # all-MiniLM-L6-v2 output size


def get_client() -> QdrantClient:
    """Supports both local Podman and Qdrant Cloud."""
    url     = os.getenv("QDRANT_HOST")
    api_key = os.getenv("QDRANT_API_KEY")

    if url and api_key:
        # Qdrant Cloud
        qdrant_client = QdrantClient(url=url, api_key=api_key)
        print(qdrant_client.get_collections())
        return qdrant_client
    else:
        # Local Podman/Docker fallback
        qdrant_client_local = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        print(qdrant_client_local.get_collections())
        return qdrant_client_local


def setup_collection(client: QdrantClient):
    """Create collection if not exists."""
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
        print(f"🗑️  Deleted existing collection: {COLLECTION}")

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )
    print(f"✅ Created collection: {COLLECTION}")


def store_class_embeddings(
    client: QdrantClient,
    classes: list[dict],
    embeddings: list[list[float]]
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
                "method_names": [
                    m["name"] for m in cls.get("methods", [])
                ],
                "field_names": [
                    f["name"] for f in cls.get("fields", [])
                ]
            }
        ))

    client.upsert(collection_name=COLLECTION, points=points)
    print(f"✅ Stored {len(points)} class embeddings")


def semantic_search(
    client: QdrantClient,
    query_vector: list[float],
    top_k: int = 5,
    component_type: str = None
) -> list[dict]:
    """Search for similar classes by vector similarity."""

    search_filter = None
    if component_type:
        search_filter = Filter(
            must=[FieldCondition(
                key="component_type",
                match=MatchValue(value=component_type)
            )]
        )

    results = client.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        limit=top_k,
        query_filter=search_filter,
        with_payload=True
    ).points

    return [
        {
            "name":           r.payload["name"],
            "component_type": r.payload["component_type"],
            "package":        r.payload["package"],
            "methods":        r.payload["method_names"],
            "score":          round(r.score, 4)
        }
        for r in results
    ]