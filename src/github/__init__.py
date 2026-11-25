"""GitHub Repositories & CI Health domain package for Database Manager."""

from .exporter import DEFAULT_REPORT_DESTINATION, export_markdown_report
from .local_sync import (
    discover_default_roots,
    normalize_github_slug,
    reconcile_local_with_web,
    save_local_roots,
    scan_local_git_repos,
)
from .scanner import (
    LIVE_CACHE_FILE,
    PUBLIC_CACHE_FILE,
    SYNC_STATE_FILE,
    cancel_background_refresh,
    get_cache_metadata,
    get_cached_repos,
    get_refresh_status,
    is_scan_in_progress,
    load_sync_state,
    redact_public_repos,
    refresh_single_repository,
    run_gh_api,
    run_local_sync_check,
    scan_all_repositories,
    start_background_refresh,
    triage_repositories,
)

__all__ = [
    "LIVE_CACHE_FILE",
    "PUBLIC_CACHE_FILE",
    "SYNC_STATE_FILE",
    "DEFAULT_REPORT_DESTINATION",
    "cancel_background_refresh",
    "discover_default_roots",
    "get_cache_metadata",
    "get_cached_repos",
    "get_refresh_status",
    "is_scan_in_progress",
    "load_sync_state",
    "normalize_github_slug",
    "reconcile_local_with_web",
    "redact_public_repos",
    "refresh_single_repository",
    "run_gh_api",
    "run_local_sync_check",
    "save_local_roots",
    "scan_all_repositories",
    "scan_local_git_repos",
    "start_background_refresh",
    "triage_repositories",
    "export_markdown_report",
]
