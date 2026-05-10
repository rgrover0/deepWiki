import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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