from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"  # 80MB, fast on CPU, 384 dimensions
_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"📥 Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        print("✅ Model loaded")
    return _model


def embed_text(text: str) -> list[float]:
    model = get_model()
    return model.encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    model = get_model()
    return model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    ).tolist()


def build_class_text(cls: dict) -> str:
    """Build searchable text description for a class."""
    method_names = ", ".join(
        m["name"] for m in cls.get("methods", [])
    ) or "none"

    field_names = ", ".join(
        f"{f['name']} ({f['type']})" for f in cls.get("fields", [])
    ) or "none"

    annotations = ", ".join(cls.get("annotations", [])) or "none"

    return (
        f"Class: {cls['name']}. "
        f"Type: {cls['component_type']}. "
        f"Package: {cls.get('package', '')}. "
        f"Annotations: {annotations}. "
        f"Methods: {method_names}. "
        f"Fields: {field_names}."
    )