"""Multi-source public metadata enrichment & local gitignored poster cache for Media domain."""

from __future__ import annotations

import html
import json
import mimetypes
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from media import MEDIA_DATA_DIR

POSTER_CACHE_DIR = MEDIA_DATA_DIR / "poster_cache"
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

_HOST_LOCKS: dict[str, threading.Lock] = {}
_HOST_LAST_CALL: dict[str, float] = {}
_GLOBAL_LOCK = threading.Lock()


def _throttle_host(host: str, min_interval: float = 0.25) -> None:
    """Rate-limit requests per upstream host cleanly without blocking other hosts."""
    with _GLOBAL_LOCK:
        lock = _HOST_LOCKS.setdefault(host, threading.Lock())
    with lock:
        now = time.monotonic()
        last = _HOST_LAST_CALL.get(host, 0.0)
        wait = min_interval - (now - last)
        if wait > 0:
            time.sleep(wait)
        _HOST_LAST_CALL[host] = time.monotonic()


def _clean_text(raw: str | None, max_len: int = 420) -> str:
    """Strip HTML tags/entities and collapse whitespace into a concise readable blurb."""
    if not raw:
        return ""
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(raw)))
    text = re.sub(r"\(Source:[^)]+\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        cut = text[: max_len - 1].rsplit(" ", 1)[0].rstrip(",;:")
        return f"{cut}…"
    return text


def _normalize_title_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _title_similarity(query: str, candidate: str) -> float:
    q_words = set(_normalize_title_key(query).split())
    c_words = set(_normalize_title_key(candidate).split())
    if not q_words or not c_words:
        return 0.0
    if _normalize_title_key(query) == _normalize_title_key(candidate):
        return 1.0
    inter = len(q_words & c_words)
    return inter / max(len(q_words), len(c_words))


def _http_json(
    url: str,
    post_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 8.0,
    min_interval: float = 0.25,
) -> Any:
    parsed = urllib.parse.urlparse(url)
    _throttle_host(parsed.netloc.lower(), min_interval=min_interval)
    req_headers = {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    data = None
    if post_body is not None:
        data = json.dumps(post_body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def query_anilist_franchise(title: str, alt: str = "") -> dict[str, dict[str, Any]]:
    """Query AniList GraphQL once for manga/novel/anime/donghua matches."""
    query_str = (
        "query ($s: String) { "
        "Page(perPage: 8) { "
        "media(search: $s) { "
        "id type format isAdult siteUrl "
        "title { english romaji native } "
        "coverImage { large medium } "
        "description(asHtml: false) "
        "} } }"
    )
    queries = [title.strip()]
    if alt:
        for part in re.split(r"[/·,;()]+", alt):
            clean = part.strip()
            if len(clean) >= 4 and clean.lower() not in {q.lower() for q in queries}:
                queries.append(clean)
                if len(queries) >= 2:
                    break

    by_bucket: dict[str, dict[str, Any]] = {}
    for q in queries:
        payload = _http_json(
            "https://graphql.anilist.co",
            post_body={"query": query_str, "variables": {"s": q}},
            min_interval=0.55,
        )
        items = (((payload or {}).get("data") or {}).get("Page") or {}).get("media") or []
        for m in items:
            titles = m.get("title") or {}
            cand_names = [titles.get("english") or "", titles.get("romaji") or ""]
            best_sim = max((_title_similarity(q, cn) for cn in cand_names if cn), default=0.0)
            if best_sim < 0.72:
                continue
            mtype = str(m.get("type") or "").upper()
            fmt = str(m.get("format") or "").upper()
            if fmt == "NOVEL":
                bucket = "light_novel"
            elif mtype == "MANGA":
                bucket = "comic"
            elif fmt == "MOVIE":
                bucket = "movie"
            elif mtype == "ANIME":
                bucket = "anime"
            else:
                continue
            cover = (m.get("coverImage") or {}).get("large") or (m.get("coverImage") or {}).get("medium") or ""
            desc = _clean_text(m.get("description"))
            prev = by_bucket.get(bucket)
            if not prev or best_sim > prev["score"]:
                by_bucket[bucket] = {
                    "score": best_sim,
                    "poster_url": cover,
                    "description": desc,
                    "is_adult": bool(m.get("isAdult")),
                    "url": m.get("siteUrl") or "",
                    "source": "anilist",
                }
        if "comic" in by_bucket and ("anime" in by_bucket or "light_novel" in by_bucket):
            break
    return by_bucket


def query_mangaupdates(title: str, alt: str = "") -> dict[str, Any] | None:
    """Query MangaUpdates REST API for comic/novel poster, synopsis, and adult tags."""
    candidates = [title.strip()]
    if alt:
        for part in re.split(r"[/·,;()]+", alt):
            clean = part.strip()
            if len(clean) >= 4 and clean.lower() not in {c.lower() for c in candidates}:
                candidates.append(clean)
                break

    best: dict[str, Any] | None = None
    for q in candidates:
        payload = _http_json(
            "https://api.mangaupdates.com/v1/series/search",
            post_body={"search": q, "perpage": 5},
            min_interval=0.35,
        )
        for row in (payload or {}).get("results") or []:
            rec = row.get("record") or {}
            rec_title = str(rec.get("title") or "")
            sim = _title_similarity(q, rec_title)
            if sim < 0.72:
                continue
            genres = {str(g.get("genre") or "").lower() for g in (rec.get("genres") or []) if isinstance(g, dict)}
            is_adult = bool(genres & {"hentai", "smut"}) or ("adult" in genres and sim >= 0.9)
            img = ((rec.get("image") or {}).get("url") or {}).get("original") or ""
            desc = _clean_text(rec.get("description"))
            rec_type = str(rec.get("type") or "").lower()
            if not best or sim > best["score"]:
                best = {
                    "score": sim,
                    "poster_url": img,
                    "description": desc,
                    "is_adult": is_adult,
                    "type": rec_type,
                    "url": rec.get("url") or "",
                    "source": "mangaupdates",
                }
        if best and best["score"] >= 0.85:
            break
    return best


def query_imdb_suggestion(title: str, alt: str = "") -> dict[str, dict[str, Any]]:
    """Query IMDb Suggestion JSON (no AWS WAF) for movie, tv_series, and animation posters."""
    queries = [title.strip()]
    if alt:
        for part in re.split(r"[/·,;()]+", alt):
            clean = re.sub(r"\bby\s+.*$", "", part, flags=re.IGNORECASE).strip()
            if len(clean) >= 4 and clean.lower() not in {q.lower() for q in queries}:
                queries.append(clean)
                if len(queries) >= 2:
                    break

    found: dict[str, dict[str, Any]] = {}
    for q in queries:
        first = re.sub(r"[^a-z0-9]", "", q.lower())[:1] or "a"
        encoded = urllib.parse.quote(q)
        payload = _http_json(
            f"https://v3.sg.media-imdb.com/suggestion/{first}/{encoded}.json",
            min_interval=0.25,
        )
        for item in (payload or {}).get("d") or []:
            if not isinstance(item, dict):
                continue
            iid = str(item.get("id") or "")
            if not iid.startswith("tt"):
                continue
            lbl = str(item.get("l") or "")
            sim = _title_similarity(q, lbl)
            if sim < 0.72:
                continue
            qtype = str(item.get("q") or "").lower()
            bucket = "movie" if "feature" in qtype or "movie" in qtype else "tv_series"
            img = str((item.get("i") or {}).get("imageUrl") or "")
            year = item.get("y")
            cast = str(item.get("s") or "").strip()
            blurb_parts = []
            if year:
                blurb_parts.append(str(year))
            if item.get("q"):
                blurb_parts.append(str(item["q"]))
            if cast:
                blurb_parts.append(f"Starring {cast}")
            prev = found.get(bucket)
            if not prev or sim > prev["score"]:
                found[bucket] = {
                    "score": sim,
                    "poster_url": img,
                    "imdb_id": iid,
                    "imdb_url": f"https://www.imdb.com/title/{iid}/",
                    "meta_summary": " · ".join(blurb_parts),
                    "source": "imdb",
                }
        if found:
            break
    return found


def query_tvmaze(title: str, alt: str = "") -> dict[str, Any] | None:
    """Query TVmaze public API for TV series / K-Drama / C-Drama synopsis & poster."""
    for q in [title.strip(), *(p.strip() for p in re.split(r"[/·,;()]+", alt or "") if len(p.strip()) >= 4)][:2]:
        rows = _http_json(f"https://api.tvmaze.com/search/shows?q={urllib.parse.quote(q)}", min_interval=0.25)
        if not isinstance(rows, list):
            continue
        for row in rows[:4]:
            show = row.get("show") or {}
            name = str(show.get("name") or "")
            sim = _title_similarity(q, name)
            if sim < 0.5:
                continue
            img = (show.get("image") or {}).get("medium") or (show.get("image") or {}).get("original") or ""
            summary = _clean_text(show.get("summary"))
            if img or summary:
                return {
                    "score": sim,
                    "poster_url": img,
                    "description": summary,
                    "official_site": show.get("officialSite") or "",
                    "url": show.get("url") or "",
                    "source": "tvmaze",
                }
    return None


def query_wikipedia_summary(title: str) -> dict[str, Any] | None:
    """Query Wikipedia REST summary API as clean fallback for novels, films, and series."""
    slug = urllib.parse.quote(title.strip().replace(" ", "_"))
    payload = _http_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}", min_interval=0.25)
    if not isinstance(payload, dict) or payload.get("type") == "disambiguation":
        return None
    extract = _clean_text(payload.get("extract"))
    thumb = ((payload.get("thumbnail") or {}).get("source")) or ((payload.get("originalimage") or {}).get("source")) or ""
    if not extract and not thumb:
        return None
    return {
        "poster_url": thumb,
        "description": extract,
        "source": "wikipedia",
    }


def _detect_image_ext(blob: bytes, content_type: str = "", url: str = "") -> str | None:
    if blob.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if blob.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if blob.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if len(blob) >= 12 and blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
        return ".webp"
    if content_type.startswith("image/"):
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            return ".jpg" if guessed == ".jpeg" else guessed
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        return ".jpg" if ext == ".jpeg" else ext
    return None


def download_poster_to_cache(
    entry_id: str,
    poster_url: str,
    cache_dir: Path = POSTER_CACHE_DIR,
    timeout: float = 10.0,
) -> str | None:
    """Download poster_url into gitignored `data/media/poster_cache/` and return cached filename."""
    if not entry_id or not poster_url or not poster_url.startswith(("http://", "https://")):
        return None
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^a-zA-Z0-9._-]+", "-", entry_id).strip("-")
    if not safe_id:
        return None

    for existing_ext in (".jpg", ".png", ".webp", ".gif"):
        candidate = cache_dir / f"{safe_id}{existing_ext}"
        if candidate.is_file() and candidate.stat().st_size > 256:
            return candidate.name

    parsed = urllib.parse.urlparse(poster_url)
    _throttle_host(parsed.netloc.lower(), min_interval=0.15)
    req = urllib.request.Request(
        poster_url,
        headers={
            "User-Agent": DEFAULT_UA,
            "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8",
            "Referer": f"{parsed.scheme}://{parsed.netloc}/",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = str(resp.headers.get("Content-Type") or "").lower()
            blob = resp.read(5 * 1024 * 1024 + 1)
        if len(blob) < 256 or len(blob) > 5 * 1024 * 1024:
            return None
        ext = _detect_image_ext(blob, content_type=ctype, url=poster_url)
        if not ext:
            return None
        dest = cache_dir / f"{safe_id}{ext}"
        dest.write_bytes(blob)
        return dest.name
    except Exception:
        return None


def get_cached_poster_bytes(
    entry_id: str,
    cache_dir: Path = POSTER_CACHE_DIR,
    cached_filename: str = "",
) -> tuple[bytes, str] | None:
    """Read locally cached poster bytes and MIME type safely from `data/media/poster_cache/`."""
    if not cache_dir.is_dir():
        return None
    candidates: list[Path] = []
    if cached_filename:
        safe_name = Path(cached_filename).name
        candidates.append(cache_dir / safe_name)
    safe_id = re.sub(r"[^a-zA-Z0-9._-]+", "-", entry_id).strip("-")
    if safe_id:
        for ext in (".jpg", ".png", ".webp", ".gif"):
            candidates.append(cache_dir / f"{safe_id}{ext}")

    cache_root = cache_dir.resolve()
    for cand in candidates:
        try:
            resolved = cand.resolve()
            if cache_root not in resolved.parents:
                continue
            if resolved.is_file():
                blob = resolved.read_bytes()
                ctype = mimetypes.guess_type(resolved.name)[0] or "image/jpeg"
                return blob, ctype
        except Exception:
            continue
    return None
