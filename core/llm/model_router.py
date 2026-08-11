"""
Model Router — Iteration 21.

Selects the right LLM adapter for each task type and content size.
All consumers call route() and get back an LLMAdapter with a .complete() method —
they never talk to a specific SDK directly.

Task preference chains (first available provider wins):
  annotation_extraction   groq -> local
  wiki_generation         groq -> claude   (claude bumped to front if content > 6k chars)
  architecture_analysis   claude -> groq
  flow_trace              groq
  ask                     groq
  intent_classification   groq
  plan                    groq

Providers:
  groq   — Groq API, llama-3.3-70b-versatile  (default; requires GROQ_API_KEY)
  claude — Anthropic API, claude-sonnet-4-6   (requires ANTHROPIC_API_KEY)
  local  — stub, not yet implemented
"""

import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

TASK_MODEL_MAP: dict[str, list[str]] = {
    "annotation_extraction": ["groq", "local"],
    "wiki_generation":       ["groq", "claude"],
    "architecture_analysis": ["claude", "groq"],
    "flow_trace":            ["groq"],
    "ask":                   ["groq"],
    "intent_classification": ["groq"],
    "plan":                  ["groq"],
}

# Above this threshold prefer claude (larger context window)
_LARGE_CONTENT_CHARS = 6_000


# ── Base adapter ───────────────────────────────────────────────────────────────

class LLMAdapter:
    provider: str = "base"
    model: str    = "base"

    def complete(
        self,
        prompt:      str,
        max_tokens:  int   = 300,
        temperature: float = 0.2,
    ) -> tuple[str, int]:
        """
        Call the LLM and return (generated_text, total_tokens_used).
        Raises on unrecoverable error (caller handles retries if needed).
        """
        raise NotImplementedError


# ── Groq adapter ───────────────────────────────────────────────────────────────

class GroqAdapter(LLMAdapter):
    provider = "groq"

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        from groq import Groq
        self.model   = model
        self._client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def complete(self, prompt, max_tokens=300, temperature=0.2):
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text   = resp.choices[0].message.content.strip()
        tokens = (resp.usage.prompt_tokens or 0) + (resp.usage.completion_tokens or 0)
        return text, tokens


# ── Anthropic adapter ──────────────────────────────────────────────────────────

class AnthropicAdapter(LLMAdapter):
    provider = "claude"

    def __init__(self, model: str = "claude-sonnet-4-6"):
        import anthropic
        self.model   = model
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def complete(self, prompt, max_tokens=300, temperature=0.2):
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text   = resp.content[0].text.strip()
        tokens = resp.usage.input_tokens + resp.usage.output_tokens
        return text, tokens


# ── Provider factory ───────────────────────────────────────────────────────────

def _build_adapter(provider: str) -> LLMAdapter | None:
    """Instantiate provider adapter. Returns None if unavailable."""
    try:
        if provider == "groq":
            if not os.getenv("GROQ_API_KEY"):
                logger.debug("GROQ_API_KEY not set — skipping groq provider")
                return None
            return GroqAdapter()
        if provider == "claude":
            if not os.getenv("ANTHROPIC_API_KEY"):
                logger.debug("ANTHROPIC_API_KEY not set — skipping claude provider")
                return None
            return AnthropicAdapter()
        # "local" and "bedrock" — not implemented, fall through
        logger.debug("Provider %r not yet implemented", provider)
        return None
    except Exception as e:
        logger.warning("Failed to build adapter for %r: %s", provider, e)
        return None


# ── Public API ─────────────────────────────────────────────────────────────────

def route(task: str, content_size: int = 0) -> LLMAdapter:
    """
    Return the best available LLMAdapter for the given task.

    Args:
        task:         Key from TASK_MODEL_MAP (e.g. "wiki_generation").
        content_size: Character length of the prompt being sent. Used to prefer
                      Claude for tasks where it outperforms on large context.

    Returns:
        A ready-to-use LLMAdapter. Never raises — falls back to GroqAdapter.
    """
    candidates = list(TASK_MODEL_MAP.get(task, ["groq"]))

    # Boost claude to front for large-content wiki generation
    if content_size > _LARGE_CONTENT_CHARS and "claude" in candidates:
        candidates = ["claude"] + [c for c in candidates if c != "claude"]

    for provider in candidates:
        adapter = _build_adapter(provider)
        if adapter:
            logger.info(
                "model_router: task=%s provider=%s model=%s content_size=%d",
                task, adapter.provider, adapter.model, content_size,
            )
            return adapter

    logger.error("model_router: all providers exhausted for task=%s — no adapter available", task)
    raise RuntimeError(
        f"No LLM provider available for task '{task}'. "
        "Set GROQ_API_KEY or ANTHROPIC_API_KEY in your .env file."
    )
