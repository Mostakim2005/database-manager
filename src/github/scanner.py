"""GitHub Domain — Core Scanner & Triage Engine.

Queries repositories via GitHub CLI (`gh api`) with timeouts and non-interactive
git environment guards, keeps private repo metadata strictly in the gitignored
local cache (`data/github/live_cache.json`), falls back cleanly to the committed
public catalog (`data/github/repos_public.json`), and classifies activity/CI/fork
drift without brittle per-repo name hardcoding.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import threading
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
GITHUB_DATA_DIR = ROOT_DIR / "data" / "github"
LIVE_CACHE_FILE = GITHUB_DATA_DIR / "live_cache.json"
PUBLIC_CACHE_FILE = GITHUB_DATA_DIR / "repos_public.json"

_SCAN_LOCK = threading.Lock()
_GH_TIMEOUT_SECONDS = 15
_PUSH_COMMIT_ANOMALY_GAP_DAYS = 14.0


def is_scan_in_progress() -> bool:
    """Return True if a live `gh api` scan currently holds the refresh lock."""
    return _SCAN_LOCK.locked()


def _parse_iso_datetime(value: str | None) -> datetime.datetime | None:
    """Parse an ISO-8601 UTC timestamp string safely."""
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except ValueError:
        return None


def run_gh_api(endpoint: str, timeout: int = _GH_TIMEOUT_SECONDS) -> Any:
    """Run a `gh api` command safely with timeout & non-interactive prompts."""
    cmd = ["gh", "api", endpoint]
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GH_PROMPT_DISABLED": "1"}
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            timeout=timeout,
            env=env,
        )
        return json.loads(res.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return None


def get_cached_repos(
    live_cache_path: Path | None = None,
    public_cache_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Load local live_cache.json if present, falling back to repos_public.json."""
    live_path = live_cache_path or LIVE_CACHE_FILE
    public_path = public_cache_path or PUBLIC_CACHE_FILE

    for candidate in (live_path, public_path):
        if candidate.exists():
            try:
                loaded = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    return loaded
            except (OSError, json.JSONDecodeError):
                continue
    return []


