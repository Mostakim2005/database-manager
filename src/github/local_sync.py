"""GitHub Domain — Local vs. Web Repository Reconciliation Engine.

Discovers local Git repositories across configured workspace roots using
non-interactive `git` (`GIT_TERMINAL_PROMPT=0`), detects dirty working trees,
unpushed ahead/behind commit counts, and reconciles local clones against the
GitHub web inventory to surface local-only, uncloned/web-only, and newly deleted
repositories (local or remote).

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
GITHUB_DATA_DIR = ROOT_DIR / "data" / "github"
LOCAL_ROOTS_FILE = GITHUB_DATA_DIR / "local_roots.json"

_GIT_TIMEOUT_SECONDS = 5
_IGNORED_DIR_NAMES = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


def normalize_github_slug(remote_url: str | None) -> str | None:
    """Normalize a GitHub HTTP/SSH remote URL into lowercase `owner/repo`."""
    raw = str(remote_url or "").strip()
    if not raw:
        return None
    patterns = (
        r"github\.com[:/]([^/\s]+/[^/\s]+?)(?:\.git)?/?$",
    )
    for pat in patterns:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            slug = m.group(1).strip().rstrip("/")
            if slug.lower().endswith(".git"):
                slug = slug[:-4]
            return slug.lower()
    return None


def discover_default_roots() -> list[Path]:
    """Resolve local workspace root directories dynamically without hardcoded user names."""
    env_roots = os.environ.get("DATABASE_MANAGER_LOCAL_ROOTS", "").strip()
    if env_roots:
        paths = [Path(p.strip()) for p in env_roots.split(os.pathsep) if p.strip()]
        return [p for p in paths if p.is_dir()]

    if LOCAL_ROOTS_FILE.is_file():
        try:
            loaded = json.loads(LOCAL_ROOTS_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                paths = [Path(str(p)) for p in loaded if str(p).strip()]
                valid = [p for p in paths if p.is_dir()]
                if valid:
                    return valid
        except (OSError, json.JSONDecodeError):
            pass

    candidates: list[Path] = []
    reg_env = os.environ.get("LOCAL_ECOSYSTEM_REGISTRY")
    reg_paths = [
        Path(reg_env) if reg_env else Path.home() / ".local" / "share" / "ecosystem-registry.json",
        Path(os.environ.get("LOCALAPPDATA", "")) / "SharedLibraries" / "ecosystem-registry.json",
    ]
    for reg_path in reg_paths:
        if reg_path.is_file():
            try:
                reg = json.loads(reg_path.read_text(encoding="utf-8"))
                harness_dir = (reg.get("paths") or {}).get("agenticHarness")
                if harness_dir and Path(harness_dir).is_dir():
                    candidates.append(Path(harness_dir))
                    break
            except (OSError, json.JSONDecodeError):
                pass

    if not candidates and ROOT_DIR.parent.is_dir():
        candidates.append(ROOT_DIR.parent)

    return candidates


def save_local_roots(roots: list[str | Path], target_path: Path | None = None) -> list[str]:
    """Persist custom local workspace scan roots cleanly in UTF-8 without BOM."""
    dest = target_path or LOCAL_ROOTS_FILE
    dest.parent.mkdir(parents=True, exist_ok=True)
    cleaned = [str(Path(r)) for r in roots if str(r).strip()]
    dest.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return cleaned


def _run_git(cwd: Path, args: list[str], timeout: int = _GIT_TIMEOUT_SECONDS) -> tuple[int, str]:
    """Execute a git command safely without interactive credential prompts."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        return proc.returncode, (proc.stdout or "").strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return 1, ""


