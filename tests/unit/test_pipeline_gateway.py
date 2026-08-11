"""Unit tests for API → pipeline subprocess gateway."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from api.pipeline_gateway import PipelineGatewayError, run_cli


def test_run_cli_parses_json(monkeypatch):
    def fake_run(cmd, input=None, capture_output=False, text=False, timeout=None):
        assert cmd[-2:] == ["suite-bootstrap"] or "suite-bootstrap" in cmd
        return SimpleNamespace(returncode=0, stdout=json.dumps({"status": "ok", "suites": 1}), stderr="")

    monkeypatch.setattr("api.pipeline_gateway.subprocess.run", fake_run)
    result = run_cli("suite-bootstrap")
    assert result == {"status": "ok", "suites": 1}


def test_run_cli_raises_on_nonzero(monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=2, stdout="", stderr="boom")

    monkeypatch.setattr("api.pipeline_gateway.subprocess.run", fake_run)
    with pytest.raises(PipelineGatewayError) as exc:
        run_cli("plan", payload={"requirement": "x"})
    assert "boom" in str(exc.value)


def test_run_cli_background_uses_popen(monkeypatch):
    calls = []

    def fake_popen(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(pid=123)

    monkeypatch.setattr("api.pipeline_gateway.subprocess.Popen", fake_popen)
    result = run_cli("onboard", "--repo-id", "r1", background=True)
    assert result == {"started": True}
    assert calls and "pipeline.admin_cli" in " ".join(calls[0])
