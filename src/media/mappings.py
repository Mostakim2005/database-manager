"""Shared cross-platform media ID mappings, RapidFuzz matching & adaptation discovery."""

from __future__ import annotations

import json
import os
import re
import threading
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from rapidfuzz import fuzz as _rf_fuzz  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional acceleration
    _rf_fuzz = None

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

_ANILIST_ID_RE = re.compile(r"anilist\.co/(?:anime|manga)/(\d+)", re.IGNORECASE)
_MAL_ID_RE = re.compile(r"myanimelist\.net/(?:anime|manga)/(\d+)", re.IGNORECASE)
_IMDB_ID_RE = re.compile(r"(tt\d{6,})", re.IGNORECASE)
_BGM_ID_RE = re.compile(r"(?:bgm\.tv|bangumi\.tv)/subject/(\d+)", re.IGNORECASE)
_AODB_SRC_RE = re.compile(
    r"(anilist\.co/anime|myanimelist\.net/anime|kitsu\.(?:app|io)/anime|anidb\.net/anime)/(\d+)",
    re.IGNORECASE,
)

_CACHE_LOCK = threading.Lock()
_DATASET_CACHE: dict[str, Any] = {}


def resolve_shared_mappings_dir(override: Path | str | None = None) -> Path | None:
    """Locate `%LOCALAPPDATA%\\SharedLibraries\\media-mappings` or registry override if present."""
    if override:
        p = Path(override)
        return p if p.is_dir() else None

    env_dir = os.environ.get("MEDIA_MAPPINGS_DIR", "").strip()
    if env_dir:
        p = Path(env_dir)
        if p.is_dir():
            return p

    local_app = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app:
        cand = Path(local_app) / "SharedLibraries" / "media-mappings"
        if cand.is_dir():
            return cand

    reg_path = Path.home() / ".local" / "share" / "ecosystem-registry.json"
    if reg_path.is_file():
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
            paths = reg.get("paths") or {}
            mm = paths.get("mediaMappings")
            if mm and Path(mm).is_dir():
                return Path(mm)
            cl = paths.get("commonLibraries")
            if cl and (Path(cl) / "media-mappings").is_dir():
                return Path(cl) / "media-mappings"
        except Exception:
            pass

    fallback = Path.home() / "AppData" / "Local" / "SharedLibraries" / "media-mappings"
    return fallback if fallback.is_dir() else None


def normalize_title_key(text: str) -> str:
    """Normalize title for punctuation-insensitive matching."""
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def compute_title_similarity(query: str, candidate: str) -> float:
    """Compute fuzzy similarity combining word overlap, compact romanization, and RapidFuzz."""
    q_norm = normalize_title_key(query)
    c_norm = normalize_title_key(candidate)
    if not q_norm or not c_norm:
        return 0.0
    if q_norm == c_norm:
        return 1.0

    q_compact = q_norm.replace(" ", "")
    c_compact = c_norm.replace(" ", "")
    if len(q_compact) >= 5 and q_compact == c_compact:
        return 0.98

    q_words = set(q_norm.split())
    c_words = set(c_norm.split())
    inter = len(q_words & c_words)
    ratio = inter / max(len(q_words), len(c_words))

    if len(q_words) >= 3 and (q_norm in c_norm or c_norm in q_norm):
        ratio = max(ratio, 0.80)

    if _rf_fuzz is not None:
        compact_rf = _rf_fuzz.ratio(q_compact, c_compact) / 100.0
        if compact_rf >= 0.88:
            ratio = max(ratio, compact_rf)
        tok_rf = _rf_fuzz.token_sort_ratio(q_norm, c_norm) / 100.0
        if len(q_words) >= 2 and len(c_words) >= 2 and tok_rf >= 0.84:
            ratio = max(ratio, tok_rf * 0.96)

    return min(1.0, ratio)


def _load_json_cached(path: Path) -> Any:
    if not path.is_file():
        return None
    key = f"{path.resolve()}::{path.stat().st_mtime_ns}"
    with _CACHE_LOCK:
        if key in _DATASET_CACHE:
            return _DATASET_CACHE[key]
    data = json.loads(path.read_text(encoding="utf-8"))
    with _CACHE_LOCK:
        _DATASET_CACHE[key] = data
    return data