def redact_public_repos(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only public repository records (`is_private == False`)."""
    return [dict(r) for r in repos if not r.get("is_private")]


def write_public_snapshot(
    repos: list[dict[str, Any]],
    public_cache_path: Path | None = None,
) -> Path:
    """Persist redacted public-only repositories to `repos_public.json`."""
    dest = public_cache_path or PUBLIC_CACHE_FILE
    dest.parent.mkdir(parents=True, exist_ok=True)
    pub = redact_public_repos(repos)
    dest.write_text(json.dumps(pub, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dest


def _extract_commit_summary(commit_obj: dict[str, Any], include_full_sha: bool = False) -> dict[str, Any]:
    commit_meta = commit_obj.get("commit") or {}
    author_meta = commit_meta.get("author") or {}
    committer_meta = commit_meta.get("committer") or {}
    sha = str(commit_obj.get("sha") or "")
    entry: dict[str, Any] = {
        "sha": sha[:7],
        "date": author_meta.get("date") or committer_meta.get("date"),
        "author": author_meta.get("name"),
        "message": str(commit_meta.get("message") or "").split("\n")[0],
    }
    if include_full_sha:
        entry["full_sha"] = sha
    return entry


def _scan_repositories_unlocked(
    live_cache_path: Path,
    public_cache_path: Path,
) -> list[dict[str, Any]]:
    repos = run_gh_api("user/repos?per_page=100&affiliation=owner&sort=pushed&direction=desc")
    if not isinstance(repos, list) or len(repos) == 0:
        return get_cached_repos(live_cache_path=live_cache_path, public_cache_path=public_cache_path)

    results: list[dict[str, Any]] = []
    for r in repos:
        repo_name = r["name"]
        owner = (r.get("owner") or {}).get("login", "")
        full_name = r["full_name"]
        is_fork = bool(r.get("fork", False))
        is_private = bool(r.get("private", False))
        default_branch = r.get("default_branch") or "main"

        repo_data: dict[str, Any] = {
            "name": repo_name,
            "full_name": full_name,
            "is_fork": is_fork,
            "is_private": is_private,
            "default_branch": default_branch,
            "pushed_at": r.get("pushed_at"),
            "updated_at": r.get("updated_at"),
            "description": r.get("description") or "",
            "parent": None,
            "upstream_comparison": None,
            "latest_release": None,
            "latest_tag": None,
            "latest_run": None,
            "recent_commits": [],
            "commits_since_last_build": [],
            "commits_since_last_release": [],
            "unbuilt_commits_count": 0,
            "unreleased_commits_count": 0,
        }

        if is_fork and owner:
            repo_detail = run_gh_api(f"repos/{full_name}")
            if isinstance(repo_detail, dict) and repo_detail.get("parent"):
                parent_info = repo_detail["parent"]
                parent_full_name = parent_info.get("full_name", "")
                parent_owner = (parent_info.get("owner") or {}).get("login", "")
                parent_branch = parent_info.get("default_branch") or "main"
                repo_data["parent"] = {
                    "full_name": parent_full_name,
                    "default_branch": parent_branch,
                    "html_url": parent_info.get("html_url"),
                }
                if parent_owner:
                    comp = run_gh_api(
                        f"repos/{full_name}/compare/{parent_owner}:{parent_branch}...{owner}:{default_branch}"
                    )
                    if isinstance(comp, dict):
                        repo_data["upstream_comparison"] = {
                            "status": comp.get("status"),
                            "ahead_by": int(comp.get("ahead_by") or 0),
                            "behind_by": int(comp.get("behind_by") or 0),
                            "total_commits": int(comp.get("total_commits") or 0),
                            "html_url": comp.get("html_url"),
                        }

        releases = run_gh_api(f"repos/{full_name}/releases?per_page=1")
        if isinstance(releases, list) and len(releases) > 0:
            rel = releases[0]
            repo_data["latest_release"] = {
                "name": rel.get("name"),
                "tag_name": rel.get("tag_name"),
                "published_at": rel.get("published_at"),
                "html_url": rel.get("html_url"),
            }

        tags = run_gh_api(f"repos/{full_name}/tags?per_page=1")
        if isinstance(tags, list) and len(tags) > 0:
            t = tags[0]
            repo_data["latest_tag"] = {
                "name": t.get("name"),
                "commit_sha": (t.get("commit") or {}).get("sha"),
            }

        runs = run_gh_api(f"repos/{full_name}/actions/runs?per_page=5")
        if isinstance(runs, dict) and isinstance(runs.get("workflow_runs"), list) and len(runs["workflow_runs"]) > 0:
            latest_run = runs["workflow_runs"][0]
            repo_data["latest_run"] = {
                "id": latest_run.get("id"),
                "name": latest_run.get("name"),
                "head_sha": latest_run.get("head_sha"),
                "head_branch": latest_run.get("head_branch"),
                "event": latest_run.get("event"),
                "status": latest_run.get("status"),
                "conclusion": latest_run.get("conclusion"),
                "created_at": latest_run.get("created_at"),
                "updated_at": latest_run.get("updated_at"),
                "html_url": latest_run.get("html_url"),
            }

        commits = run_gh_api(f"repos/{full_name}/commits?sha={default_branch}&per_page=20")
        if isinstance(commits, list):
            parsed_commits = [_extract_commit_summary(c, include_full_sha=True) for c in commits]
            repo_data["recent_commits"] = parsed_commits

            latest_run_obj = repo_data.get("latest_run") or {}
            run_sha = latest_run_obj.get("head_sha")
            if run_sha:
                unbuilt: list[dict[str, Any]] = []
                for c in parsed_commits:
                    if c["full_sha"] == run_sha:
                        break
                    unbuilt.append(c)
                else:
                    comp_run = run_gh_api(f"repos/{full_name}/compare/{run_sha[:7]}...{default_branch}")
                    if isinstance(comp_run, dict) and isinstance(comp_run.get("commits"), list):
                        unbuilt = [_extract_commit_summary(uc) for uc in comp_run["commits"]]
                repo_data["commits_since_last_build"] = unbuilt
                repo_data["unbuilt_commits_count"] = len(unbuilt)
            else:
                repo_data["commits_since_last_build"] = parsed_commits
                repo_data["unbuilt_commits_count"] = len(parsed_commits)

            tag_name = None
            if repo_data["latest_release"] and repo_data["latest_release"].get("tag_name"):
                tag_name = repo_data["latest_release"]["tag_name"]
            elif repo_data["latest_tag"] and repo_data["latest_tag"].get("name"):
                tag_name = repo_data["latest_tag"]["name"]

            if tag_name:
                comp_tag = run_gh_api(f"repos/{full_name}/compare/{tag_name}...{default_branch}")
                if isinstance(comp_tag, dict) and isinstance(comp_tag.get("commits"), list):
                    unreleased = [_extract_commit_summary(uc) for uc in comp_tag["commits"]]
                    repo_data["commits_since_last_release"] = unreleased
                    repo_data["unreleased_commits_count"] = len(unreleased)

        results.append(repo_data)

    try:
        live_cache_path.parent.mkdir(parents=True, exist_ok=True)
        live_cache_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError:
        pass

    return results


def scan_all_repositories(
    force_refresh: bool = False,
    live_cache_path: Path | None = None,
    public_cache_path: Path | None = None,
    blocking: bool = True,
) -> list[dict[str, Any]]:
    """Fetch & analyze GitHub repos via `gh api`, or load cached/public snapshot.

    When `blocking=False` and a live refresh is already running, raises `RuntimeError`.
    """
    live_path = live_cache_path or LIVE_CACHE_FILE
    public_path = public_cache_path or PUBLIC_CACHE_FILE

    if not force_refresh:
        return get_cached_repos(live_cache_path=live_path, public_cache_path=public_path)

    acquired = _SCAN_LOCK.acquire(blocking=blocking)
    if not acquired:
        raise RuntimeError("GitHub refresh scan already in progress")
    try:
        return _scan_repositories_unlocked(live_cache_path=live_path, public_cache_path=public_path)
    finally:
        _SCAN_LOCK.release()


def triage_repositories(
    repos: list[dict[str, Any]],
    now: datetime.datetime | None = None,
) -> dict[str, Any]:
    """Categorize repositories into 0-4d, 4-8d, and dormant buckets with CI/fork KPIs.

    Guards against missing/None fields and detects stale metadata-only `pushed_at`
    bumps by comparing `pushed_at` against the latest commit timestamp in `recent_commits`.
    """
    ref_now = now or datetime.datetime.now(datetime.timezone.utc)
    if ref_now.tzinfo is None:
        ref_now = ref_now.replace(tzinfo=datetime.timezone.utc)

    sec1: list[dict[str, Any]] = []
    sec2: list[dict[str, Any]] = []
    sec3: list[dict[str, Any]] = []

    for orig in repos:
        r = dict(orig)
        pushed_dt = _parse_iso_datetime(r.get("pushed_at"))
        commits = r.get("recent_commits") or []
        commit_dt = _parse_iso_datetime(commits[0].get("date")) if commits and isinstance(commits[0], dict) else None

        days_pushed = ((ref_now - pushed_dt).total_seconds() / 86400.0) if pushed_dt else 9999.0
        days_commit = ((ref_now - commit_dt).total_seconds() / 86400.0) if commit_dt else None

        # Detect metadata/settings-only push bumps where latest commit is >14d older than pushed_at
        effective_days = days_pushed
        stale_push_anomaly = False
        if days_commit is not None and (days_commit - days_pushed) > _PUSH_COMMIT_ANOMALY_GAP_DAYS and days_commit > 8.0:
            effective_days = days_commit
            stale_push_anomaly = True

        r["days_pushed"] = round(max(0.0, days_pushed), 1)
        if days_commit is not None:
            r["days_since_commit"] = round(max(0.0, days_commit), 1)
        r["stale_push_anomaly"] = stale_push_anomaly

        if effective_days <= 4.0:
            sec1.append(r)
        elif 4.0 < effective_days <= 8.0:
            sec2.append(r)
        else:
            sec3.append(r)

    passing_ci = 0
    failing_ci = 0
    running_ci = 0
    no_ci = 0
    for r in repos:
        run = r.get("latest_run")
        if not run:
            no_ci += 1
            continue
        conc = run.get("conclusion")
        if conc == "success":
            passing_ci += 1
        elif conc in ("failure", "cancelled", "timed_out", "action_required"):
            failing_ci += 1
        elif conc is None:
            running_ci += 1

    forks_count = sum(1 for r in repos if r.get("is_fork"))
    private_count = sum(1 for r in repos if r.get("is_private"))
    total_unreleased_commits = sum(int(r.get("unreleased_commits_count") or 0) for r in repos)

    return {
        "section_1": sec1,
        "section_2": sec2,
        "section_3": sec3,
        "metrics": {
            "total_repos": len(repos),
            "sec1_count": len(sec1),
            "sec2_count": len(sec2),
            "sec3_count": len(sec3),
            "passing_ci": passing_ci,
            "failing_ci": failing_ci,
            "running_ci": running_ci,
            "no_ci": no_ci,
            "forks_count": forks_count,
            "private_count": private_count,
            "total_unreleased_commits": total_unreleased_commits,
            "cache_source": "live_cache.json" if LIVE_CACHE_FILE.exists() else "repos_public.json",
        },
    }
