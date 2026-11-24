"""Slug and title matcher module for Media domain."""

from __future__ import annotations

import re
import urllib.parse

from media.indexer import build_index


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def resolve_title_url(
    query: str,
    patterns: list[str] | None = None,
    indexed_urls: list[str] | None = None,
) -> str:
    """Resolve a title query to a canonical ``comix.to/title/`` URL or browse fallback."""
    if indexed_urls is None:
        indexed_urls = build_index(allow_missing=True)

    search_patterns = patterns or [_slugify(query)]
    search_patterns = [p.lower() for p in search_patterns if p]

    for p in search_patterns:
        candidates = [
            u for u in indexed_urls
            if p in u.lower() and "doujinshi" not in u.lower() and "omakes" not in u.lower()
        ]
        if not candidates:
            candidates = [u for u in indexed_urls if p in u.lower()]
        if candidates:
            return min(candidates, key=len)

    encoded = urllib.parse.quote(query)
    return f"https://comix.to/browse?q={encoded}&sort=relevance%3Adesc"
