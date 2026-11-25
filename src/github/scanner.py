"""GitHub Domain — Core Scanner, Progress Tracker & Triage Engine.

Queries repositories via GitHub CLI (`gh api`) with timeouts, cancellation,
real-time progress tracking, single-repo quick refresh, and non-interactive git
environment guards. Keeps private repo metadata and local filesystem sync state
strictly in gitignored local files (`data/github/live_cache.json` and
`data/github/sync_state.json`), falls back cleanly to the committed public
catalog (`data/github/repos_public.json`), and classifies activity/CI/fork drift.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from .local_sync import reconcile_local_with_web

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
GITHUB_DATA_DIR = ROOT_DIR / "data" / "github"
LIVE_CACHE_FILE = GITHUB_DATA_DIR / "live_cache.json"
PUBLIC_CACHE_FILE = GITHUB_DATA_DIR / "repos_public.json"
SYNC_STATE_FILE = GITHUB_DATA_DIR / "sync_state.json"

_SCAN_LOCK = threading.Lock()
_PROGRESS_LOCK = threading.Lock()
_CANCEL_EVENT = threading.Event()
_GH_TIMEOUT_SECONDS = 15
_PUSH_COMMIT_ANOMALY_GAP_DAYS = 14.0
_CACHE_STALE_HOURS = 24.0

_REFRESH_STATUS: dict[str, Any] = {
    "running": False,
    "job_id": None,
    "stage": "idle",
    "current": 0,
    "total": 0,
    "percent": 0.0,
    "current_repo": "",
    "message": "Ready to refresh live GitHub data.",
    "started_at": None,
    "finished_at": None,
    "elapsed_seconds": 0.0,
    "cancel_requested": False,
    "error": None,
    "summary": None,
}


def is_scan_in_progress() -> bool:
    """Return True if a live `gh api` scan currently holds the refresh lock."""
    return _SCAN_LOCK.locked()


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _update_refresh_status(**fields: Any) -> None:
    with _PROGRESS_LOCK:
        _REFRESH_STATUS.update(fields)
        started = _parse_iso_datetime(_REFRESH_STATUS.get("started_at"))
        finished = _parse_iso_datetime(_REFRESH_STATUS.get("finished_at"))
        if started:
            end_ref = finished or datetime.datetime.now(datetime.timezone.utc)
            _REFRESH_STATUS["elapsed_seconds"] = round(max(0.0, (end_ref - started).total_seconds()), 1)
        total = int(_REFRESH_STATUS.get("total") or 0)
        cur = int(_REFRESH_STATUS.get("current") or 0)
        if total > 0:
            _REFRESH_STATUS["percent"] = round(min(100.0, max(0.0, (cur / total) * 100.0)), 1)
        elif _REFRESH_STATUS.get("stage") == "completed":
            _REFRESH_STATUS["percent"] = 100.0


def get_refresh_status() -> dict[str, Any]:
    """Return a thread-safe snapshot of the active or most recent refresh job."""
    with _PROGRESS_LOCK:
        snap = dict(_REFRESH_STATUS)
    started = _parse_iso_datetime(snap.get("started_at"))
    finished = _parse_iso_datetime(snap.get("finished_at"))
    if started and snap.get("running") and not finished:
        snap["elapsed_seconds"] = round(
            max(0.0, (datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()), 1
        )
    return snap


def load_sync_state(sync_state_path: Path | None = None) -> dict[str, Any]:
    """Load gitignored local sync & last-refreshed metadata if present."""
    path = sync_state_path or SYNC_STATE_FILE
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_sync_state(state: dict[str, Any], sync_state_path: Path | None = None) -> Path:
    """Persist sync metadata atomically in UTF-8 without BOM."""
    path = sync_state_path or SYNC_STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


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


def get_cache_metadata(
    live_cache_path: Path | None = None,
    public_cache_path: Path | None = None,
    sync_state_path: Path | None = None,
) -> dict[str, Any]:
    """Return freshness timestamp, source, age in hours, and staleness flag."""
    live_path = live_cache_path or LIVE_CACHE_FILE
    public_path = public_cache_path or PUBLIC_CACHE_FILE
    sync_state = load_sync_state(sync_state_path=sync_state_path)

    source = "live_cache.json" if live_path.exists() else ("repos_public.json" if public_path.exists() else "none")
    active_file = live_path if live_path.exists() else (public_path if public_path.exists() else None)

    refreshed_iso = sync_state.get("last_refreshed_at")
    refreshed_dt = _parse_iso_datetime(refreshed_iso)
    if refreshed_dt is None and active_file is not None and active_file.exists():
        mtime = active_file.stat().st_mtime
        refreshed_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
        refreshed_iso = refreshed_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    age_hours: float | None = None
    is_stale = True
    if refreshed_dt is not None:
        age_hours = round(max(0.0, (datetime.datetime.now(datetime.timezone.utc) - refreshed_dt).total_seconds() / 3600.0), 1)
        is_stale = age_hours >= _CACHE_STALE_HOURS

    return {
        "cache_source": source,
        "last_refreshed_at": refreshed_iso,
        "cache_age_hours": age_hours,
        "is_cache_stale": is_stale,
    }


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


def _scan_single_repo_details(r: dict[str, Any]) -> dict[str, Any]:
    """Fetch releases, tags, CI runs, commits, and fork drift for one repository object."""
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
        "language": r.get("language") or "",
        "stargazers_count": int(r.get("stargazers_count") or 0),
        "forks_count": int(r.get("forks_count") or 0),
        "open_issues_count": int(r.get("open_issues_count") or 0),
        "topics": [str(topic) for topic in (r.get("topics") or [])[:6]],
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
        repo_detail = r if r.get("parent") else run_gh_api(f"repos/{full_name}")
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

    return repo_data


def _fetch_all_owner_repos(
    progress_cb: Callable[[str, int, int, str, str], None] | None = None,
) -> list[dict[str, Any]]:
    """Fetch owned & forked repositories across pages via `gh api`."""
    collected: list[dict[str, Any]] = []
    for page in range(1, 6):
        batch = run_gh_api(f"user/repos?per_page=100&page={page}&affiliation=owner&sort=pushed&direction=desc")
        if not isinstance(batch, list):
            if page == 1:
                return []
            break
        collected.extend(batch)
        if progress_cb:
            progress_cb("listing", 0, len(collected), "", f"Discovered {len(collected)} repositories (page {page})...")
        if len(batch) < 100:
            break
    return collected


def _write_live_cache(results: list[dict[str, Any]], live_cache_path: Path) -> None:
    try:
        live_cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = live_cache_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(live_cache_path)
    except OSError:
        pass


def _update_sync_state_from_scan(
    repos: list[dict[str, Any]],
    include_local: bool = True,
    sync_state_path: Path | None = None,
) -> dict[str, Any]:
    prev = load_sync_state(sync_state_path=sync_state_path)
    now_iso = _utc_now_iso()
    next_state: dict[str, Any] = {
        "last_refreshed_at": now_iso,
        "web_total": len(repos),
        "web_slugs": sorted({str(r.get("full_name") or "").lower() for r in repos if r.get("full_name")}),
        "local_slugs": prev.get("local_slugs", []),
        "local_sync": prev.get("local_sync"),
    }
    if include_local:
        local_sync = reconcile_local_with_web(repos, previous_state=prev)
        next_state["local_slugs"] = local_sync.get("current_local_slugs", [])
        next_state["local_sync"] = local_sync
    save_sync_state(next_state, sync_state_path=sync_state_path)
    return next_state


def _scan_repositories_unlocked(
    live_cache_path: Path,
    public_cache_path: Path,
    progress_cb: Callable[[str, int, int, str, str], None] | None = None,
    cancel_event: threading.Event | None = None,
    include_local: bool = True,
    sync_state_path: Path | None = None,
) -> list[dict[str, Any]]:
    if progress_cb:
        progress_cb("listing", 0, 0, "", "Querying GitHub repository list via gh api...")
    repos = _fetch_all_owner_repos(progress_cb=progress_cb)
    if not repos:
        cached = get_cached_repos(live_cache_path=live_cache_path, public_cache_path=public_cache_path)
        if progress_cb:
            progress_cb("error", 0, 0, "", "GitHub CLI unavailable or returned 0 repos; kept cached snapshot.")
        return cached

    total = len(repos)
    results: list[dict[str, Any]] = []
    for idx, r in enumerate(repos, start=1):
        if cancel_event and cancel_event.is_set():
            if progress_cb:
                progress_cb("cancelled", idx - 1, total, r.get("name", ""), "Scan cancelled; kept previous cache.")
            return get_cached_repos(live_cache_path=live_cache_path, public_cache_path=public_cache_path)
        if progress_cb:
            progress_cb("scanning_repos", idx - 1, total, r.get("full_name") or r.get("name", ""), f"Scanning {r.get('name', '')} ({idx}/{total})...")
        results.append(_scan_single_repo_details(r))
        if progress_cb:
            progress_cb("scanning_repos", idx, total, r.get("full_name") or r.get("name", ""), f"Scanned {r.get('name', '')} ({idx}/{total})")

    if cancel_event and cancel_event.is_set():
        if progress_cb:
            progress_cb("cancelled", len(results), total, "", "Scan cancelled; kept previous cache.")
        return get_cached_repos(live_cache_path=live_cache_path, public_cache_path=public_cache_path)

    if progress_cb:
        progress_cb("saving", total, total, "", "Writing live cache & checking local workspaces...")
    _write_live_cache(results, live_cache_path)
    state = _update_sync_state_from_scan(
        results,
        include_local=include_local,
        sync_state_path=sync_state_path,
    )
    if progress_cb:
        counts = ((state.get("local_sync") or {}).get("counts") or {})
        summary = {
            "total_repos": len(results),
            "last_refreshed_at": state.get("last_refreshed_at"),
            "local_checked": bool(include_local),
            "local_counts": counts,
        }
        _update_refresh_status(summary=summary)
        progress_cb("completed", total, total, "", f"Refreshed {len(results)} repositories successfully.")
    return results


def scan_all_repositories(
    force_refresh: bool = False,
    live_cache_path: Path | None = None,
    public_cache_path: Path | None = None,
    blocking: bool = True,
    include_local: bool = True,
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
    _CANCEL_EVENT.clear()
    _update_refresh_status(
        running=True,
        job_id=uuid.uuid4().hex[:10],
        stage="listing",
        current=0,
        total=0,
        percent=0.0,
        current_repo="",
        message="Starting live GitHub refresh...",
        started_at=_utc_now_iso(),
        finished_at=None,
        cancel_requested=False,
        error=None,
        summary=None,
    )
    try:
        def _cb(stage: str, cur: int, tot: int, repo: str, msg: str) -> None:
            _update_refresh_status(
                running=stage not in ("completed", "cancelled", "error"),
                stage=stage,
                current=cur,
                total=tot,
                current_repo=repo,
                message=msg,
                finished_at=_utc_now_iso() if stage in ("completed", "cancelled", "error") else None,
            )

        return _scan_repositories_unlocked(
            live_cache_path=live_path,
            public_cache_path=public_path,
            progress_cb=_cb,
            cancel_event=_CANCEL_EVENT,
            include_local=include_local,
        )
    except Exception as exc:
        _update_refresh_status(
            running=False,
            stage="error",
            message=f"Refresh failed: {exc}",
            error=str(exc),
            finished_at=_utc_now_iso(),
        )
        raise
    finally:
        if get_refresh_status().get("running"):
            _update_refresh_status(running=False, finished_at=_utc_now_iso())
        _SCAN_LOCK.release()


def start_background_refresh(
    include_local: bool = True,
    live_cache_path: Path | None = None,
    public_cache_path: Path | None = None,
) -> dict[str, Any]:
    """Start an asynchronous full GitHub + optional local refresh and return initial status."""
    acquired = _SCAN_LOCK.acquire(blocking=False)
    if not acquired:
        raise RuntimeError("GitHub refresh scan already in progress")

    live_path = live_cache_path or LIVE_CACHE_FILE
    public_path = public_cache_path or PUBLIC_CACHE_FILE
    job_id = uuid.uuid4().hex[:10]
    _CANCEL_EVENT.clear()
    _update_refresh_status(
        running=True,
        job_id=job_id,
        stage="listing",
        current=0,
        total=0,
        percent=0.0,
        current_repo="",
        message="Starting live GitHub scan via gh api...",
        started_at=_utc_now_iso(),
        finished_at=None,
        cancel_requested=False,
        error=None,
        summary=None,
    )

    def _worker() -> None:
        try:
            def _cb(stage: str, cur: int, tot: int, repo: str, msg: str) -> None:
                _update_refresh_status(
                    running=stage not in ("completed", "cancelled", "error"),
                    stage=stage,
                    current=cur,
                    total=tot,
                    current_repo=repo,
                    message=msg,
                    finished_at=_utc_now_iso() if stage in ("completed", "cancelled", "error") else None,
                )

            _scan_repositories_unlocked(
                live_cache_path=live_path,
                public_cache_path=public_path,
                progress_cb=_cb,
                cancel_event=_CANCEL_EVENT,
                include_local=include_local,
            )
        except Exception as exc:
            _update_refresh_status(
                running=False,
                stage="error",
                message=f"Refresh error: {exc}",
                error=str(exc),
                finished_at=_utc_now_iso(),
            )
        finally:
            if get_refresh_status().get("running"):
                _update_refresh_status(running=False, finished_at=_utc_now_iso())
            _SCAN_LOCK.release()

    threading.Thread(target=_worker, name=f"gh-refresh-{job_id}", daemon=True).start()
    return get_refresh_status()


def cancel_background_refresh() -> dict[str, Any]:
    """Request cancellation of the active background GitHub refresh job."""
    if not _SCAN_LOCK.locked():
        return {"status": "idle", "cancelled": False, "refresh": get_refresh_status()}
    _CANCEL_EVENT.set()
    _update_refresh_status(cancel_requested=True, message="Cancellation requested — stopping after current repo...")
    return {"status": "cancelling", "cancelled": True, "refresh": get_refresh_status()}


def refresh_single_repository(
    full_name: str,
    live_cache_path: Path | None = None,
    public_cache_path: Path | None = None,
    sync_state_path: Path | None = None,
) -> dict[str, Any]:
    """Refresh one specific repository (`owner/name`) and merge it into `live_cache.json`."""
    target = str(full_name or "").strip().strip("/")
    if not target or "/" not in target:
        raise ValueError("Repository full_name (owner/name) is required")

    acquired = _SCAN_LOCK.acquire(blocking=False)
    if not acquired:
        raise RuntimeError("GitHub refresh scan already in progress")

    live_path = live_cache_path or LIVE_CACHE_FILE
    public_path = public_cache_path or PUBLIC_CACHE_FILE
    try:
        repo_raw = run_gh_api(f"repos/{target}")
        if not isinstance(repo_raw, dict) or not repo_raw.get("full_name"):
            raise LookupError(f"Repository '{target}' not found or gh api unavailable")

        updated = _scan_single_repo_details(repo_raw)
        existing = get_cached_repos(live_cache_path=live_path, public_cache_path=public_path)
        merged: list[dict[str, Any]] = []
        replaced = False
        target_l = target.lower()
        for item in existing:
            if str(item.get("full_name") or "").lower() == target_l:
                merged.append(updated)
                replaced = True
            else:
                merged.append(item)
        if not replaced:
            merged.insert(0, updated)

        _write_live_cache(merged, live_path)
        prev = load_sync_state(sync_state_path=sync_state_path)
        prev["last_refreshed_at"] = _utc_now_iso()
        prev["web_total"] = len(merged)
        save_sync_state(prev, sync_state_path=sync_state_path)
        return {
            "status": "ok",
            "repository": updated,
            "triage": triage_repositories(merged),
        }
    finally:
        _SCAN_LOCK.release()


def run_local_sync_check(
    repos: list[dict[str, Any]] | None = None,
    roots: list[Path] | None = None,
    persist: bool = True,
    sync_state_path: Path | None = None,
) -> dict[str, Any]:
    """Run local vs. GitHub web drift and deletion check without calling `gh api`."""
    web_repos = repos if repos is not None else get_cached_repos()
    prev = load_sync_state(sync_state_path=sync_state_path)
    report = reconcile_local_with_web(web_repos, previous_state=prev, roots=roots)
    if persist:
        prev["local_slugs"] = report.get("current_local_slugs", [])
        if "web_slugs" not in prev:
            prev["web_slugs"] = report.get("current_web_slugs", [])
        prev["local_sync"] = report
        save_sync_state(prev, sync_state_path=sync_state_path)
    return report


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
    cache_meta = get_cache_metadata()
    sync_state = load_sync_state()
    local_counts = ((sync_state.get("local_sync") or {}).get("counts")) if isinstance(sync_state.get("local_sync"), dict) else None

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
            "cache_source": cache_meta["cache_source"],
            "last_refreshed_at": cache_meta["last_refreshed_at"],
            "cache_age_hours": cache_meta["cache_age_hours"],
            "is_cache_stale": cache_meta["is_cache_stale"],
            "local_sync_counts": local_counts,
        },
    }
