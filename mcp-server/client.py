"""
HTTP client for DeepWiki API.
All MCP tools call through here so DEEPWIKI_API_URL is the single config point.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

_BASE = os.getenv("DEEPWIKI_API_URL", "http://localhost:8000").rstrip("/")
_TIMEOUT = 30.0


def api_get(path: str, params: dict | None = None) -> dict:
    url = f"{_BASE}/{path.lstrip('/')}"
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params or {})
        resp.raise_for_status()
        return resp.json()


def api_post(path: str, payload: dict) -> dict:
    url = f"{_BASE}/{path.lstrip('/')}"
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()
