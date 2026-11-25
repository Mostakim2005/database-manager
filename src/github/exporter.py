"""GitHub Domain — Markdown Audit Report Exporter.

Generates the 3-tier GitHub Activity, CI Build Status & Upstream Sync Audit
directly into %USERPROFILE%\\Downloads\\ (or an explicit target path).
Reuses `triage_repositories()` and guards against None CI runs/conclusions.
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import Any

from .scanner import triage_repositories

DEFAULT_REPORT_DESTINATION = (
    Path(os.environ.get("USERPROFILE") or Path.home())
    / "Downloads"
    / "GitHub Repositories - Activity and Build Status Audit.md"
)


def _format_ci_badge(run: dict[str, Any] | None, compact: bool = False) -> str:
    if not run:
        return "⚪ *None*" if compact else "⚪ *No CI configured*"

    conc = run.get("conclusion")
    run_name = run.get("name") or "CI"
    if conc == "success":
        return "✅ Passed" if compact else f"✅ Passed (`{run_name}`)"
    if conc == "failure":
        return "❌ FAILURE" if compact else f"❌ FAILED (`{run_name}`)"
    if conc == "cancelled":
        return "⚠️ CANCELLED" if compact else f"⚠️ Cancelled (`{run_name}`)"
    if conc is None:
        status_label = str(run.get("status") or "in_progress").upper()
        return f"🔄 {status_label}" if compact else f"🔄 {run.get('status') or 'in_progress'} (`{run_name}`)"
    return f"ℹ️ {str(conc).upper()}" if compact else f"ℹ️ {conc} (`{run_name}`)"


def _format_release_tag(repo: dict[str, Any], with_backticks: bool = True) -> str:
    rel = repo.get("latest_release") or {}
    tag = repo.get("latest_tag") or {}
    raw = rel.get("tag_name") or tag.get("name")
    if not raw:
        return "—"
    return f"`{raw}`" if with_backticks else str(raw)


def _format_repo_type(repo: dict[str, Any]) -> str:
    if repo.get("is_fork"):
        return "🍴 Fork"
    if repo.get("is_private"):
        return "🔒 Private"
    return "📦 Owned"


def export_markdown_report(
    repos: list[dict[str, Any]],
    destination: str | os.PathLike[str] | None = None,
    now: datetime.datetime | None = None,
) -> str:
    """Export a patch-ready 3-tier Markdown audit report and return the written path."""
    dest_path = Path(destination) if destination is not None else DEFAULT_REPORT_DESTINATION
    triaged = triage_repositories(repos, now=now)
    sec1 = triaged["section_1"]
    sec2 = triaged["section_2"]
    sec3 = triaged["section_3"]

    md: list[str] = []
    md.append("# GitHub Repositories — Activity, Build Status & Upstream Sync Audit")
    md.append(
        f"> **Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Local Time | "
        f"**Total Repositories:** {len(repos)}"
    )
    md.append(
        "> **Audit Scope:** CI build status (GitHub Actions), official release publication, "
        "commit gap since last build/release, and upstream fork sync comparison."
    )
    md.append("")

    md.append("## Executive Summary")
    md.append("")
    md.append("| Section | Scope & Criteria | Repo Count | Key Highlights |")
    md.append("| :--- | :--- | :---: | :--- |")
    md.append(
        f"| **Section 1** | **Active (Last 0–4 Days)** | **{len(sec1)}** | "
        "Recent active pushes; CI and release build health; unbuilt & unreleased commit tracking. |"
    )
    md.append(
        f"| **Section 2** | **Mid-Range Activity (Past 4–8 Days)** | **{len(sec2)}** | "
        "Intermediate updates or changes authored in the 4–8 day window. |"
    )
    md.append(
        f"| **Section 3** | **Dormant / Untouched (2+ Weeks to 3+ Months)** | **{len(sec3)}** | "
        "Inactive repositories, untouched prototypes, and upstream fork drift. |"
    )
    md.append("")

    md.append("### Upstream Fork Sync Summary")
    md.append("")
    md.append("| Fork Repository | Upstream Parent | Sync Status | Commits Ahead | Commits Behind Upstream | Recommendation |")
    md.append("| :--- | :--- | :---: | :---: | :---: | :--- |")

    fork_rows = 0
    for r in repos:
        if r.get("is_fork"):
            parent = r.get("parent") or {}
            parent_name = parent.get("full_name") or "Unknown"
            comp = r.get("upstream_comparison")
            if isinstance(comp, dict):
                ahead = int(comp.get("ahead_by") or 0)
                behind = int(comp.get("behind_by") or 0)
                status = comp.get("status") or "unknown"
                if behind > 0 and ahead > 0:
                    rec = "⚠️ Diverged — Rebase / merge upstream changes"
                elif behind > 0:
                    rec = "⚠️ Out of date — Fast-forward sync needed"
                elif ahead > 0:
                    rec = "✅ Healthy fork — Ahead of upstream with custom patches"
                else:
                    rec = "✅ Perfectly in sync"
                md.append(
                    f"| **`{r.get('name', 'unknown')}`** | `{parent_name}` | `{status}` | `+{ahead}` | `-{behind}` | {rec} |"
                )
                fork_rows += 1
    if fork_rows == 0:
        md.append("| — | — | — | `0` | `0` | No forked repositories with comparison data |")

    md.append("")
    md.append("---")
    md.append("")

    md.append("## Section 1: Repositories with Significant Commits or Tags in the Last 0–4 Days")
    md.append("")
    if not sec1:
        md.append("> *No repositories pushed within the last 4 days.*")
    else:
        md.append("| Repository | Type | Latest Push | CI Build Status | Latest Release | Unbuilt | Unreleased |")
        md.append("| :--- | :---: | :--- | :--- | :--- | :---: | :---: |")
        for r in sec1:
            pushed_str = str(r.get("pushed_at") or "")[:16].replace("T", " ") or "—"
            ci_badge = _format_ci_badge(r.get("latest_run"), compact=False)
            rel_str = _format_release_tag(r, with_backticks=True)
            unbuilt = int(r.get("unbuilt_commits_count") or 0)
            unrel = int(r.get("unreleased_commits_count") or 0)
            md.append(
                f"| **`{r.get('name', 'unknown')}`** | {_format_repo_type(r)} | {pushed_str} | {ci_badge} | {rel_str} | **`{unbuilt}`** | **`{unrel}`** |"
            )

    md.append("")
    md.append("---")
    md.append("")

    md.append("## Section 2: Repositories with Changes in the Past 4 to 8 Days")
    md.append("")
    if not sec2:
        md.append("> *No repositories had their final push timestamp strictly within 4–8 days.*")
    else:
        md.append("| Repository | Type | Latest Push | CI Build Status | Latest Release | Unbuilt |")
        md.append("| :--- | :---: | :--- | :--- | :--- | :---: |")
        for r in sec2:
            pushed_str = str(r.get("pushed_at") or "")[:16].replace("T", " ") or "—"
            ci_badge = _format_ci_badge(r.get("latest_run"), compact=True)
            rel_str = _format_release_tag(r, with_backticks=True)
            unbuilt = int(r.get("unbuilt_commits_count") or 0)
            md.append(
                f"| **`{r.get('name', 'unknown')}`** | {_format_repo_type(r)} | {pushed_str} | {ci_badge} | {rel_str} | {unbuilt} |"
            )

    md.append("")
    md.append("---")
    md.append("")

    md.append("## Section 3: Repositories Untouched Within 2+ Weeks (or Older)")
    md.append("")
    if not sec3:
        md.append("> *No dormant repositories in this bucket.*")
    else:
        md.append("| Repository | Type | Last Pushed | CI Status | Release Tag | Upstream Drift (`ahead`/`behind`) |")
        md.append("| :--- | :---: | :--- | :--- | :--- | :---: |")
        for r in sec3:
            pushed_str = str(r.get("pushed_at") or "")[:10] or "—"
            ci_badge = _format_ci_badge(r.get("latest_run"), compact=True)
            rel_str = _format_release_tag(r, with_backticks=True)
            comp = r.get("upstream_comparison")
            drift = f"+{comp.get('ahead_by', 0)} / -{comp.get('behind_by', 0)}" if isinstance(comp, dict) else "N/A"
            md.append(
                f"| **`{r.get('name', 'unknown')}`** | {_format_repo_type(r)} | {pushed_str} | {ci_badge} | {rel_str} | `{drift}` |"
            )

    md.append("")

    sync_state = None
    try:
        from .scanner import load_sync_state
        sync_state = load_sync_state()
    except Exception:
        sync_state = None
    local_sync = (sync_state or {}).get("local_sync") if isinstance(sync_state, dict) else None
    if isinstance(local_sync, dict) and local_sync.get("counts"):
        lc = local_sync["counts"]
        md.append("---")
        md.append("")
        md.append("## Local Workspace vs. GitHub Web Sync")
        md.append(
            f"> **Checked:** {local_sync.get('checked_at', '—')} | "
            f"**Synced:** {lc.get('synced', 0)} | **Dirty/Ahead:** {lc.get('dirty_or_ahead', 0)} | "
            f"**Local-Only:** {lc.get('local_only', 0)} | **Web-Only:** {lc.get('web_only', 0)}"
        )
        if local_sync.get("deleted_on_web_since_last"):
            md.append(f"- **Deleted on Web Since Last Scan:** {', '.join(local_sync['deleted_on_web_since_last'])}")
        if local_sync.get("deleted_locally_since_last"):
            md.append(f"- **Deleted Locally Since Last Scan:** {', '.join(local_sync['deleted_locally_since_last'])}")
        md.append("")

    content = "\n".join(md)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(content, encoding="utf-8")
    return str(dest_path)
