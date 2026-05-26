"""
Intent classifier — Iteration 16.

Classify a developer question into one of five retrieval strategies.
Keyword rules are checked first; LLM is the fallback for ambiguous cases.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Ordered by specificity — first match wins
_RULES: list[tuple[str, list[str]]] = [
    ("FLOW_TRACE",   ["how does", "how do", "walk through", "step by step",
                      "trace", "what happens when", "explain the flow",
                      "explain how", "take me through"]),
    ("WHY_DECISION", ["why do we", "why does", "why use", "why is", "why was",
                      "reason for", "rationale", "design decision"]),
    ("API_IMPACT",   ["which endpoint", "what endpoint", "api endpoint", "rest api",
                      "http route", "who calls", "who consumes", "consuming repo"]),
    ("HISTORY",      ["when was", "who changed", "last changed", "git history",
                      "which commit"]),
]

_LLM_PROMPT = """Classify this developer question into exactly one category.

FLOW_TRACE   – asks about execution flow or process (how does X work, trace X)
CLASS_LOOKUP – asks what a class or method does (what is X, describe X)
API_IMPACT   – asks about HTTP endpoints or API consumers
WHY_DECISION – asks why something was designed a certain way
HISTORY      – asks about change history

Question: {question}

Reply with ONLY the category name."""

_ENTITY_PROMPT = """You are helping trace code execution in a Spring PetClinic application.

Extract the most relevant class or method name from this question so we can
trace its execution flow in the codebase.

Known entry points:
  owner creation  → processCreationForm
  owner update    → processUpdateOwnerForm
  owner search    → processFindForm
  owner display   → showOwner
  pet creation    → PetController
  visit creation  → VisitController
  vet listing     → VetController

Question: {question}

Reply with ONLY the class or method name, nothing else."""


def classify_intent(question: str) -> str:
    """Return intent string for the question."""
    q = question.lower()
    for intent, keywords in _RULES:
        if any(kw in q for kw in keywords):
            return intent
    # LLM fallback
    try:
        resp = _groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": _LLM_PROMPT.format(question=question)}],
            max_tokens=10,
            temperature=0.0,
        )
        label = resp.choices[0].message.content.strip().upper()
        if label in {"FLOW_TRACE", "CLASS_LOOKUP", "API_IMPACT", "WHY_DECISION", "HISTORY"}:
            return label
    except Exception:
        pass
    return "CLASS_LOOKUP"


def extract_entry_point(question: str) -> str:
    """Extract the class or method name to use as flow-trace entry point."""
    try:
        resp = _groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": _ENTITY_PROMPT.format(question=question)}],
            max_tokens=15,
            temperature=0.0,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        # Fallback: take the longest word from the question as a guess
        words = [w for w in question.split() if len(w) > 4 and w[0].isupper()]
        return words[0] if words else question.split()[0]
