"""Subprocess gateway — API talks to pipeline without importing it."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from typing import Any

logger = logging.getLogger(__name__)


class PipelineGatewayError(RuntimeError):
    def __init__(self, message: str, *, stderr: str = "", returncode: int = 1):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


def run_cli(
    *args: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 600,
    background: bool = False,
) -> dict[str, Any] | None:
    """
    Invoke ``python -m pipeline.admin_cli <args>``.

    When ``background`` is True, start the process and return immediately
    with ``{"started": True}``. Otherwise wait and parse JSON stdout.
    """
    cmd = [sys.executable, "-m", "pipeline.admin_cli", *args]
    stdin = None
    input_text = None
    if payload is not None:
        input_text = json.dumps(payload)

    logger.info("pipeline_gateway: %s background=%s", " ".join(cmd), background)

    if background:
        subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE if input_text else None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            text=True,
        )
        # Note: payload for background onboard is passed via CLI args, not stdin.
        return {"started": True}

    result = subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "pipeline CLI failed").strip()
        raise PipelineGatewayError(err[:800], stderr=err, returncode=result.returncode)

    out = (result.stdout or "").strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise PipelineGatewayError(
            f"Invalid JSON from pipeline CLI: {exc}; stdout={out[:400]}"
        ) from exc
