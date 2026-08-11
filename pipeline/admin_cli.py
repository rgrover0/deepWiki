"""Pipeline admin CLI — subprocess entrypoint for the API gateway."""

from __future__ import annotations

import argparse
import json
import sys


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()


def cmd_onboard(args: argparse.Namespace) -> int:
    from core import jobs as job_store
    from pipeline.onboard_runner import _make_job, run_ingestion

    job = _make_job()
    job_store.save_job(args.repo_id, job)
    run_ingestion(args.repo_id, args.repo_url, args.suite_id, args.confluence_link or "")
    final = job_store.load_job(args.repo_id) or {}
    _emit({"repo_id": args.repo_id, "status": final.get("status", "unknown")})
    return 0 if final.get("status") == "done" else 1


def cmd_bootstrap(args: argparse.Namespace) -> int:
    from pipeline.project_bootstrap import bootstrap_project

    result = bootstrap_project(
        repo_id=args.repo_id,
        repo_url=args.repo_url or "",
        suite_id=args.suite_id,
        confluence_link=args.confluence_link or "",
    )
    _emit({"ok": True, "result": result})
    return 0


def cmd_confluence_ingest(args: argparse.Namespace) -> int:
    from pipeline.ingestion.confluence_ingester import ingest_page

    payload = json.loads(sys.stdin.read() or "{}")
    result = ingest_page(
        url_or_id=payload.get("url") or args.url,
        category=payload.get("category", "current"),
        module_tags=payload.get("module_tags") or [],
        suite_id=payload.get("suite_id", ""),
    )
    _emit({"ok": True, "result": result})
    return 0


def cmd_suite_bootstrap(_: argparse.Namespace) -> int:
    from core.graph.schema import get_driver
    from pipeline.graph.suite_writer import write_suite_config

    driver = get_driver()
    try:
        counts = write_suite_config(driver)
    finally:
        driver.close()
    _emit({"status": "ok", **counts})
    return 0


def cmd_plan(_: argparse.Namespace) -> int:
    from pipeline.cli_handlers import run_plan

    payload = json.loads(sys.stdin.read() or "{}")
    _emit(run_plan(payload))
    return 0


def cmd_compare(_: argparse.Namespace) -> int:
    from pipeline.cli_handlers import run_compare

    payload = json.loads(sys.stdin.read() or "{}")
    _emit(run_compare(payload))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline.admin_cli")
    sub = parser.add_subparsers(dest="command", required=True)

    onboard = sub.add_parser("onboard", help="Run admin Build Now ingestion")
    onboard.add_argument("--repo-id", required=True)
    onboard.add_argument("--repo-url", default="")
    onboard.add_argument("--suite-id", required=True)
    onboard.add_argument("--confluence-link", default="")
    onboard.set_defaults(func=cmd_onboard)

    reindex = sub.add_parser("reindex", help="Re-run ingestion for an existing repo")
    reindex.add_argument("--repo-id", required=True)
    reindex.add_argument("--repo-url", default="")
    reindex.add_argument("--suite-id", required=True)
    reindex.add_argument("--confluence-link", default="")
    reindex.set_defaults(func=cmd_onboard)

    boot = sub.add_parser("bootstrap", help="Project bootstrap ingestion")
    boot.add_argument("--repo-id", required=True)
    boot.add_argument("--repo-url", default="")
    boot.add_argument("--suite-id", required=True)
    boot.add_argument("--confluence-link", default="")
    boot.set_defaults(func=cmd_bootstrap)

    conf = sub.add_parser("confluence-ingest", help="Ingest a Confluence page")
    conf.add_argument("--url", default="")
    conf.set_defaults(func=cmd_confluence_ingest)

    suite = sub.add_parser("suite-bootstrap", help="Write suites from config/suites.json")
    suite.set_defaults(func=cmd_suite_bootstrap)

    plan = sub.add_parser("plan", help="Generate implementation plan (JSON stdin)")
    plan.set_defaults(func=cmd_plan)

    compare = sub.add_parser("compare", help="Run model comparison (JSON stdin)")
    compare.set_defaults(func=cmd_compare)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        _emit({"error": f"{type(exc).__name__}: {exc}"})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