def _inspect_git_repo(repo_dir: Path) -> dict[str, Any]:
    """Gather branch, remote, dirty status, ahead/behind counts, and HEAD commit."""
    _, origin_url = _run_git(repo_dir, ["remote", "get-url", "origin"])
    _, branch = _run_git(repo_dir, ["rev-parse", "--abbrev-ref", "HEAD"])
    rc_status, status_out = _run_git(repo_dir, ["status", "--porcelain"])
    dirty_lines = [ln for ln in status_out.splitlines() if ln.strip()] if rc_status == 0 else []

    ahead_by = 0
    behind_by = 0
    has_upstream = False
    rc_up, up_counts = _run_git(repo_dir, ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"])
    if rc_up == 0 and up_counts:
        parts = up_counts.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            has_upstream = True
            ahead_by = int(parts[0])
            behind_by = int(parts[1])

    rc_log, log_line = _run_git(repo_dir, ["log", "-1", "--format=%H|%cI|%s"])
    head_sha = ""
    head_date = ""
    head_message = ""
    if rc_log == 0 and log_line:
        chunks = log_line.split("|", 2)
        if len(chunks) == 3:
            head_sha, head_date, head_message = chunks[0][:7], chunks[1], chunks[2]

    return {
        "folder_name": repo_dir.name,
        "local_path": str(repo_dir),
        "origin_url": origin_url,
        "github_slug": normalize_github_slug(origin_url),
        "branch": branch or "HEAD",
        "dirty_count": len(dirty_lines),
        "is_dirty": len(dirty_lines) > 0,
        "has_upstream": has_upstream,
        "ahead_by": ahead_by,
        "behind_by": behind_by,
        "head_sha": head_sha,
        "head_date": head_date,
        "head_message": head_message,
    }


def scan_local_git_repos(roots: list[Path] | None = None, max_depth: int = 2) -> list[dict[str, Any]]:
    """Scan workspace roots (up to `max_depth`) for local Git repositories."""
    scan_roots = roots if roots is not None else discover_default_roots()
    seen_paths: set[str] = set()
    discovered: list[dict[str, Any]] = []

    def _walk(directory: Path, depth: int) -> None:
        if not directory.is_dir() or depth > max_depth:
            return
        if (directory / ".git").exists():
            resolved = str(directory.resolve())
            if resolved not in seen_paths:
                seen_paths.add(resolved)
                discovered.append(_inspect_git_repo(directory))
            return
        if depth == max_depth:
            return
        try:
            children = sorted(
                (p for p in directory.iterdir() if p.is_dir() and p.name not in _IGNORED_DIR_NAMES and not p.name.startswith(".")),
                key=lambda p: p.name.lower(),
            )
        except OSError:
            return
        for child in children:
            _walk(child, depth + 1)

    for root in scan_roots:
        _walk(Path(root), 0)

    return discovered


def reconcile_local_with_web(
    web_repos: list[dict[str, Any]],
    local_repos: list[dict[str, Any]] | None = None,
    previous_state: dict[str, Any] | None = None,
    roots: list[Path] | None = None,
) -> dict[str, Any]:
    """Cross-match local Git clones against GitHub web repositories to detect drift or deletions."""
    local_list = local_repos if local_repos is not None else scan_local_git_repos(roots=roots)
    prev = previous_state if isinstance(previous_state, dict) else {}
    prev_web_slugs = {str(s).lower() for s in (prev.get("web_slugs") or []) if s}
    prev_local_slugs = {str(s).lower() for s in (prev.get("local_slugs") or []) if s}

    web_by_slug: dict[str, dict[str, Any]] = {}
    web_by_name: dict[str, dict[str, Any]] = {}
    for w in web_repos:
        full_name = str(w.get("full_name") or "").strip().lower()
        name = str(w.get("name") or "").strip().lower()
        if full_name:
            web_by_slug[full_name] = w
        if name:
            web_by_name[name] = w

    matched: list[dict[str, Any]] = []
    local_only: list[dict[str, Any]] = []
    matched_web_slugs: set[str] = set()
    current_local_identifiers: set[str] = set()

    for loc in local_list:
        slug = (loc.get("github_slug") or "").lower()
        ident = slug or f"local:{loc['folder_name'].lower()}"
        current_local_identifiers.add(ident)

        web_match = web_by_slug.get(slug) if slug else None
        if web_match is None and not slug:
            web_match = web_by_name.get(loc["folder_name"].lower())

        if web_match is not None:
            w_slug = str(web_match.get("full_name") or web_match.get("name") or "").lower()
            matched_web_slugs.add(w_slug)
            if loc["ahead_by"] > 0 and loc["behind_by"] > 0:
                sync_status = "diverged"
            elif loc["ahead_by"] > 0:
                sync_status = "ahead"
            elif loc["behind_by"] > 0:
                sync_status = "behind"
            elif loc["is_dirty"]:
                sync_status = "dirty"
            else:
                sync_status = "synced"

            matched.append(
                {
                    **loc,
                    "web_full_name": web_match.get("full_name"),
                    "web_name": web_match.get("name"),
                    "is_private": bool(web_match.get("is_private")),
                    "sync_status": sync_status,
                }
            )
        else:
            deleted_on_web = bool(slug and slug in prev_web_slugs)
            reason = "deleted_on_web" if deleted_on_web else ("remote_mismatch" if slug else "no_origin_remote")
            local_only.append(
                {
                    **loc,
                    "sync_status": reason,
                    "deleted_on_web": deleted_on_web,
                }
            )

    web_only: list[dict[str, Any]] = []
    current_web_slugs: set[str] = set()
    for w in web_repos:
        w_slug = str(w.get("full_name") or "").strip().lower()
        if w_slug:
            current_web_slugs.add(w_slug)
        if w_slug in matched_web_slugs:
            continue
        deleted_locally = w_slug in prev_local_slugs
        web_only.append(
            {
                "name": w.get("name"),
                "full_name": w.get("full_name"),
                "is_fork": bool(w.get("is_fork")),
                "is_private": bool(w.get("is_private")),
                "pushed_at": w.get("pushed_at"),
                "sync_status": "deleted_locally" if deleted_locally else "not_cloned_locally",
                "deleted_locally": deleted_locally,
            }
        )

    deleted_on_web_since_last = sorted(prev_web_slugs - current_web_slugs) if prev_web_slugs else []
    added_on_web_since_last = sorted(current_web_slugs - prev_web_slugs) if prev_web_slugs else []
    deleted_locally_since_last = sorted(prev_local_slugs - current_local_identifiers) if prev_local_slugs else []

    dirty_or_ahead = [m for m in matched if m["sync_status"] != "synced"]

    return {
        "checked_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scanned_roots": [str(p) for p in (roots if roots is not None else discover_default_roots())],
        "counts": {
            "local_total": len(local_list),
            "web_total": len(web_repos),
            "matched": len(matched),
            "synced": sum(1 for m in matched if m["sync_status"] == "synced"),
            "dirty_or_ahead": len(dirty_or_ahead),
            "local_only": len(local_only),
            "web_only": len(web_only),
            "deleted_on_web_since_last": len(deleted_on_web_since_last),
            "deleted_locally_since_last": len(deleted_locally_since_last),
            "added_on_web_since_last": len(added_on_web_since_last),
        },
        "matched": matched,
        "local_only": local_only,
        "web_only": web_only,
        "deleted_on_web_since_last": deleted_on_web_since_last,
        "deleted_locally_since_last": deleted_locally_since_last,
        "added_on_web_since_last": added_on_web_since_last,
        "current_web_slugs": sorted(current_web_slugs),
        "current_local_slugs": sorted(current_local_identifiers),
    }
