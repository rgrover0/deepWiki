import os
import json
import time
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

METHOD_CACHE_FILE = Path("output/cache/method_logic_cache.json")

METHOD_LOGIC_PROMPT = """You are a code documentation expert.

Write a 2-3 sentence logic_summary for this Java method.
Focus on WHAT it does and its business purpose, not implementation details.

Class: {class_name} — {class_wiki_summary}
Method: {return_type} {method_name}({params})
Annotations: {annotations}
Calls: {calls}

Rules:
- State the method's purpose clearly
- Name the key services or repositories it uses if relevant
- Under 60 words, no bullet points
"""

SUMMARIZE_PROMPT = """You are a technical documentation expert analyzing a Java Spring Boot application.

Generate a concise wiki summary for this Java class based on the details below.

Class: {name}
Type: {component_type}
Package: {package}
Annotations: {annotations}
Methods: {methods}
Fields: {fields}

Write a clear 3-5 sentence wiki entry covering:
1. What this class does and its responsibility
2. Its role in the application architecture
3. Key methods and their purpose
4. Important fields or dependencies

Rules:
- Be technical but clear
- No bullet points — write flowing sentences
- Do not repeat the class name more than twice
- Maximum 150 words
"""


def build_prompt(cls: dict) -> str:
    methods = ", ".join(
        f"{m['name']}({m.get('return_type', '')})"
        for m in cls.get("methods", [])[:10]
    ) or "none"

    fields = ", ".join(
        f"{f['name']}: {f.get('type', '')}"
        for f in cls.get("fields", [])[:8]
    ) or "none"

    annotations = ", ".join(cls.get("annotations", [])) or "none"

    return SUMMARIZE_PROMPT.format(
        name=cls["name"],
        component_type=cls["component_type"],
        package=cls.get("package", ""),
        annotations=annotations,
        methods=methods,
        fields=fields
    )


def summarize_class(cls: dict, retries: int = 3) -> str:
    prompt = build_prompt(cls)

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            error = str(e)
            if "rate_limit" in error.lower() or "429" in error:
                wait = (attempt + 1) * 15
                print(f"   ⏳ Rate limited — waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"   ⚠️  Error: {error}")
                return f"Wiki summary unavailable for {cls['name']}."

    return f"Wiki summary unavailable for {cls['name']}."


def _load_method_cache() -> dict:
    if METHOD_CACHE_FILE.exists():
        return json.loads(METHOD_CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def _save_method_cache(cache: dict):
    METHOD_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    METHOD_CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def is_trivial_method(method: dict) -> bool:
    """True for getters, setters, and is-prefixed accessors with minimal logic."""
    name   = method.get("name", "")
    params = method.get("parameters", [])
    calls  = method.get("calls", [])
    return (
        name.startswith(("get", "set", "is"))
        and len(params) <= 1
        and len(calls) <= 1
    )


def summarize_method(cls_name: str, cls_wiki: str, method: dict,
                     cache: dict, retries: int = 3) -> str:
    cache_key = f"{cls_name}.{method['name']}"
    if cache_key in cache:
        return cache[cache_key]

    params = ", ".join(method.get("parameters", [])) or "none"
    annotations = ", ".join(method.get("annotations", [])) or "none"
    calls_str = ", ".join(
        c["target"] for c in method.get("calls", []) if c.get("confidence", 0) >= 1.0
    ) or "none"

    prompt = METHOD_LOGIC_PROMPT.format(
        class_name=cls_name,
        class_wiki_summary=(cls_wiki or "")[:200],
        return_type=method.get("return_type", "void"),
        method_name=method["name"],
        params=params,
        annotations=annotations,
        calls=calls_str,
    )

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3,
            )
            summary = response.choices[0].message.content.strip()
            cache[cache_key] = summary
            return summary
        except Exception as e:
            error = str(e)
            if "rate_limit" in error.lower() or "429" in error:
                wait = (attempt + 1) * 15
                print(f"   Rate limited — waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"   Warning: {error}")
                return f"Logic summary unavailable for {method['name']}."

    return f"Logic summary unavailable for {method['name']}."


def summarize_methods(cls: dict, cls_wiki: str,
                      delay: float = 0.5) -> dict[str, str]:
    """Generate logic_summary for every non-trivial method in cls.
    Returns {method_name: logic_summary}. Results are cached to disk."""
    cache = _load_method_cache()
    summaries: dict[str, str] = {}

    non_trivial = [m for m in cls.get("methods", []) if not is_trivial_method(m)]
    trivial     = [m for m in cls.get("methods", []) if is_trivial_method(m)]

    for method in trivial:
        summaries[method["name"]] = ""

    for i, method in enumerate(non_trivial):
        summaries[method["name"]] = summarize_method(
            cls["name"], cls_wiki, method, cache
        )
        _save_method_cache(cache)
        if i < len(non_trivial) - 1:
            time.sleep(delay)

    return summaries


def summarize_all(classes: list[dict], delay: float = 2.0) -> dict[str, str]:
    """Summarize all classes. Returns dict of name → summary."""
    summaries = {}
    total = len(classes)

    for i, cls in enumerate(classes, 1):
        print(f"  [{i:2d}/{total}] Summarizing: {cls['name']}...")
        summaries[cls["name"]] = summarize_class(cls)
        if i < total:
            time.sleep(delay)  # respect free tier rate limits

    return summaries