def _parse_aodb_sources(sources: list[str]) -> dict[str, int]:
    ids: dict[str, int] = {}
    for s in sources or []:
        m = _AODB_SRC_RE.search(str(s))
        if not m:
            continue
        host, num = m.group(1).lower(), int(m.group(2))
        if "anilist" in host:
            ids["anilist_id"] = num
        elif "myanimelist" in host:
            ids["mal_id"] = num
        elif "kitsu" in host:
            ids["kitsu_id"] = num
        elif "anidb" in host:
            ids["anidb_id"] = num
    return ids


def _build_fribb_index(mappings_dir: Path) -> dict[str, dict[Any, dict[str, Any]]]:
    p = mappings_dir / "fribb-anime-list-full.json"
    if not p.is_file():
        return {"anilist": {}, "mal": {}, "imdb": {}}
    key = f"idx:fribb:{p.resolve()}:{p.stat().st_mtime_ns}"
    with _CACHE_LOCK:
        if key in _DATASET_CACHE:
            return _DATASET_CACHE[key]
    rows = _load_json_cached(p) or []
    by_al: dict[int, dict[str, Any]] = {}
    by_mal: dict[int, dict[str, Any]] = {}
    by_imdb: dict[str, dict[str, Any]] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        if r.get("anilist_id"):
            by_al.setdefault(int(r["anilist_id"]), r)
        if r.get("mal_id"):
            by_mal.setdefault(int(r["mal_id"]), r)
        imdb_val = r.get("imdb_id")
        if isinstance(imdb_val, list):
            for iv in imdb_val:
                if iv:
                    by_imdb.setdefault(str(iv).lower(), r)
        elif isinstance(imdb_val, str) and imdb_val:
            by_imdb.setdefault(imdb_val.lower(), r)
    idx = {"anilist": by_al, "mal": by_mal, "imdb": by_imdb}
    with _CACHE_LOCK:
        _DATASET_CACHE[key] = idx
    return idx


def _build_aodb_index(mappings_dir: Path) -> dict[str, Any]:
    p = mappings_dir / "anime-offline-database-minified.json"
    if not p.is_file():
        return {"by_anilist": {}, "by_mal": {}, "entries": []}
    key = f"idx:aodb:{p.resolve()}:{p.stat().st_mtime_ns}"
    with _CACHE_LOCK:
        if key in _DATASET_CACHE:
            return _DATASET_CACHE[key]
    raw = _load_json_cached(p) or {}
    entries = raw.get("data") if isinstance(raw, dict) else []
    by_al: dict[int, dict[str, Any]] = {}
    by_mal: dict[int, dict[str, Any]] = {}
    for e in entries or []:
        if not isinstance(e, dict):
            continue
        ids = _parse_aodb_sources(e.get("sources") or [])
        if ids.get("anilist_id"):
            by_al.setdefault(ids["anilist_id"], e)
        if ids.get("mal_id"):
            by_mal.setdefault(ids["mal_id"], e)
    idx = {"by_anilist": by_al, "by_mal": by_mal, "entries": entries or []}
    with _CACHE_LOCK:
        _DATASET_CACHE[key] = idx
    return idx


def get_dataset_inventory(mappings_dir: Path | str | None = None) -> dict[str, Any]:
    """Return status and file sizes of installed SharedLibraries mapping datasets."""
    mdir = resolve_shared_mappings_dir(mappings_dir)
    names = {
        "anime_offline_db": "anime-offline-database-minified.json",
        "anibridge_mappings": "anibridge-mappings.min.json",
        "fribb_anime_list": "fribb-anime-list-full.json",
        "rensetsu_bangumi": "rensetsu-bangumi.min.json",
        "rensetsu_silveryasha": "rensetsu-silveryasha.min.json",
    }
    files: dict[str, Any] = {}
    for k, fname in names.items():
        if mdir and (mdir / fname).is_file():
            files[k] = {"exists": True, "path": str(mdir / fname), "bytes": (mdir / fname).stat().st_size}
        else:
            files[k] = {"exists": False, "path": str(mdir / fname) if mdir else "", "bytes": 0}
    return {
        "available": bool(mdir and any(v["exists"] for v in files.values())),
        "mappings_dir": str(mdir) if mdir else "",
        "rapidfuzz_installed": _rf_fuzz is not None,
        "datasets": files,
    }


