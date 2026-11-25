"""Unified CLI entry point for GitHub Repositories domain inside Database Manager."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from github.exporter import export_markdown_report  # noqa: E402
from github.local_sync import reconcile_local_with_web  # noqa: E402
from github.scanner import (  # noqa: E402
    LIVE_CACHE_FILE,
    PUBLIC_CACHE_FILE,
    get_cache_metadata,
    load_sync_state,
    run_local_sync_check,
    scan_all_repositories,
    triage_repositories,
    write_public_snapshot,
)


def inspect_github_doctor(repos: list[dict[str, Any]], include_local: bool = False) -> dict[str, Any]:
    """Summarize CI failures, behind-upstream forks, unreleased commits, cache freshness, and local drift."""
    triaged = triage_repositories(repos)
    metrics = triaged["metrics"]
    all_triaged = triaged["section_1"] + triaged["section_2"] + triaged["section_3"]

    failing_repos: list[dict[str, Any]] = []
    behind_forks: list[dict[str, Any]] = []
    stale_anomalies: list[str] = []
    unbuilt_repos: list[dict[str, Any]] = []

    for r in all_triaged:
        run = r.get("latest_run") or {}
        conc = run.get("conclusion")
        if conc in ("failure", "cancelled", "timed_out", "action_required"):
            failing_repos.append(
                {
                    "name": r.get("name"),
                    "conclusion": conc,
                    "workflow": run.get("name"),
                    "html_url": run.get("html_url"),
                }
            )
        comp = r.get("upstream_comparison")
        if r.get("is_fork") and isinstance(comp, dict) and int(comp.get("behind_by") or 0) > 0:
            behind_forks.append(
                {
                    "name": r.get("name"),
                    "parent": (r.get("parent") or {}).get("full_name"),
                    "ahead_by": int(comp.get("ahead_by") or 0),
                    "behind_by": int(comp.get("behind_by") or 0),
                }
            )
        if r.get("stale_push_anomaly"):
            stale_anomalies.append(str(r.get("name")))
        if int(r.get("unbuilt_commits_count") or 0) > 0 and run:
            unbuilt_repos.append(
                {
                    "name": r.get("name"),
                    "unbuilt_commits_count": int(r.get("unbuilt_commits_count") or 0),
                }
            )

    cache_meta = get_cache_metadata()
    sync_state = load_sync_state()
    local_sync = sync_state.get("local_sync")
    if include_local:
        local_sync = reconcile_local_with_web(repos, previous_state=sync_state)

    return {
        "healthy": len(repos) > 0 and metrics["private_count"] >= 0,
        "total_repos": len(repos),
        "live_cache_present": LIVE_CACHE_FILE.exists(),
        "public_snapshot_present": PUBLIC_CACHE_FILE.exists(),
        "cache_metadata": cache_meta,
        "metrics": metrics,
        "failing_repos": failing_repos,
        "behind_forks": behind_forks,
        "stale_push_anomalies": stale_anomalies,
        "unbuilt_repos": unbuilt_repos,
        "local_sync_counts": (local_sync or {}).get("counts") if isinstance(local_sync, dict) else None,
        "local_sync": local_sync if include_local else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="GitHub Repositories Domain CLI (Database Manager)")
    parser.add_argument("--verify", action="store_true", help="Verify cached/public repo inventory & triage metrics")
    parser.add_argument("--refresh", action="store_true", help="Scan live GitHub repos via `gh api` into live_cache.json")
    parser.add_argument("--check-local", action="store_true", help="Reconcile local Git repos against GitHub web inventory")
    parser.add_argument("--no-local", action="store_true", help="Skip local folder scan during --refresh")
    parser.add_argument("--update-public", action="store_true", help="Write redacted public-only repos to data/github/repos_public.json")
    parser.add_argument("--export", action="store_true", help="Export Markdown activity & CI report to Downloads")
    parser.add_argument("--out", help="Custom destination file path for --export")
    parser.add_argument("--doctor", action="store_true", help="Audit CI failures, fork drift, local sync, and unbuilt commits")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    repos = scan_all_repositories(force_refresh=args.refresh, include_local=not args.no_local)
    if args.update_public:
        pub_path = write_public_snapshot(repos)
        if not args.export and not args.doctor and not args.verify and not args.check_local:
            payload = {"updated_public_snapshot": str(pub_path), "public_count": sum(1 for r in repos if not r.get("is_private"))}
            print(json.dumps(payload, indent=2) if args.json else f"Updated public snapshot: {pub_path} ({payload['public_count']} repos)")
            return

    if args.check_local:
        report = run_local_sync_check(repos=repos, persist=True)
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            c = report["counts"]
            print("\n=== GitHub Local vs. Web Sync ===")
            print(f"  Scanned roots:     {', '.join(report['scanned_roots'])}")
            print(f"  Local git repos:   {c['local_total']} | Web repos: {c['web_total']}")
            print(f"  Synced cleanly:    {c['synced']} | Dirty/Ahead: {c['dirty_or_ahead']}")
            print(f"  Local-only:        {c['local_only']} | Web-only (not cloned): {c['web_only']}\n")
        return

    if args.export:
        dest = export_markdown_report(repos, destination=args.out)
        payload = {"status": "ok", "destination": dest, "total_repos": len(repos)}
        print(json.dumps(payload, indent=2) if args.json else f"Exported GitHub audit report to: {dest}")
        return

    if args.doctor:
        report = inspect_github_doctor(repos, include_local=not args.no_local)
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            m = report["metrics"]
            print("\n=== GitHub Domain Doctor ===")
            print(f"  Total repos:       {report['total_repos']} (cache: {m['cache_source']}, age: {m.get('cache_age_hours')}h)")
            print(f"  CI Health:         {m['passing_ci']} passing | {m['failing_ci']} failing | {m['no_ci']} none")
            print(f"  Behind forks:      {len(report['behind_forks'])}")
            print(f"  Push-commit drift: {', '.join(report['stale_push_anomalies']) or 'None'}")
            if report.get("local_sync_counts"):
                lc = report["local_sync_counts"]
                print(f"  Local vs Web:      {lc['synced']} synced | {lc['dirty_or_ahead']} dirty/ahead | {lc['local_only']} local-only | {lc['web_only']} web-only\n")
        return

    # Default or --verify
    triaged = triage_repositories(repos)
    m = triaged["metrics"]
    payload = {
        "total_repos": m["total_repos"],
        "public_repos": sum(1 for r in repos if not r.get("is_private")),
        "private_repos": m["private_count"],
        "forks_count": m["forks_count"],
        "passing_ci": m["passing_ci"],
        "failing_ci": m["failing_ci"],
        "no_ci": m["no_ci"],
        "last_refreshed_at": m.get("last_refreshed_at"),
        "healthy": m["total_repos"] > 0,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("\n=== GitHub Domain Verification ===")
        print(f"  Total repositories: {payload['total_repos']} (Public: {payload['public_repos']}, Private: {payload['private_repos']})")
        print(f"  Upstream forks:     {payload['forks_count']}")
        print(f"  CI Health:          {payload['passing_ci']} passing / {payload['failing_ci']} failing / {payload['no_ci']} none\n")


if __name__ == "__main__":
    main()
