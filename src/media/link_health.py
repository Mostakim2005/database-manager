"""Streaming & Reading Link Health Checker for Media Domain."""

from __future__ import annotations

import datetime
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from media import CATALOG_JSON_PATH, load_catalog
from media.fetch_helper import probe_url_status

_URL_RE = re.compile(r"https?://[^\s\)\]>\"']+")


def extract_catalog_links(catalog: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Extract normalized link records across link, links, anime, and live_action fields."""
    extracted: list[dict[str, str]] = []
    for item in catalog:
        title = str(item.get("name", "Unknown"))
        seen_item_urls: set[str] = set()
        for field in ("link", "anime", "live_action"):
            text = str(item.get(field, ""))
            for raw_url in _URL_RE.findall(text):
                url = raw_url.rstrip(".,;:")
                if url in seen_item_urls:
                    continue
                seen_item_urls.add(url)
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
        for lk in item.get("links") or []:
            if not isinstance(lk, dict):
                continue
            url = str(lk.get("url") or "").strip().rstrip(".,;:")
            if not url or url in seen_item_urls:
                continue
            seen_item_urls.add(url)
            parsed = urlparse(url)
            kind = "browse_search" if "browse?q=" in url or "search_query=" in url or "/search?" in url else "direct"
            extracted.append(
                {
                    "title": title,
                    "field": "links",
                    "url": url,
                    "host": parsed.netloc.lower(),
                    "kind": kind,
                }
            )
    return extracted


def audit_catalog_links_offline(catalog_path: Path = CATALOG_JSON_PATH) -> dict[str, Any]:
    """Audit syntax, host breakdown, and direct vs search fallback counts offline."""
    catalog = load_catalog(catalog_path)
    links = extract_catalog_links(catalog)
    malformed = [
        entry for entry in links
        if not entry["host"] or not entry["url"].startswith(("http://", "https://"))
    ]
    hosts = Counter(entry["host"] for entry in links)
    kinds = Counter(entry["kind"] for entry in links)

    return {
        "mode": "offline",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_titles": len(catalog),
        "total_links": len(links),
        "malformed_count": len(malformed),
        "malformed_links": malformed,
        "kind_counts": dict(kinds),
        "top_hosts": dict(hosts.most_common(12)),
        "healthy": len(malformed) == 0 and len(links) > 0,
    }


def check_catalog_links_live(
    catalog_path: Path = CATALOG_JSON_PATH,
    limit: int = 10,
    host_filter: str | None = None,
    delay_sec: float = 0.75,
) -> dict[str, Any]:
    """Politely probe up to `limit` unique direct URLs in the catalog."""
    catalog = load_catalog(catalog_path)
    links = extract_catalog_links(catalog)

    seen: set[str] = set()
    targets: list[dict[str, str]] = []
    for entry in links:
        if entry["kind"] != "direct":
            continue
        if host_filter and host_filter.lower() not in entry["host"]:
            continue
        if entry["url"] not in seen:
            seen.add(entry["url"])
            targets.append(entry)
        if len(targets) >= limit:
            break

    results: list[dict[str, Any]] = []
    for target in targets:
        probe = probe_url_status(target["url"], delay_sec=delay_sec)
        results.append({**target, **probe})

    state_counts = Counter(r["state"] for r in results)
    broken = [r for r in results if r["state"] == "broken"]
    return {
        "mode": "live",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "probed_count": len(results),
        "state_counts": dict(state_counts),
        "broken_links": broken,
        "results": results,
    }
