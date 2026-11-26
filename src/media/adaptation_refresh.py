"""Automated Adaptation Refresh, Franchise Graph & Catalog Doctor Pipeline for Media domain."""

from __future__ import annotations

import datetime
import json
import re
import threading
import urllib.parse
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from media import CATALOG_JSON_PATH, SITEMAPS_DIR, load_catalog
from media.fetch_helper import safe_get
from media.franchise_builder import build_multi_tier_catalog, enrich_catalog_metadata
from media.indexer import build_index
from media.matcher import resolve_title_url
from media.poster_cache import POSTER_CACHE_DIR, get_cached_poster_bytes

_REFRESH_LOCK = threading.Lock()
_PROGRESS_LOCK = threading.Lock()
_CANCEL_EVENT = threading.Event()
_REFRESH_STATUS: dict[str, Any] = {
    "running": False,
    "job_id": None,
    "stage": "idle",
    "current": 0,
    "total": 0,
    "pct": 0,
    "message": "Idle",
    "started_at": None,
    "finished_at": None,
    "elapsed_seconds": 0.0,
    "cancel_requested": False,
    "error": None,
    "summary": None,
}

VALID_WATCHLIST_STATUSES = {
    "",
    "plan_to_read",
    "reading",
    "plan_to_watch",
    "watching",
    "completed",
    "paused",
    "dropped",
}


def _update_refresh_status(**kwargs: Any) -> dict[str, Any]:
    with _PROGRESS_LOCK:
        _REFRESH_STATUS.update(kwargs)
        return dict(_REFRESH_STATUS)


