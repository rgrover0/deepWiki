import tree_sitter_java as tsjava
from tree_sitter import Language, Parser
from pathlib import Path

JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser(JAVA_LANGUAGE)

# Annotation → component type mapping
COMPONENT_MAP = {
    "@RestController": "REST_CONTROLLER",
    "@Controller":     "CONTROLLER",
    "@Service":        "SERVICE",
    "@Repository":     "REPOSITORY",
    "@Entity":         "ENTITY",
    "@Component":      "COMPONENT",
    "@Configuration":  "CONFIGURATION",
}


def _text(node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _get_annotations(node, source: bytes) -> list[str]:
    annotations = []
    for child in node.children:
        if child.type == "modifiers":
            for mod in child.children:
                if mod.type in ("marker_annotation", "annotation"):
                    annotations.append(_text(mod, source))
    return annotations


def _get_methods(class_body, source: bytes) -> list[dict]:
    methods = []
    for node in class_body.children:
        if node.type == "method_declaration":
            name = ""
            return_type = ""
            params = []
            annotations = _get_annotations(node, source)

            for child in node.children:
                if child.type == "identifier":
                    name = _text(child, source)
                elif child.type in (
                    "type_identifier", "integral_type",
                    "floating_point_type", "boolean_type",
                    "void_type", "generic_type", "array_type"
                ):
                    return_type = _text(child, source)
                elif child.type == "formal_parameters":
                    for param in child.children:
                        if param.type == "formal_parameter":
                            params.append(_text(param, source))

            if name:
                methods.append({
                    "name": name,
                    "return_type": return_type,
                    "parameters": params,
                    "annotations": annotations
                })
    return methods


def _get_fields(class_body, source: bytes) -> list[dict]:
    fields = []
    for node in class_body.children:
        if node.type == "field_declaration":
            field_type = ""
            field_name = ""
            annotations = _get_annotations(node, source)

            for child in node.children:
                if child.type in (
                    "type_identifier", "integral_type",
                    "generic_type", "array_type"
                ):
                    field_type = _text(child, source)
                elif child.type == "variable_declarator":
                    for sub in child.children:
                        if sub.type == "identifier":
                            field_name = _text(sub, source)

            if field_name:
                fields.append({
                    "name": field_name,
                    "type": field_type,
                    "annotations": annotations
                })
    return fields


def _get_imports(root, source: bytes) -> list[str]:
    imports = []
    for node in root.children:
        if node.type == "import_declaration":
            imports.append(_text(node, source).strip())
    return imports


def _get_package(root, source: bytes) -> str:
    for node in root.children:
        if node.type == "package_declaration":
            return _text(node, source).strip()
    return ""


def _determine_component_type(annotations: list[str]) -> str:
    for ann in annotations:
        for key, val in COMPONENT_MAP.items():
            if key in ann:
                return val
    return "CLASS"


def analyze_file(file_path: str) -> dict:
    """Parse a single Java file and extract structure."""
    source = Path(file_path).read_bytes()
    tree = parser.parse(source)
    root = tree.root_node

    result = {
        "file": file_path,
        "package": _get_package(root, source),
        "imports": _get_imports(root, source),
        "classes": []
    }

    for node in root.children:
        if node.type == "class_declaration":
            class_name = ""
            class_body = None
            annotations = _get_annotations(node, source)

            for child in node.children:
                if child.type == "identifier":
                    class_name = _text(child, source)
                elif child.type == "class_body":
                    class_body = child

            if class_name and class_body:
                result["classes"].append({
                    "name": class_name,
                    "component_type": _determine_component_type(annotations),
                    "annotations": annotations,
                    "methods": _get_methods(class_body, source),
                    "fields": _get_fields(class_body, source)
                })

    return result


def analyze_files(file_paths: list[str]) -> list[dict]:
    """Analyze multiple files. Skips files with parse errors."""
    results = []
    for path in file_paths:
        try:
            result = analyze_file(path)
            if result["classes"]:
                results.append(result)
        except Exception as e:
            print(f"⚠️  Skipped {path}: {e}")
    return results