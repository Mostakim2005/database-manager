#!/usr/bin/env python3
"""Multi-tier HTTP/Scraper fallback router and --dry-run diff preview engine."""

from __future__ import annotations

import importlib.util
import json
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_USER_AGENT = "DatabaseManager/1.1 (+https://github.com/Mostakim2005/database-manager)"


@dataclass
class FetchResult:
    url: str
    tier_used: str
    status_code: int
    content: str
    ok: bool
    error: str = ""


def detect_installed_tiers() -> dict[str, dict[str, Any]]:
    """Probe which optional OSS scraping/validation libraries are installed."""
    checks = {
        "tier0_stdlib": ["urllib.request"],
        "tier1_httpx_selectolax": ["httpx", "selectolax"],
        "tier2_scrapling": ["scrapling"],
        "tier3_playwright": ["playwright"],
        "tier3_crawl4ai": ["crawl4ai"],
        "tier4_ytdlp": ["yt_dlp"],
        "validator_pydantic": ["pydantic"],
        "bridge_datasette": ["datasette"],
    }
    report: dict[str, dict[str, Any]] = {}
    for name, mods in checks.items():
        present = {m: (importlib.util.find_spec(m) is not None) for m in mods}
        report[name] = {"available": all(present.values()), "modules": present}
    return report


def fetch_tier0_urllib(url: str, timeout: int = 15) -> FetchResult:
    """Tier 0: Zero-dependency stdlib HTTP GET (best for official JSON APIs)."""
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json, text/html"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return FetchResult(url=url, tier_used="tier0_stdlib", status_code=resp.status, content=body, ok=200 <= resp.status < 300)
    except Exception as exc:
        return FetchResult(url=url, tier_used="tier0_stdlib", status_code=0, content="", ok=False, error=str(exc))


def fetch_tier1_httpx(url: str, timeout: int = 15) -> FetchResult:
    """Tier 1: Fast HTTP/2 client via httpx."""
    if importlib.util.find_spec("httpx") is None:
        return FetchResult(url=url, tier_used="tier1_httpx", status_code=0, content="", ok=False, error="httpx not installed")
    import httpx  # type: ignore[import-not-found]
    try:
        with httpx.Client(http2=False, follow_redirects=True, timeout=timeout, headers={"User-Agent": DEFAULT_USER_AGENT}) as client:
            resp = client.get(url)
            ok = 200 <= resp.status_code < 300 and "cf-browser-verification" not in resp.text.lower()
            return FetchResult(url=url, tier_used="tier1_httpx", status_code=resp.status_code, content=resp.text, ok=ok)
    except Exception as exc:
        return FetchResult(url=url, tier_used="tier1_httpx", status_code=0, content="", ok=False, error=str(exc))


def fetch_tier2_scrapling(url: str, timeout: int = 25) -> FetchResult:
    """Tier 2: Adaptive stealth fetcher via Scrapling."""
    if importlib.util.find_spec("scrapling") is None:
        return FetchResult(url=url, tier_used="tier2_scrapling", status_code=0, content="", ok=False, error="scrapling not installed")
    try:
        from scrapling.fetchers import Fetcher  # type: ignore[import-not-found]
        page = Fetcher.get(url, timeout=timeout)
        text = getattr(page, "html_content", None) or str(getattr(page, "body", ""))
        status = int(getattr(page, "status", 200))
        return FetchResult(url=url, tier_used="tier2_scrapling", status_code=status, content=text, ok=200 <= status < 300)
    except Exception as exc:
        return FetchResult(url=url, tier_used="tier2_scrapling", status_code=0, content="", ok=False, error=str(exc))


def fetch_with_fallback(url: str, tiers: tuple[str, ...] = ("tier0", "tier1", "tier2"), timeout: int = 15) -> FetchResult:
    """Try configured scraper tiers in order until one succeeds."""
    dispatch = {
        "tier0": fetch_tier0_urllib,
        "tier1": fetch_tier1_httpx,
        "tier2": fetch_tier2_scrapling,
    }
    last = FetchResult(url=url, tier_used="none", status_code=0, content="", ok=False, error="No tiers executed")
    for t in tiers:
        fn = dispatch.get(t)
        if not fn:
            continue
        res = fn(url, timeout=timeout)
        if res.ok:
            return res
        last = res
    return last


def compute_record_diff(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
    key_field: str = "id",
) -> dict[str, Any]:
    """Compute structured dry-run diff (+ added, ~ changed, - removed, = unchanged)."""
    old_map = {str(r.get(key_field)): r for r in existing if r.get(key_field) is not None}
    new_map = {str(r.get(key_field)): r for r in incoming if r.get(key_field) is not None}

    added = [new_map[k] for k in sorted(new_map.keys() - old_map.keys())]
    removed = [old_map[k] for k in sorted(old_map.keys() - new_map.keys())]
    changed: list[dict[str, Any]] = []
    unchanged = 0

    for k in sorted(old_map.keys() & new_map.keys()):
        if json.dumps(old_map[k], sort_keys=True) != json.dumps(new_map[k], sort_keys=True):
            changed.append({"id": k, "before": old_map[k], "after": new_map[k]})
        else:
            unchanged += 1

    return {
        "added_count": len(added),
        "changed_count": len(changed),
        "removed_count": len(removed),
        "unchanged_count": unchanged,
        "added": added,
        "changed": changed,
        "removed": removed,
    }


def format_diff_report(diff: dict[str, Any], label: str = "Dry-Run Preview") -> str:
    """Format a compact human-readable dry-run diff summary."""
    lines = [
        f"=== {label} ===",
        f"  + Added:     {diff['added_count']}",
        f"  ~ Changed:   {diff['changed_count']}",
        f"  - Removed:   {diff['removed_count']}",
        f"  = Unchanged: {diff['unchanged_count']}",
    ]
    for item in diff["added"][:5]:
        lines.append(f"    + {item.get('id', item.get('name', 'item'))}")
    for item in diff["changed"][:5]:
        lines.append(f"    ~ {item['id']}")
    for item in diff["removed"][:5]:
        lines.append(f"    - {item.get('id', item.get('name', 'item'))}")
    return "\n".join(lines)