def get_media_refresh_status() -> dict[str, Any]:
    """Return thread-safe snapshot of current or last background media refresh job."""
    with _PROGRESS_LOCK:
        snap = dict(_REFRESH_STATUS)
    started = snap.get("started_at")
    finished = snap.get("finished_at")
    if started and snap.get("running") and not finished:
        try:
            dt = datetime.datetime.fromisoformat(str(started).replace("Z", "+00:00"))
            snap["elapsed_seconds"] = round(
                max(0.0, (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds()), 1
            )
        except ValueError:
            pass
    return snap


def cancel_background_media_refresh() -> dict[str, Any]:
    """Request cancellation of the active media refresh/poster-cache job."""
    if not _REFRESH_LOCK.locked():
        return {"status": "idle", "cancelled": False, "refresh": get_media_refresh_status()}
    _CANCEL_EVENT.set()
    return {
        "status": "cancelling",
        "cancelled": True,
        "refresh": _update_refresh_status(cancel_requested=True, message="Cancelling media metadata refresh…"),
    }


def start_background_media_refresh(
    franchise_id: str | None = None,
    download_posters: bool = True,
    catalog_path: Path = CATALOG_JSON_PATH,
) -> dict[str, Any]:
    """Start async background media metadata/poster enrichment job."""
    if not _REFRESH_LOCK.acquire(blocking=False):
        raise RuntimeError("Media metadata refresh already in progress")

    job_id = uuid.uuid4().hex[:10]
    _CANCEL_EVENT.clear()
    snap = _update_refresh_status(
        running=True,
        job_id=job_id,
        stage="probing",
        current=0,
        total=1,
        pct=4,
        message=f"Probing public sources ({franchise_id or 'all franchises'})…",
        started_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        finished_at=None,
        elapsed_seconds=0.0,
        cancel_requested=False,
        error=None,
        summary=None,
    )

    def _worker() -> None:
        t0 = datetime.datetime.now(datetime.timezone.utc)
        try:
            catalog = load_catalog(catalog_path)
            expanded, build_stats = build_multi_tier_catalog(catalog, include_obsidian_batch=True)

            def _on_prog(done: int, total: int, fid: str) -> None:
                pct = min(96, max(5, int((done / max(1, total)) * 95)))
                _update_refresh_status(
                    current=done,
                    total=total,
                    pct=pct,
                    message=f"Checked {done}/{total} franchises ({fid})…",
                )

            enrich_stats = enrich_catalog_metadata(
                expanded,
                franchise_filter=franchise_id,
                download_posters=download_posters,
                progress_cb=_on_prog,
                cancel_check=_CANCEL_EVENT.is_set,
            )
            if not enrich_stats.get("cancelled"):
                catalog_path.write_text(json.dumps(expanded, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            elapsed = round((datetime.datetime.now(datetime.timezone.utc) - t0).total_seconds(), 1)
            _update_refresh_status(
                running=False,
                stage="cancelled" if enrich_stats.get("cancelled") else "done",
                current=enrich_stats["franchises_scanned"],
                total=enrich_stats["total_franchises"],
                pct=100 if not enrich_stats.get("cancelled") else snap.get("pct", 50),
                message=(
                    f"Cancelled after {enrich_stats['franchises_scanned']} franchises."
                    if enrich_stats.get("cancelled")
                    else f"Synced {enrich_stats['franchises_scanned']} franchises ({enrich_stats['posters_cached']} posters cached, {enrich_stats['metadata_updated']} entries enriched)."
                ),
                finished_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                elapsed_seconds=elapsed,
                summary={"build": build_stats, "enrich": enrich_stats},
            )
        except Exception as exc:
            elapsed = round((datetime.datetime.now(datetime.timezone.utc) - t0).total_seconds(), 1)
            _update_refresh_status(
                running=False,
                stage="error",
                message=f"Media refresh failed: {exc}",
                finished_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                elapsed_seconds=elapsed,
                error=str(exc),
            )
        finally:
            _REFRESH_LOCK.release()

    t = threading.Thread(target=_worker, daemon=True, name="media-async-refresh")
    t.start()
    return snap


def update_media_entry_status(
    entry_id: str,
    watchlist_status: str,
    catalog_path: Path = CATALOG_JSON_PATH,
) -> dict[str, Any]:
    """Persist per-entry Watch/Read status (`watchlist_status`) safely to JSON."""
    clean_id = str(entry_id or "").strip()
    clean_status = str(watchlist_status or "").strip().lower()
    if not clean_id:
        raise ValueError("Entry id is required")
    if clean_status not in VALID_WATCHLIST_STATUSES:
        raise ValueError(f"Unsupported watchlist_status: {clean_status}")

    catalog = load_catalog(catalog_path)
    target = next((item for item in catalog if str(item.get("id", "")).strip() == clean_id), None)
    if target is None:
        raise LookupError(f"Media entry not found: {clean_id}")
    target["watchlist_status"] = clean_status
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"status": "ok", "id": clean_id, "watchlist_status": clean_status}


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

    with_posters = sum(1 for item in catalog if str(item.get("poster_url", "")).strip())
    with_descriptions = sum(1 for item in catalog if str(item.get("description", "")).strip())
    nsfw_count = sum(1 for item in catalog if item.get("nsfw"))
    franchises_count = len({str(item.get("franchise_id") or item.get("id") or "") for item in catalog})
    cached_on_disk = (
        sum(1 for item in catalog if get_cached_poster_bytes(str(item.get("id", "")), cached_filename=str(item.get("poster_cached_file", ""))) is not None)
        if POSTER_CACHE_DIR.is_dir()
        else 0
    )

    return {
        "total_titles": len(catalog),
        "franchises_count": franchises_count,
        "direct_comix_links": direct_links,
        "browse_fallback_count": len(browse_fallbacks),
        "browse_fallback_titles": browse_fallbacks,
        "with_anime_or_motion": with_anime,
        "with_live_action": with_live_action,
        "in_production_count": in_production,
        "with_relations": with_relations,
        "with_posters": with_posters,
        "cached_posters_on_disk": cached_on_disk,
        "with_descriptions": with_descriptions,
        "nsfw_count": nsfw_count,
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
