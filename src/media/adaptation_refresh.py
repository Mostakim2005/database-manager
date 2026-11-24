"""Automated Adaptation Refresh, Franchise Graph & Catalog Doctor Pipeline for Media domain."""

from __future__ import annotations

import datetime
import json
import re
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Any

from media import CATALOG_JSON_PATH, SITEMAPS_DIR, load_catalog
from media.fetch_helper import safe_get
from media.indexer import build_index
from media.matcher import resolve_title_url


def _clean_slug_patterns(name: str, alt: str = "") -> list[str]:
    patterns: list[str] = []
    for raw in [name] + [part.strip() for part in re.split(r"[/,;()]+", alt or "") if part.strip()]:
        slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
        if len(slug) >= 4 and slug not in patterns:
            patterns.append(slug)
    return patterns


def inspect_catalog_doctor(catalog: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit media catalog consistency, duplicates, link types, subdomain coverage & relations."""
    names = [str(item.get("name", "")).strip() for item in catalog]
    dups = [name for name, cnt in Counter(n.lower() for n in names if n).items() if cnt > 1]

    missing_fields: list[dict[str, Any]] = []
    browse_fallbacks: list[str] = []
    direct_links = 0
    with_anime = 0
    with_live_action = 0
    in_production = 0
    with_relations = 0
    origin_counts: Counter[str] = Counter()
    media_type_counts: Counter[str] = Counter()

    for idx, item in enumerate(catalog):
        name = str(item.get("name", "")).strip() or f"row-{idx}"
        missing = [k for k in ("id", "name", "media_type", "link", "origin", "anime", "live_action") if not str(item.get(k, "")).strip()]
        if missing:
            missing_fields.append({"name": name, "missing": missing})

        link = str(item.get("link", ""))
        if "comix.to/title/" in link:
            direct_links += 1
        elif "browse?q=" in link:
            browse_fallbacks.append(name)

        anime = str(item.get("anime", ""))
        live = str(item.get("live_action", ""))
        if not anime.startswith("**None**"):
            with_anime += 1
        if not live.startswith("**None**"):
            with_live_action += 1
        if "in production" in (anime + " " + live).lower():
            in_production += 1
        if item.get("relations"):
            with_relations += 1
        origin_counts[str(item.get("origin", "Unknown"))] += 1
        media_type_counts[str(item.get("media_type", "comic"))] += 1

    return {
        "total_titles": len(catalog),
        "direct_comix_links": direct_links,
        "browse_fallback_count": len(browse_fallbacks),
        "browse_fallback_titles": browse_fallbacks,
        "with_anime_or_motion": with_anime,
        "with_live_action": with_live_action,
        "in_production_count": in_production,
        "with_relations": with_relations,
        "media_type_counts": dict(media_type_counts),
        "duplicate_names": dups,
        "missing_fields": missing_fields,
        "origin_counts": dict(origin_counts),
        "healthy": len(dups) == 0 and len(missing_fields) == 0,
    }


def propose_link_upgrades(
    catalog: list[dict[str, Any]],
    sitemaps_dir: Path = SITEMAPS_DIR,
) -> list[dict[str, str]]:
    """Propose canonical ``comix.to/title/`` upgrades for comic entries currently using browse?q=."""
    indexed_urls = build_index(sitemaps_dir=sitemaps_dir, allow_missing=True)
    if not indexed_urls:
        return []

    proposals: list[dict[str, str]] = []
    for item in catalog:
        link = str(item.get("link", ""))
        if "comix.to/title/" in link or "browse?q=" not in link:
            continue
        name = str(item.get("name", ""))
        alt = str(item.get("alt", ""))
        patterns = _clean_slug_patterns(name, alt)
        candidate = resolve_title_url(name, patterns=patterns, indexed_urls=indexed_urls)
        if "comix.to/title/" in candidate and candidate != link:
            proposals.append(
                {
                    "name": name,
                    "old_link": link,
                    "proposed_link": candidate,
                    "source": "comix_sitemap_index",
                }
            )
    return proposals


def probe_public_adaptation_sources(
    title: str,
    alt: str = "",
    delay_sec: float = 1.0,
) -> dict[str, Any]:
    """Probe reachable public sources (IMDb suggestion JSON, MyDramaList, YouTube, DDG)."""
    query = title.strip()
    first_char = re.sub(r"[^a-z0-9]", "", query.lower())[:1] or "a"
    encoded = urllib.parse.quote(query)
    findings: dict[str, Any] = {"title": query, "alt": alt, "sources": {}}

    imdb_url = f"https://v3.sg.media-imdb.com/suggestion/{first_char}/{encoded}.json"
    imdb_res = safe_get(imdb_url, delay_sec=delay_sec, retries=1)
    if imdb_res and imdb_res[0] == 200:
        try:
            payload = json.loads(imdb_res[1])
            hits = [
                {"id": d.get("id"), "title": d.get("l"), "year": d.get("y"), "type": d.get("q")}
                for d in payload.get("d", [])[:5]
                if isinstance(d, dict)
            ]
            findings["sources"]["imdb"] = {"ok": True, "hits": hits}
        except Exception as exc:
            findings["sources"]["imdb"] = {"ok": False, "error": str(exc)}
    else:
        findings["sources"]["imdb"] = {"ok": False, "status": imdb_res[0] if imdb_res else 0}

    mdl_url = f"https://mydramalist.com/search?q={encoded}"
    mdl_res = safe_get(mdl_url, referer="https://mydramalist.com/", delay_sec=delay_sec, retries=1)
    if mdl_res and mdl_res[0] == 200:
        titles_found = re.findall(r'class="text-primary title"[^>]*>\s*<a[^>]*>([^<]+)</a>', mdl_res[1])[:5]
        findings["sources"]["mydramalist"] = {"ok": True, "url": mdl_url, "matches": titles_found}
    else:
        findings["sources"]["mydramalist"] = {"ok": False, "status": mdl_res[0] if mdl_res else 0}

    yt_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query + ' anime donghua trailer')}"
    yt_res = safe_get(yt_url, referer="https://www.youtube.com/", delay_sec=delay_sec, retries=1)
    findings["sources"]["youtube"] = {
        "ok": bool(yt_res and yt_res[0] == 200),
        "url": yt_url,
    }

    ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query + ' anime OR donghua OR drama OR movie')}"
    ddg_res = safe_get(ddg_url, referer="https://html.duckduckgo.com/", delay_sec=delay_sec, retries=1)
    if ddg_res and ddg_res[0] == 200:
        snippets = re.findall(r'class="result__a"[^>]*>([^<]+)</a>', ddg_res[1])[:5]
        findings["sources"]["duckduckgo"] = {"ok": True, "snippets": snippets}
    else:
        findings["sources"]["duckduckgo"] = {"ok": False, "status": ddg_res[0] if ddg_res else 0}

    return findings


def apply_link_proposals(
    proposals: list[dict[str, str]],
    catalog_path: Path = CATALOG_JSON_PATH,
) -> int:
    """Apply approved canonical comix.to link upgrades to ``media_catalog.json``."""
    if not proposals:
        return 0
    catalog = load_catalog(catalog_path)
    by_name = {p["name"]: p["proposed_link"] for p in proposals}
    updated = 0
    for item in catalog:
        name = item.get("name", "")
        if name in by_name and item.get("link") != by_name[name]:
            item["link"] = by_name[name]
            updated += 1
    if updated > 0:
        catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return updated


def add_catalog_entry(
    name: str,
    origin: str = "Manga",
    media_type: str = "comic",
    alt: str = "",
    anime: str = "**None**",
    live_action: str = "**None**",
    franchise_id: str = "",
    catalog_path: Path = CATALOG_JSON_PATH,
    sitemaps_dir: Path = SITEMAPS_DIR,
    apply: bool = False,
) -> dict[str, Any]:
    """Build (and optionally persist) a new media entry across any subdomain."""
    catalog = load_catalog(catalog_path)
    existing = {str(x.get("name", "")).strip().lower() for x in catalog}
    if name.strip().lower() in existing:
        return {"added": False, "reason": f"Title '{name}' already exists in catalog."}

    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-") or "media-item"
    if media_type == "comic":
        indexed = build_index(sitemaps_dir=sitemaps_dir, allow_missing=True)
        link = resolve_title_url(name, patterns=_clean_slug_patterns(name, alt), indexed_urls=indexed)
    else:
        link = f"https://www.imdb.com/find/?q={urllib.parse.quote(name.strip())}"

    entry = {
        "id": slug,
        "name": name.strip(),
        "alt": alt.strip() or name.strip(),
        "media_type": media_type,
        "link": link,
        "origin": origin.strip(),
        "anime": anime.strip(),
        "live_action": live_action.strip(),
        "franchise_id": franchise_id.strip() or slug,
        "relations": [],
    }
    if apply:
        catalog.append(entry)
        catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"added": apply, "proposed_entry": entry, "total_after": len(catalog) + (1 if apply else 0)}


def run_adaptation_refresh(
    mode: str = "doctor",
    title: str | None = None,
    origin: str = "Manga",
    media_type: str = "comic",
    alt: str = "",
    apply: bool = False,
    limit: int = 5,
    catalog_path: Path = CATALOG_JSON_PATH,
    sitemaps_dir: Path = SITEMAPS_DIR,
) -> dict[str, Any]:
    """Run requested adaptation refresh mode (doctor, propose, update, add, all)."""
    catalog = load_catalog(catalog_path)
    report: dict[str, Any] = {
        "mode": mode,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    if mode in ("doctor", "all"):
        report["doctor"] = inspect_catalog_doctor(catalog)

    if mode in ("propose", "update", "all"):
        proposals = propose_link_upgrades(catalog, sitemaps_dir=sitemaps_dir)
        report["link_proposals"] = proposals
        if apply and proposals:
            report["applied_link_upgrades"] = apply_link_proposals(proposals, catalog_path=catalog_path)

    if mode in ("update", "all") and title:
        report["source_probe"] = probe_public_adaptation_sources(title, alt=alt)
    elif mode == "update" and not title:
        probes = []
        for item in catalog[:max(1, limit)]:
            if "browse?q=" in str(item.get("link", "")):
                probes.append(probe_public_adaptation_sources(item["name"], alt=item.get("alt", "")))
        report["batch_probes"] = probes

    if mode == "add":
        if not title:
            raise ValueError("--title is required when using --add")
        report["add_result"] = add_catalog_entry(
            name=title,
            origin=origin,
            media_type=media_type,
            alt=alt,
            catalog_path=catalog_path,
            sitemaps_dir=sitemaps_dir,
            apply=apply,
        )

    return report
