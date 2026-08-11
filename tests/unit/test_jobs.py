"""Unit tests for core.jobs file-backed store."""

from __future__ import annotations

import os
from pathlib import Path

from core import jobs


def test_save_load_and_list_jobs(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DEEPWIKI_JOB_DIR", str(tmp_path))
    job = jobs.make_job()
    assert job["status"] == "running"
    assert len(job["steps"]) == len(jobs.PIPELINE_STEPS)
    assert job["steps"][0]["label"] == jobs.PIPELINE_STEPS[0]

    jobs.save_job("repo-a", job)
    loaded = jobs.load_job("repo-a")
    assert loaded is not None
    assert loaded["repo_id"] == "repo-a"
    assert loaded["status"] == "running"

    job["status"] = "done"
    job["progress"] = 100
    jobs.save_job("repo-a", job)

    listed = jobs.list_jobs()
    assert len(listed) == 1
    assert listed[0]["status"] == "done"


def test_missing_job_returns_none(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DEEPWIKI_JOB_DIR", str(tmp_path))
    assert jobs.load_job("missing") is None
