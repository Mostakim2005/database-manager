"""Streaming & Reading Link Health Checker for Manga Domain (Bravo 4).

Extracts all URLs across ``link``, ``anime``, and ``live_action`` fields in
``manga_catalog.json``, classifies them offline, and optionally performs polite
live HTTP checks via ``fetch_helper.probe_url_status``.
"""

from __future__ import annotations

import datetime
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from manga import CATALOG_JSON_PATH
from manga.fetch_helper import probe_url_status
from manga.sync_vault import load_catalog

_URL_RE = re.compile(r"https?://[^\s\)\]>\"']+")


def extract_catalog_links(catalog: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Extract normalized link records across reading, anime, and live-action fields."""
    extracted: list[dict[str, str]] = []
    for item in catalog:
        title = str(item.get("name", "Unknown"))
        for field in ("link", "anime", "live_action"):
            text = str(item.get(field, ""))
            for raw_url in _URL_RE.findall(text):
                url = raw_url.rstrip(".,;:")
                parsed = urlparse(url)
                kind = "browse_search" if "browse?q=" in url or "search_query=" in url or "/search?" in url else "direct"
                extracted.append(
                    {
                        "title": title,
                        "field": field,
                        "url": url,
                        "host": parsed.netloc.lower(),
                        "kind": kind,
                    }
                )
    return extracted


def audit_catalog_links_offline(catalog_path: Path = CATALOG_JSON_PATH) -> dict[str, Any]:
    """Perform offline structural & domain distribution audit over all catalog links."""
    catalog = load_catalog(catalog_path)
    links = extract_catalog_links(catalog)
    host_counts: Counter[str] = Counter(row["host"] for row in links)
    field_counts: Counter[str] = Counter(row["field"] for row in links)
    kind_counts: Counter[str] = Counter(row["kind"] for row in links)
    malformed = [row for row in links if not row["host"] or "." not in row["host"]]

    return {
        "mode": "offline",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_titles": len(catalog),
        "total_links": len(links),
        "field_counts": dict(field_counts),
        "kind_counts": dict(kind_counts),
        "top_hosts": dict(host_counts.most_common(15)),
        "malformed_count": len(malformed),
        "malformed_links": malformed,
        "healthy": len(malformed) == 0,
    }


def check_catalog_links_live(
    limit: int = 10,
    timeout: float = 8.0,
    delay_sec: float = 0.5,
    host_filter: str | None = None,
    catalog_path: Path = CATALOG_JSON_PATH,
) -> dict[str, Any]:
    """Politely probe up to ``limit`` unique direct URLs and report live HTTP health."""
    catalog = load_catalog(catalog_path)
    links = extract_catalog_links(catalog)
    if host_filter:
        links = [row for row in links if host_filter.lower() in row["host"]]

    seen: set[str] = set()
    targets: list[dict[str, str]] = []
    for row in links:
        if row["url"] not in seen:
            seen.add(row["url"])
            targets.append(row)
        if len(targets) >= max(1, limit):
            break

    results: list[dict[str, Any]] = []
    state_counts: Counter[str] = Counter()
    for row in targets:
        probe = probe_url_status(row["url"], timeout=timeout, delay_sec=delay_sec)
        merged = {**row, **probe}
        results.append(merged)
        state_counts[probe["state"]] += 1

    return {
        "mode": "live",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "probed_count": len(results),
        "state_counts": dict(state_counts),
        "broken_links": [r for r in results if not r["ok"]],
        "results": results,
    }
