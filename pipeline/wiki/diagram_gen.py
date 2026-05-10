import re


def _sanitize(text: str) -> str:
    """Remove characters that break Mermaid syntax."""
    if not text:
        return ""
    # Remove Java generics e.g. List<Pet> → List
    text = re.sub(r"<[^>]+>", "", text)
    # Remove special chars except letters, digits, underscore
    text = re.sub(r"[^a-zA-Z0-9_]", "_", text)
    return text.strip("_")


def _annotation_label(component_type: str) -> str:
    """Map component types to clean Mermaid stereotype labels."""
    mapping = {
        "REST_CONTROLLER": "Controller",
        "CONTROLLER":      "Controller",
        "SERVICE":         "Service",
        "REPOSITORY":      "Repository",
        "ENTITY":          "Entity",
        "COMPONENT":       "Component",
        "CONFIGURATION":   "Config",
        "CLASS":           "Class",
    }
    return mapping.get(component_type, "Class")


def generate_mermaid_diagram(
    classes: list[dict],
    relationships: list[dict]
) -> str:
    lines = ["classDiagram"]

    for cls in classes:
        safe_name = _sanitize(cls["name"])
        if not safe_name:
            continue

        lines.append(f'    class {safe_name}["'
                     f'{cls["name"]}"]')

        # Add stereotype annotation
        label = _annotation_label(cls["component_type"])
        lines.append(f"    <<{label}>> {safe_name}")

        # Fields — max 4, sanitized
        for field in cls.get("fields", [])[:4]:
            fname = _sanitize(field.get("name", ""))
            ftype = _sanitize(field.get("type", "Object"))
            if fname:
                lines.append(f"    {safe_name} : +{ftype} {fname}")

        # Methods — max 4, sanitized
        for method in cls.get("methods", [])[:4]:
            mname = _sanitize(method.get("name", ""))
            rtype = _sanitize(method.get("return_type", "void"))
            if mname:
                lines.append(f"    {safe_name} : +{mname}() {rtype}")

    # Relationships
    seen = set()
    for rel in relationships:
        src = _sanitize(rel.get("source", ""))
        tgt = _sanitize(rel.get("target", ""))
        if src and tgt and src != tgt:
            key = f"{src}-->{tgt}"
            if key not in seen:
                lines.append(f"    {src} --> {tgt}")
                seen.add(key)

    return "\n".join(lines)


def generate_wiki_page(cls: dict, summary: str) -> str:
    methods_rows = "\n".join(
        f"| `{m.get('name','')}` "
        f"| `{m.get('return_type','void')}` "
        f"| {', '.join(m.get('annotations',[]) or []) or '-'} |"
        for m in cls.get("methods", [])
    ) or "| - | - | - |"

    fields_rows = "\n".join(
        f"| `{f.get('name','')}` "
        f"| `{f.get('type','Object')}` "
        f"| {', '.join(f.get('annotations',[]) or []) or '-'} |"
        for f in cls.get("fields", [])
    ) or "| - | - | - |"

    return f"""# {cls['name']}

**Type:** `{cls['component_type']}`
**Package:** `{cls.get('package', '')}`
**Annotations:** {', '.join(cls.get('annotations', [])) or 'none'}

## Summary
{summary}

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
{methods_rows}

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
{fields_rows}
"""