def resolve_cross_ids(
    anilist_id: int | None = None,
    mal_id: int | None = None,
    imdb_id: str | None = None,
    bangumi_id: int | None = None,
    title: str | None = None,
    mappings_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Resolve cross-platform IDs, poster URL, and related anime URLs from SharedLibraries datasets."""
    mdir = resolve_shared_mappings_dir(mappings_dir)
    result: dict[str, Any] = {
        "found": False,
        "anilist_id": anilist_id,
        "mal_id": mal_id,
        "anidb_id": None,
        "kitsu_id": None,
        "tvdb_id": None,
        "tmdb_id": None,
        "imdb_id": imdb_id,
        "bangumi_id": bangumi_id,
        "poster_url": "",
        "related_anime": [],
        "sources": [],
    }
    if not mdir:
        return result

    fribb_idx = _build_fribb_index(mdir)
    aodb_idx = _build_aodb_index(mdir)

    f_hit = None
    if anilist_id and anilist_id in fribb_idx["anilist"]:
        f_hit = fribb_idx["anilist"][anilist_id]
    elif mal_id and mal_id in fribb_idx["mal"]:
        f_hit = fribb_idx["mal"][mal_id]
    elif imdb_id and imdb_id.lower() in fribb_idx["imdb"]:
        f_hit = fribb_idx["imdb"][imdb_id.lower()]

    if f_hit:
        result["found"] = True
        result["sources"].append("fribb")
        for src_k, dst_k in (("anilist_id", "anilist_id"), ("mal_id", "mal_id"), ("anidb_id", "anidb_id"), ("kitsu_id", "kitsu_id"), ("tvdb_id", "tvdb_id")):
            if f_hit.get(src_k) and not result.get(dst_k):
                result[dst_k] = int(f_hit[src_k])
        if f_hit.get("themoviedb_id") and not result["tmdb_id"]:
            result["tmdb_id"] = f_hit["themoviedb_id"]
        if f_hit.get("imdb_id") and not result["imdb_id"]:
            iv = f_hit["imdb_id"]
            result["imdb_id"] = iv[0] if isinstance(iv, list) and iv else str(iv)

    al_lookup = result["anilist_id"] or anilist_id
    mal_lookup = result["mal_id"] or mal_id
    a_hit = None
    if al_lookup and al_lookup in aodb_idx["by_anilist"]:
        a_hit = aodb_idx["by_anilist"][al_lookup]
    elif mal_lookup and mal_lookup in aodb_idx["by_mal"]:
        a_hit = aodb_idx["by_mal"][mal_lookup]
    elif title:
        best_score = 0.0
        for e in aodb_idx["entries"]:
            cands = [e.get("title") or ""] + list(e.get("synonyms") or [])[:5]
            sc = max((compute_title_similarity(title, c) for c in cands if c), default=0.0)
            if sc > best_score and sc >= 0.88:
                best_score = sc
                a_hit = e

    if a_hit:
        result["found"] = True
        result["sources"].append("anime_offline_db")
        ids = _parse_aodb_sources(a_hit.get("sources") or [])
        for k in ("anilist_id", "mal_id", "anidb_id", "kitsu_id"):
            if ids.get(k) and not result.get(k):
                result[k] = ids[k]
        if a_hit.get("picture") and not result["poster_url"]:
            result["poster_url"] = str(a_hit["picture"])
        if a_hit.get("relatedAnime"):
            result["related_anime"] = list(a_hit["relatedAnime"])

    # Enrich with Anibridge if AniList ID present
    ab_path = mdir / "anibridge-mappings.min.json"
    if result["anilist_id"] and ab_path.is_file():
        ab_raw = _load_json_cached(ab_path) or {}
        ab_entry = ab_raw.get(f"anilist:{result['anilist_id']}")
        if isinstance(ab_entry, dict):
            result["found"] = True
            result["sources"].append("anibridge")
            for k in ab_entry:
                if k.startswith("tmdb_") and not result["tmdb_id"]:
                    result["tmdb_id"] = k
                elif k.startswith("tvdb_") and not result["tvdb_id"]:
                    result["tvdb_id"] = k

    # Enrich with Rensetsu Bangumi when Bangumi ID or title is given
    ren_path = mdir / "rensetsu-bangumi.min.json"
    if (bangumi_id or title) and ren_path.is_file():
        ren_rows = _load_json_cached(ren_path) or []
        for r in ren_rows:
            if not isinstance(r, dict):
                continue
            r_bgm = (r.get("mappings") or {}).get("bangumi")
            if bangumi_id and r_bgm == bangumi_id:
                result["found"] = True
                result["sources"].append("rensetsu_bangumi")
                result["bangumi_id"] = bangumi_id
                break
            if title and not bangumi_id:
                cands = [r.get("title_display") or "", r.get("title_english") or ""] + list(r.get("synonyms") or [])[:4]
                if max((compute_title_similarity(title, c) for c in cands if c), default=0.0) >= 0.92:
                    result["found"] = True
                    result["sources"].append("rensetsu_bangumi")
                    if r_bgm:
                        result["bangumi_id"] = int(r_bgm)
                    break

    return result


def extract_entry_ids(entry: dict[str, Any]) -> dict[str, Any]:
    """Extract AniList, MAL, IMDb, and Bangumi IDs from a media catalog record."""
    urls: list[str] = []
    if entry.get("link"):
        urls.append(str(entry["link"]))
    for lk in entry.get("links") or []:
        if isinstance(lk, dict) and lk.get("url"):
            urls.append(str(lk["url"]))

    al_ids: list[int] = []
    mal_ids: list[int] = []
    imdb_ids: list[str] = []
    bgm_ids: list[int] = []
    for u in urls:
        for m in _ANILIST_ID_RE.findall(u):
            al_ids.append(int(m))
        for m in _MAL_ID_RE.findall(u):
            mal_ids.append(int(m))
        for m in _IMDB_ID_RE.findall(u):
            imdb_ids.append(m.lower())
        for m in _BGM_ID_RE.findall(u):
            bgm_ids.append(int(m))
    return {"anilist_ids": al_ids, "mal_ids": mal_ids, "imdb_ids": imdb_ids, "bangumi_ids": bgm_ids}


def query_anilist_relations(anilist_id: int, timeout: float = 8.0) -> list[dict[str, Any]]:
    """Query AniList GraphQL Media.relations edges for sequels, prequels, movies & adaptations."""
    gql = """query ($id: Int) {
  Media(id: $id) {
    id
    relations {
      edges {
        relationType
        node {
          id idMal type format status episodes siteUrl
          startDate { year }
          title { english romaji native }
          coverImage { large }
        }
      }
    }
  }
}"""
    body = json.dumps({"query": gql, "variables": {"id": int(anilist_id)}}).encode("utf-8")
    req = urllib.request.Request(
        "https://graphql.anilist.co",
        data=body,
        headers={"User-Agent": DEFAULT_UA, "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return []
    edges = ((((payload or {}).get("data") or {}).get("Media") or {}).get("relations") or {}).get("edges") or []
    out: list[dict[str, Any]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        node = edge.get("node") or {}
        if not node.get("id"):
            continue
        titles = node.get("title") or {}
        yr = (node.get("startDate") or {}).get("year")
        out.append(
            {
                "relation_type": str(edge.get("relationType") or ""),
                "anilist_id": int(node["id"]),
                "mal_id": int(node["idMal"]) if node.get("idMal") else None,
                "type": str(node.get("type") or ""),
                "format": str(node.get("format") or ""),
                "status": str(node.get("status") or ""),
                "episodes": node.get("episodes"),
                "year": int(yr) if isinstance(yr, int) else None,
                "title": str(titles.get("english") or titles.get("romaji") or titles.get("native") or ""),
                "title_romaji": str(titles.get("romaji") or ""),
                "title_native": str(titles.get("native") or ""),
                "poster_url": str((node.get("coverImage") or {}).get("large") or ""),
                "site_url": str(node.get("siteUrl") or f"https://anilist.co/anime/{node['id']}"),
            }
        )
    return out


def discover_new_adaptations(
    catalog: list[dict[str, Any]],
    franchise_filter: str | None = None,
    limit: int = 15,
    include_live_anilist: bool = True,
    mappings_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Scan tracked franchises for untracked sequels, movies, spin-offs, or adaptations."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in catalog:
        fid = str(item.get("franchise_id") or item.get("id") or "").strip()
        if not fid:
            continue
        if franchise_filter and fid.lower() != franchise_filter.strip().lower():
            continue
        groups.setdefault(fid, []).append(item)

    mdir = resolve_shared_mappings_dir(mappings_dir)
    aodb_idx = _build_aodb_index(mdir) if mdir else {"by_anilist": {}, "by_mal": {}, "entries": []}
    proposals: list[dict[str, Any]] = []
    scanned = 0

    for fid, grp in groups.items():
        if scanned >= max(1, limit):
            break
        known_al: set[int] = set()
        known_mal: set[int] = set()
        known_imdb: set[str] = set()
        known_titles: list[str] = []
        primary_al_ids: list[int] = []

        for entry in grp:
            known_titles.append(str(entry.get("name") or ""))
            if entry.get("franchise_title"):
                known_titles.append(str(entry["franchise_title"]))
            ids = extract_entry_ids(entry)
            known_al.update(ids["anilist_ids"])
            known_mal.update(ids["mal_ids"])
            known_imdb.update(ids["imdb_ids"])
            if entry.get("media_type") in ("donghua", "anime", "movie"):
                primary_al_ids.extend(ids["anilist_ids"])

        if not primary_al_ids:
            primary_al_ids = sorted(known_al)[:1]
        if not primary_al_ids:
            continue

        scanned += 1
        seen_candidate_al: set[int] = set()
        candidates: list[dict[str, Any]] = []

        if include_live_anilist:
            for al_id in primary_al_ids[:2]:
                for rel in query_anilist_relations(al_id):
                    cid = rel["anilist_id"]
                    if cid in known_al or cid in seen_candidate_al:
                        continue
                    seen_candidate_al.add(cid)
                    cross = resolve_cross_ids(anilist_id=cid, mal_id=rel.get("mal_id"), mappings_dir=mdir)
                    candidates.append(
                        {
                            "source": "anilist_relations",
                            "relation_type": rel["relation_type"],
                            "anilist_id": cid,
                            "mal_id": rel.get("mal_id") or cross.get("mal_id"),
                            "imdb_id": cross.get("imdb_id"),
                            "tmdb_id": cross.get("tmdb_id"),
                            "title": rel["title"],
                            "format": rel["format"],
                            "status": rel["status"],
                            "episodes": rel["episodes"],
                            "year": rel["year"],
                            "poster_url": rel["poster_url"] or cross.get("poster_url", ""),
                            "site_url": rel["site_url"],
                        }
                    )

        # Offline anime-offline-database relatedAnime check
        for al_id in primary_al_ids[:2]:
            a_hit = aodb_idx["by_anilist"].get(al_id)
            if not a_hit:
                continue
            for rel_url in a_hit.get("relatedAnime") or []:
                m = _ANILIST_ID_RE.search(str(rel_url))
                if not m:
                    continue
                cid = int(m.group(1))
                if cid in known_al or cid in seen_candidate_al:
                    continue
                seen_candidate_al.add(cid)
                rel_aodb = aodb_idx["by_anilist"].get(cid) or {}
                rel_title = str(rel_aodb.get("title") or f"AniList #{cid}")
                if any(compute_title_similarity(rel_title, kt) >= 0.94 for kt in known_titles if kt):
                    continue
                cross = resolve_cross_ids(anilist_id=cid, mappings_dir=mdir)
                candidates.append(
                    {
                        "source": "anime_offline_database",
                        "relation_type": "RELATED",
                        "anilist_id": cid,
                        "mal_id": cross.get("mal_id"),
                        "imdb_id": cross.get("imdb_id"),
                        "tmdb_id": cross.get("tmdb_id"),
                        "title": rel_title,
                        "format": str(rel_aodb.get("type") or ""),
                        "status": str(rel_aodb.get("status") or ""),
                        "episodes": rel_aodb.get("episodes"),
                        "year": (rel_aodb.get("animeSeason") or {}).get("year"),
                        "poster_url": str(rel_aodb.get("picture") or ""),
                        "site_url": f"https://anilist.co/anime/{cid}",
                    }
                )

        if candidates:
            franchise_name = str(grp[0].get("franchise_title") or grp[0].get("name") or fid)
            proposals.append(
                {
                    "franchise_id": fid,
                    "franchise_title": franchise_name,
                    "known_anilist_ids": sorted(known_al),
                    "new_candidates": candidates,
                }
            )

    return {
        "franchises_scanned": scanned,
        "franchises_with_new_candidates": len(proposals),
        "total_new_candidates": sum(len(p["new_candidates"]) for p in proposals),
        "inventory": get_dataset_inventory(mdir),
        "proposals": proposals,
    }
