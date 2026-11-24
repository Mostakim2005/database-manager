"""Sitemap indexer module for Media domain."""

from __future__ import annotations

import re
from pathlib import Path

from media import SITEMAPS_DIR

_LOC_RE = re.compile(r"<loc>(https://comix\.to/title/[^<]+)</loc>")


def build_index(sitemaps_dir: Path = SITEMAPS_DIR, allow_missing: bool = False) -> list[str]:
    """Extract all canonical ``comix.to/title/`` URLs from cached XML sitemaps."""
    if not sitemaps_dir.exists():
        if allow_missing:
            return []
        raise FileNotFoundError(f"Sitemaps directory not found at {sitemaps_dir}. Run crawler first.")

    urls: list[str] = []
    xml_files = sorted(sitemaps_dir.glob("*.xml"))
    for fpath in xml_files:
        matches = _LOC_RE.findall(fpath.read_text(encoding="utf-8", errors="replace"))
        urls.extend(matches)

    print(f"[media.indexer] Indexed {len(urls)} URLs across {len(xml_files)} sitemap files.")
    return urls
