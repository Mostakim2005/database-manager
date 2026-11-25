#!/usr/bin/env python3
"""Database Manager — Unified Local Server & Multi-Domain CLI Tool.

Serves interactive web dashboards for PC Hardware, PC Games, AI Models,
Media & Adaptations, Books, Phones, and GitHub Repositories on
http://127.0.0.1:8770 with REST API and CLI search queries.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import argparse
import csv
import http.server
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
DATA_DIR = ROOT_DIR / "data"
WEB_DIR = ROOT_DIR / "web"

PORT = 8770
SERVER_BUILD_ID = "2026.11.25-r4"

PC_CATEGORIES = (
    "cpus",
    "gpus",
    "motherboards",
    "ram",
    "ssds",
    "hdds",
    "psus",
    "monitors",
    "tvs",
    "keyboards",
    "mice",
    "graphics_tablets",
)


def load_pc_data() -> dict[str, Any]:
    """Load unified PC hardware, CPU, GPU, PSU, and peripheral catalog from JSON."""
    pc_json = DATA_DIR / "pc" / "pc.json"
    if pc_json.exists():
        try:
            with open(pc_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load PC data from {pc_json}: {e}\n")
    return {"system_baseline": {}, "transient_rules": {}, "cpus": [], "gpus": []}


def _count_pc_parts(pc_data: dict[str, Any]) -> int:
    """Count total PC parts across all registered categories in pc.json."""
    return sum(len(pc_data.get(cat, [])) for cat in PC_CATEGORIES if isinstance(pc_data.get(cat), list))


def load_ai_data() -> dict[str, Any]:
    """Load AI models pricing and benchmark catalog from JSON."""
    ai_json = DATA_DIR / "ai" / "models_master.json"
    if not ai_json.exists():
        ai_json = DATA_DIR / "ai" / "model-comparison.json"
    if ai_json.exists():
        try:
            with open(ai_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load AI data from {ai_json}: {e}\n")
            return {"error": str(e), "models": []}
    return {"models": []}


def load_games_data() -> list[dict[str, Any]]:
    """Load PC Games catalog from JSON."""
    games_json = DATA_DIR / "games" / "games.json"
    if games_json.exists():
        try:
            with open(games_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load games data from {games_json}: {e}\n")
    return []


def load_game_benchmarks_data() -> list[dict[str, Any]]:
    """Load measured FPS benchmarks from `data/games/benchmarks.csv`."""
    csv_path = DATA_DIR / "games" / "benchmarks.csv"
    if not csv_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(
                    {
                        "game_id": r["game_id"].strip(),
                        "cpu_name": r["cpu_name"].strip(),
                        "gpu_id": r["gpu_id"].strip(),
                        "resolution": r["resolution"].strip(),
                        "preset": r["preset"].strip(),
                        "avg_fps": float(r["avg_fps"]),
                        "low_1pct_fps": float(r["low_1pct_fps"]),
                        "low_01pct_fps": float(r["low_01pct_fps"]),
                        "source_url": (r.get("source_url") or "").strip(),
                        "recorded_at": (r.get("recorded_at") or "").strip(),
                    }
                )
    except Exception as e:
        sys.stderr.write(f"[ERROR] Failed to load game benchmarks from {csv_path}: {e}\n")
    return rows


def load_media_data() -> list[dict[str, Any]]:
    """Load Media, Comics, Novels, Anime, Movies & Series catalog from JSON."""
    media_json = DATA_DIR / "media" / "media_catalog.json"
    if media_json.exists():
        try:
            with open(media_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load media data from {media_json}: {e}\n")
    return []


def load_book_data() -> dict[str, Any]:
    """Load Book collection & reading tracker data merged with gitignored local library covers."""
    try:
        import book_sync
        return book_sync.load_merged_book_payload()
    except Exception as e:
        sys.stderr.write(f"[ERROR] Failed merged book load, using books.json fallback: {e}\n")
    book_json = DATA_DIR / "book" / "books.json"
    if book_json.exists():
        try:
            with open(book_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load book data from {book_json}: {e}\n")
    return {"books": []}


def load_phone_data() -> dict[str, Any]:
    """Load Phone specs & supported games/apps catalog from JSON."""
    phone_json = DATA_DIR / "phone" / "phones.json"
    if phone_json.exists():
        try:
            with open(phone_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load phone data from {phone_json}: {e}\n")
    return {"phones": []}


def load_github_data() -> list[dict[str, Any]]:
    """Load GitHub repository data (local live_cache.json if present else repos_public.json)."""
    try:
        from github.scanner import get_cached_repos
        return get_cached_repos()
    except Exception as e:
        sys.stderr.write(f"[ERROR] Failed to load GitHub data: {e}\n")
    return []


def load_domain_payload(domain_key: str) -> Any:
    """Dispatch payload loading by canonical domain key."""
    loaders: dict[str, Any] = {
        "pc": load_pc_data,
        "games": load_games_data,
        "ai": load_ai_data,
        "media": load_media_data,
        "book": load_book_data,
        "phone": load_phone_data,
        "github": load_github_data,
    }
    loader = loaders.get(domain_key)
    if loader:
        return loader()
    # Generic fallback for dynamically initialized domains via --init-domain
    from db_hub import load_registry
    cfg = load_registry().get("domains", {}).get(domain_key, {})
    src_rel = cfg.get("source_json", "")
    if src_rel:
        src_path = ROOT_DIR / src_rel
        if src_path.exists():
            return json.loads(src_path.read_text(encoding="utf-8"))
    return {}


def _extract_ai_model_fields(m: dict[str, Any]) -> dict[str, Any]:
    """Normalize AI model fields across v1 and v2 catalog schemas."""
    name = m.get("name") or m.get("model") or "Unknown"
    provider = m.get("provider") or m.get("provider_family") or m.get("vendor") or "N/A"
    scores = m.get("scores") if isinstance(m.get("scores"), dict) else {}
    intel = None
    for candidate in (
        scores.get("intelligence_index"),
        m.get("intelligence_index"),
        m.get("aa_intelligence_raw"),
        m.get("aa_index_v5"),
    ):
        if candidate is not None:
            intel = candidate
            break
    pricing = m.get("pricing") if isinstance(m.get("pricing"), dict) else {}
    pin = pricing.get("prompt_per_m")
    if pin is None:
        pin = m.get("price_in_1m", "-")
    pout = pricing.get("completion_per_m")
    if pout is None:
        pout = m.get("price_out_1m", "-")
    return {
        "id": m.get("id", ""),
        "name": name,
        "provider": provider,
        "provider_family": m.get("provider_family") or provider,
        "intelligence_index": intel,
        "prompt_per_m": pin,
        "completion_per_m": pout,
    }


def _is_allowed_loopback_origin(origin: str | None) -> bool:
    """Allow CORS only for local loopback origins."""
    if not origin or origin == "null":
        return False
    parsed = urlparse(origin)
    return parsed.scheme in ("http", "https") and parsed.hostname in ("127.0.0.1", "localhost")


def _is_allowed_loopback_host(host_header: str | None) -> bool:
    """Ensure Host header resolves strictly to loopback."""
    if not host_header:
        return False
    parsed = urlparse(f"http://{host_header}")
    return parsed.hostname in ("127.0.0.1", "localhost")


class DatabaseHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler serving web dashboard and REST API."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self) -> None:
        """Attach baseline local security headers to all responses."""
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        super().end_headers()

    def list_directory(self, path: str | os.PathLike[str]) -> None:  # type: ignore[override]
        """Disable directory listing to prevent unintended file enumeration."""
        self.send_error(403, "Directory listing is disabled")
        return None

    def guess_type(self, path: str | os.PathLike[str]) -> str:  # type: ignore[override]
        """Ensure UTF-8 charset header on text/HTML/JS/CSS assets across OSes."""
        ctype = super().guess_type(path)
        if ctype in ("text/html", "text/css", "text/javascript", "application/javascript"):
            return f"{ctype}; charset=utf-8"
        return ctype

    def do_GET(self) -> None:
        """Handle GET requests with strict v2.0.0 domain routing."""
        url_path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if url_path == "/api/status":
            from db_hub import load_registry, query_domain_health
            pc_data = load_pc_data()
            ai_data = load_ai_data()
            ai_models = ai_data.get("models")
            if ai_models is None:
                ai_models = ai_data.get("records", [])
            games_items = load_games_data()
            media_items = load_media_data()
            book_items = load_book_data().get("books", [])
            phone_items = load_phone_data().get("phones", [])
            github_items = load_github_data()
            pc_total = _count_pc_parts(pc_data)

            counts = {
                "pc": pc_total,
                "pc_gpus": len(pc_data.get("gpus", [])),
                "pc_cpus": len(pc_data.get("cpus", [])),
                "games": len(games_items),
                "ai": len(ai_models),
                "ai_models": len(ai_models),
                "media": len(media_items),
                "book": len(book_items),
                "phone": len(phone_items),
                "github": len(github_items),
            }
            reg = load_registry()
            health_rows = query_domain_health()
            for row in health_rows:
                dom = row["domain"]
                if row.get("record_count") is None:
                    row["record_count"] = counts.get(dom, 0)
                row["live_count"] = counts.get(dom, row.get("record_count") or 0)

            self._send_json(
                {
                    "status": "online",
                    "version": "2.0.0",
                    "server_build": SERVER_BUILD_ID,
                    "capabilities": {
                        "github_async_refresh": True,
                        "github_single_repo_refresh": True,
                        "ai_async_refresh": True,
                        "agent_proxy": True,
                        "book_local_sync": True,
                    },
                    "repo": "Mostakim2005/database-manager",
                    "counts": counts,
                    "registry": {
                        "version": reg.get("version", "2.0.0"),
                        "groups": reg.get("groups", {}),
                    },
                    "domains": health_rows,
                }
            )
            return

        if url_path == "/api/domains":
            from db_hub import load_registry, query_domain_health
            self._send_json({"registry": load_registry(), "health": query_domain_health()})
            return

        if url_path.startswith("/api/domain/"):
            from db_hub import load_registry, resolve_domain_key
            raw_key = url_path[len("/api/domain/"):].strip("/")
            reg = load_registry()
            canonical = resolve_domain_key(raw_key, reg)
            if not canonical:
                self._send_json({"status": "error", "error": f"Unknown domain or alias: {raw_key}"}, status=404)
                return
            self._send_json(
                {
                    "domain": canonical,
                    "requested": raw_key,
                    "meta": reg.get("domains", {}).get(canonical, {}),
                    "data": load_domain_payload(canonical),
                }
            )
            return

        # --- PC Hardware Domain ---
        if url_path == "/api/pc":
            qs = parse_qs(urlparse(self.path).query)
            cat_filter = qs.get("category", [""])[0].strip().lower()
            pc_data = load_pc_data()
            if cat_filter:
                if cat_filter not in PC_CATEGORIES:
                    self._send_json({"status": "error", "error": f"Unknown PC category: {cat_filter}"}, status=404)
                    return
                self._send_json({"category": cat_filter, "items": pc_data.get(cat_filter, [])})
                return
            self._send_json(pc_data)
            return

        if url_path == "/api/pc/gpus":
            self._send_json(load_pc_data().get("gpus", []))
            return

        if url_path == "/api/pc/cpus":
            self._send_json(load_pc_data().get("cpus", []))
            return

        if url_path == "/api/pc/check-build":
            from compatibility_engine import evaluate_default_build
            self._send_json(evaluate_default_build())
            return

        # --- Games Domain ---
        if url_path == "/api/games":
            self._send_json(load_games_data())
            return

        if url_path == "/api/games/classified":
            from catalog_classifier import classify_games_catalog
            self._send_json(classify_games_catalog())
            return

        if url_path == "/api/games/benchmarks":
            qs = parse_qs(urlparse(self.path).query)
            gpu_f = qs.get("gpu", [""])[0].strip().lower()
            game_f = qs.get("game", [""])[0].strip().lower()
            benches = load_game_benchmarks_data()
            if gpu_f:
                benches = [b for b in benches if b["gpu_id"].lower() == gpu_f]
            if game_f:
                benches = [b for b in benches if b["game_id"].lower() == game_f]
            self._send_json(benches)
            return

        # --- AI Models Domain (Pricing & Benchmarks only; decoupled from VRAM) ---
        if url_path == "/api/ai":
            self._send_json(load_ai_data())
            return

        if url_path == "/api/ai/classified":
            from catalog_classifier import classify_ai_catalog
            qs = parse_qs(urlparse(self.path).query)
            only_chinese_oss = qs.get("chinese_oss", ["false"])[0].lower() in ("true", "1", "yes")
            self._send_json(classify_ai_catalog(only_chinese_oss=only_chinese_oss))
            return

        if url_path == "/api/ai/refresh/status":
            from scrapers.multi_site_ai import get_ai_refresh_status
            self._send_json(get_ai_refresh_status())
            return

        # --- Media & Adaptations Domain ---
        if url_path == "/api/media":
            qs = parse_qs(urlparse(self.path).query)
            q = qs.get("q", [""])[0].strip().lower()
            origin_f = qs.get("origin", [""])[0].strip().lower()
            mtype_f = (qs.get("media_type") or qs.get("type") or [""])[0].strip().lower()
            franchise_f = qs.get("franchise", [""])[0].strip().lower()
            items = load_media_data()
            if q:
                items = [
                    it for it in items
                    if q in str(it.get("name", "")).lower()
                    or q in str(it.get("alt", "")).lower()
                    or q in str(it.get("anime", "")).lower()
                    or q in str(it.get("live_action", "")).lower()
                    or q in str(it.get("franchise_id", "")).lower()
                ]
            if origin_f:
                items = [it for it in items if origin_f in str(it.get("origin", "")).lower()]
            if mtype_f:
                items = [it for it in items if str(it.get("media_type", "comic")).lower() == mtype_f]
            if franchise_f:
                items = [it for it in items if str(it.get("franchise_id", "")).lower() == franchise_f]
            self._send_json(items)
            return

        if url_path == "/api/media/classified":
            from catalog_classifier import classify_media_catalog
            self._send_json(classify_media_catalog())
            return

        if url_path == "/api/media/doctor":
            from media.adaptation_refresh import inspect_catalog_doctor, propose_link_upgrades
            catalog = load_media_data()
            self._send_json(
                {
                    "doctor": inspect_catalog_doctor(catalog),
                    "link_proposals": propose_link_upgrades(catalog),
                }
            )
            return

        if url_path == "/api/media/links":
            from media.link_health import audit_catalog_links_offline, check_catalog_links_live
            qs = parse_qs(urlparse(self.path).query)
            is_live = qs.get("live", ["false"])[0].lower() in ("true", "1", "yes")
            if is_live:
                try:
                    limit = max(1, min(25, int(qs.get("limit", ["5"])[0])))
                except ValueError:
                    limit = 5
                host_f = qs.get("host", [None])[0]
                self._send_json(check_catalog_links_live(limit=limit, host_filter=host_f))
            else:
                self._send_json(audit_catalog_links_offline())
            return

        # --- Book Collection Domain ---
        if url_path == "/api/book/cover":
            import book_sync
            qs = parse_qs(urlparse(self.path).query)
            book_id = qs.get("id", [""])[0].strip()
            res = book_sync.get_book_cover_bytes(book_id) if book_id else None
            if not res:
                self._send_json({"status": "error", "error": "Book cover not found"}, status=404)
                return
            blob, ctype = res
            self._send_bytes(blob, ctype, max_age=86400)
            return

        if url_path == "/api/book":
            qs = parse_qs(urlparse(self.path).query)
            q = qs.get("q", [""])[0].strip().lower()
            own_f = qs.get("ownership", [""])[0].strip().lower()
            read_f = qs.get("reading", [""])[0].strip().lower()
            data = load_book_data()
            books = list(data.get("books", []))
            if q:
                books = [
                    b for b in books
                    if q in str(b.get("title", "")).lower()
                    or q in str(b.get("author", "")).lower()
                    or q in str(b.get("subject", "")).lower()
                ]
            if own_f:
                books = [b for b in books if str(b.get("ownership_status", "")).lower() == own_f]
            if read_f:
                books = [b for b in books if str(b.get("reading_status", "")).lower() == read_f]
            payload = dict(data)
            payload["books"] = books
            self._send_json(payload)
            return

        # --- Phone & Mobile Domain ---
        if url_path == "/api/phone":
            qs = parse_qs(urlparse(self.path).query)
            q = qs.get("q", [""])[0].strip().lower()
            brand_f = qs.get("brand", [""])[0].strip().lower()
            data = load_phone_data()
            phones = list(data.get("phones", []))
            if q:
                phones = [
                    p for p in phones
                    if q in str(p.get("name", "")).lower()
                    or q in str(p.get("brand", "")).lower()
                    or q in str(p.get("soc", "")).lower()
                    or any(q in str(g.get("name", "")).lower() for g in p.get("supported_games", []))
                    or any(q in str(a.get("name", "")).lower() for a in p.get("supported_apps", []))
                ]
            if brand_f:
                phones = [p for p in phones if brand_f in str(p.get("brand", "")).lower()]
            payload = dict(data)
            payload["phones"] = phones
            self._send_json(payload)
            return

        # --- GitHub Domain ---
        if url_path == "/api/github":
            qs = parse_qs(urlparse(self.path).query)
            q = qs.get("q", [""])[0].strip().lower()
            type_f = qs.get("type", [""])[0].strip().lower()
            ci_f = qs.get("ci", [""])[0].strip().lower()
            items = load_github_data()
            if q:
                items = [
                    r for r in items
                    if q in str(r.get("name", "")).lower()
                    or q in str(r.get("full_name", "")).lower()
                    or q in str(r.get("description", "")).lower()
                    or q in str((r.get("parent") or {}).get("full_name", "")).lower()
                ]
            if type_f == "fork":
                items = [r for r in items if r.get("is_fork")]
            elif type_f == "owned":
                items = [r for r in items if not r.get("is_fork") and not r.get("is_private")]
            elif type_f == "private":
                items = [r for r in items if r.get("is_private")]
            if ci_f == "success":
                items = [r for r in items if (r.get("latest_run") or {}).get("conclusion") == "success"]
            elif ci_f == "failure":
                items = [
                    r for r in items
                    if (r.get("latest_run") or {}).get("conclusion") in ("failure", "cancelled", "timed_out", "action_required")
                ]
            elif ci_f == "none":
                items = [r for r in items if not r.get("latest_run")]
            self._send_json(items)
            return

        if url_path == "/api/github/triage":
            from github.scanner import triage_repositories
            self._send_json(triage_repositories(load_github_data()))
            return

        if url_path == "/api/github/doctor":
            from github.cli import inspect_github_doctor
            self._send_json(inspect_github_doctor(load_github_data()))
            return

        if url_path == "/api/github/classified":
            from catalog_classifier import classify_github_catalog
            self._send_json(classify_github_catalog())
            return

        if url_path == "/api/github/refresh/status":
            from github.scanner import get_refresh_status
            self._send_json(get_refresh_status())
            return

        if url_path == "/api/github/local-sync":
            from github.scanner import load_sync_state, run_local_sync_check
            qs = parse_qs(urlparse(self.path).query)
            force_local = qs.get("refresh", ["false"])[0].lower() in ("true", "1", "yes")
            sync_state = load_sync_state()
            cached_local = sync_state.get("local_sync") if not force_local else None
            if isinstance(cached_local, dict):
                self._send_json(cached_local)
            else:
                self._send_json(run_local_sync_check(persist=True))
            return

        if url_path == "/api/github/local-roots":
            from github.local_sync import discover_default_roots
            self._send_json({"roots": [str(p) for p in discover_default_roots()]})
            return

        if url_path == "/api/agent/status":
            import agent_proxy
            self._send_json(agent_proxy.get_proxy_status())
            return

        # --- Cross-Domain PC <-> Games Queries ---
        if url_path == "/api/cross/games-by-gpu":
            from db_hub import query_games_by_gpu
            qs = parse_qs(urlparse(self.path).query)
            gpu_id = qs.get("gpu", ["rx-6600"])[0]
            try:
                psu = int(qs.get("psu", ["550"])[0])
            except ValueError:
                psu = 550
            self._send_json(query_games_by_gpu(gpu_id=gpu_id, max_psu_watts=psu))
            return

        if url_path == "/api/cross/cpu-gpu-combos":
            from db_hub import query_cpu_gpu_combos
            qs = parse_qs(urlparse(self.path).query)
            cpu_id = qs.get("cpu", ["ryzen-5-5600gt"])[0]
            self._send_json(query_cpu_gpu_combos(cpu_id=cpu_id))
            return

        if url_path == "/api/cross/game-benchmarks":
            from db_hub import query_game_benchmarks_with_pc
            qs = parse_qs(urlparse(self.path).query)
            gpu_id = qs.get("gpu", [None])[0]
            game_id = qs.get("game", [None])[0]
            self._send_json(query_game_benchmarks_with_pc(gpu_id=gpu_id, game_id=game_id))
            return

        if url_path == "/api/cross/check-build":
            from compatibility_engine import evaluate_default_build
            self._send_json(evaluate_default_build())
            return

        if url_path == "/api/cross/games-storage":
            from db_hub import query_games_storage_summary
            self._send_json(query_games_storage_summary())
            return

        # Explicit 404 for unknown / retired /api/* routes (Alpha 2 clean cutover)
        if url_path.startswith("/api/"):
            self._send_json({"status": "error", "error": f"Endpoint not found: {url_path}"}, status=404)
            return

        # Serve static web content from WEB_DIR
        super().do_GET()

    def _is_authorized_local_post(self) -> tuple[bool, str]:
        """Validate Host and Origin/Referer headers to prevent cross-site POST CSRF."""
        host_hdr = self.headers.get("Host")
        if not _is_allowed_loopback_host(host_hdr):
            return False, "Forbidden: non-loopback Host header"
        origin = self.headers.get("Origin")
        if origin is not None:
            if not _is_allowed_loopback_origin(origin):
                return False, "Forbidden: non-loopback Origin header"
            parsed_orig = urlparse(origin)
            srv_port = getattr(self.server, "server_port", None)
            if parsed_orig.port is not None and srv_port and parsed_orig.port != srv_port:
                return False, "Forbidden: Origin port mismatch"
        referer = self.headers.get("Referer")
        if origin is None and referer is not None and not _is_allowed_loopback_origin(referer):
            return False, "Forbidden: non-loopback Referer header"
        return True, ""

    def do_POST(self) -> None:
        """Handle CSRF-guarded local POST actions for GitHub refresh and report export."""
        ok, reason = self._is_authorized_local_post()
        if not ok:
            self._send_json({"status": "error", "error": reason}, status=403)
            return

        try:
            content_len = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            content_len = 0
        if content_len > 65536:
            self._send_json({"status": "error", "error": "Payload too large"}, status=413)
            return
        payload: dict[str, Any] = {}
        if content_len > 0:
            raw_body = self.rfile.read(content_len)
            try:
                parsed_body = json.loads(raw_body.decode("utf-8"))
                if isinstance(parsed_body, dict):
                    payload = parsed_body
            except (UnicodeDecodeError, json.JSONDecodeError):
                payload = {}

        parsed_url = urlparse(self.path)
        url_path = parsed_url.path.rstrip("/")
        qs = parse_qs(parsed_url.query)

        if url_path == "/api/github/refresh":
            from github.scanner import scan_all_repositories, start_background_refresh, triage_repositories
            is_async = qs.get("async", ["false"])[0].lower() in ("true", "1", "yes") or bool(payload.get("async"))
            include_local = qs.get("include_local", [str(payload.get("include_local", "true"))])[0].lower() not in ("false", "0", "no")
            try:
                if is_async:
                    job = start_background_refresh(include_local=include_local)
                    self._send_json(job, status=202)
                    return
                repos = scan_all_repositories(force_refresh=True, blocking=False, include_local=include_local)
            except RuntimeError as exc:
                self._send_json({"status": "busy", "error": str(exc)}, status=409)
                return
            self._send_json(triage_repositories(repos))
            return

        if url_path == "/api/github/refresh/cancel":
            from github.scanner import cancel_background_refresh
            self._send_json(cancel_background_refresh())
            return

        if url_path == "/api/ai/refresh":
            from scrapers.multi_site_ai import apply_ai_update, start_background_ai_refresh, sync_multi_site_ai
            is_async = qs.get("async", ["false"])[0].lower() in ("true", "1", "yes") or bool(payload.get("async"))
            try:
                if is_async:
                    job = start_background_ai_refresh()
                    self._send_json(job, status=202)
                    return
                ai_data, stats = sync_multi_site_ai(offline=False)
                apply_ai_update(ai_data)
            except RuntimeError as exc:
                self._send_json({"status": "busy", "error": str(exc)}, status=409)
                return
            self._send_json({"status": "ok", "stats": stats, "metadata": ai_data.get("metadata", {})})
            return

        if url_path == "/api/ai/refresh/cancel":
            from scrapers.multi_site_ai import cancel_background_ai_refresh
            self._send_json(cancel_background_ai_refresh())
            return

        if url_path == "/api/github/refresh/repo":
            from github.scanner import refresh_single_repository
            full_name = str(payload.get("full_name") or qs.get("full_name", [""])[0]).strip()
            try:
                res = refresh_single_repository(full_name)
                self._send_json(res)
            except ValueError as exc:
                self._send_json({"status": "error", "error": str(exc)}, status=400)
            except LookupError as exc:
                self._send_json({"status": "error", "error": str(exc)}, status=404)
            except RuntimeError as exc:
                self._send_json({"status": "busy", "error": str(exc)}, status=409)
            return

        if url_path == "/api/github/local-sync":
            from github.scanner import run_local_sync_check
            self._send_json(run_local_sync_check(persist=True))
            return

        if url_path == "/api/github/local-roots":
            from github.local_sync import save_local_roots
            from github.scanner import run_local_sync_check
            roots_in = payload.get("roots")
            if not isinstance(roots_in, list):
                self._send_json({"status": "error", "error": "Expected JSON array 'roots'"}, status=400)
                return
            saved = save_local_roots([str(r) for r in roots_in])
            report = run_local_sync_check(persist=True)
            self._send_json({"status": "ok", "roots": saved, "local_sync": report})
            return

        if url_path == "/api/book/sync":
            import book_sync
            self._send_json(book_sync.sync_alexandria_library())
            return

        if url_path == "/api/book/open":
            import book_sync
            book_id = str(payload.get("id") or qs.get("id", [""])[0]).strip()
            if not book_id:
                self._send_json({"status": "error", "error": "Book id is required"}, status=400)
                return
            try:
                self._send_json(book_sync.open_local_book_file(book_id))
            except LookupError as exc:
                self._send_json({"status": "error", "error": str(exc)}, status=404)
            except (FileNotFoundError, ValueError, OSError) as exc:
                self._send_json({"status": "error", "error": str(exc)}, status=400)
            return

        if url_path == "/api/github/export":
            from github.exporter import export_markdown_report
            dest = export_markdown_report(load_github_data())
            self._send_json({"status": "ok", "destination": dest})
            return

        if url_path == "/api/agent/start":
            import agent_proxy
            res = agent_proxy.start_cliproxy_service()
            self._send_json(res, status=200 if res.get("online") else 503)
            return

        if url_path in ("/api/agent/github-report", "/api/agent/github-summary"):
            import agent_proxy
            from github.cli import inspect_github_doctor
            from github.scanner import load_sync_state, run_local_sync_check
            repos = load_github_data()
            doctor = inspect_github_doctor(repos, include_local=False)
            sync_state = load_sync_state()
            local_sync = sync_state.get("local_sync")
            if not isinstance(local_sync, dict):
                local_sync = run_local_sync_check(repos=repos, persist=True)
            model = payload.get("model")
            if url_path == "/api/agent/github-report":
                res = agent_proxy.generate_github_ai_report(repos, doctor, local_sync=local_sync, model=model)
            else:
                res = agent_proxy.summarize_github_refresh(repos, doctor, local_sync=local_sync, model=model)
            self._send_json(res, status=200 if res.get("ok") else 503)
            return

        if url_path == "/api/agent/ask":
            import agent_proxy
            question = str(payload.get("question") or "").strip()
            model = payload.get("model")
            pc_data = load_pc_data()
            games = load_games_data()
            ai_models = load_ai_data().get("models", [])
            media_items = load_media_data()
            books = load_book_data().get("books", [])
            phones = load_phone_data().get("phones", [])
            gh_items = load_github_data()
            keywords = [w for w in question.replace("?", " ").split() if len(w) >= 3][:4]
            matched: dict[str, Any] = {}
            for kw in keywords:
                hits = search_databases(kw)
                for dom_k in ("pc", "gpus", "ai_models", "games", "media", "book", "phone", "github"):
                    if hits.get(dom_k):
                        matched.setdefault(dom_k, [])
                        for item in hits[dom_k][:5]:
                            if item not in matched[dom_k]:
                                matched[dom_k].append(item)
            ctx = {
                "baseline_pc": pc_data.get("system_baseline", {}),
                "domain_counts": {
                    "pc": _count_pc_parts(pc_data),
                    "games": len(games),
                    "ai_models": len(ai_models),
                    "media": len(media_items),
                    "book": len(books),
                    "phone": len(phones),
                    "github": len(gh_items),
                },
                "matched_records": matched,
            }
            res = agent_proxy.ask_cross_domain_agent(question, ctx, model=model)
            self._send_json(res, status=200 if res.get("ok") else 503)
            return

        self._send_json({"status": "error", "error": "Not Found"}, status=404)

    def _send_bytes(self, body: bytes, content_type: str, status: int = 200, max_age: int = 0) -> None:
        """Helper to send raw image or binary asset bytes safely."""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if max_age > 0:
            self.send_header("Cache-Control", f"public, max-age={max_age}")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: Any, status: int = 200) -> None:
        """Helper to send JSON response with loopback-only CORS."""
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        origin = self.headers.get("Origin")
        if _is_allowed_loopback_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)  # type: ignore[arg-type]
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet log for cleaner terminal output."""
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def search_databases(query: str) -> dict[str, Any]:
    """Search across all 7 domains for a case-insensitive keyword."""
    q = query.lower().strip()
    pc_data = load_pc_data()
    ai_data = load_ai_data()
    models = ai_data.get("models")
    if models is None:
        models = ai_data.get("records", [])
    games = load_games_data()
    media_items = load_media_data()
    books = load_book_data().get("books", [])
    phones = load_phone_data().get("phones", [])
    github_items = load_github_data()

    matched_pc: list[dict[str, Any]] = []
    for cat in PC_CATEGORIES:
        for item in pc_data.get(cat, []):
            hay = " ".join(str(v) for v in (item.get("name", ""), item.get("brand", ""), item.get("notes", ""), cat)).lower()
            if q in hay:
                matched_pc.append({"category": cat, **item})

    matched_gpus = [
        gpu for gpu in pc_data.get("gpus", [])
        if q in str(gpu.get("name", "")).lower() or q in str(gpu.get("brand", "")).lower()
    ]

    matched_models: list[dict[str, Any]] = []
    for m in models:
        fields = _extract_ai_model_fields(m)
        haystack = " ".join(
            str(v) for v in (
                fields["name"],
                fields["id"],
                fields["provider"],
                fields["provider_family"],
                m.get("vendor", ""),
            )
        ).lower()
        if q in haystack:
            matched_models.append(fields)

    matched_games = [
        g for g in games
        if q in str(g.get("name", "")).lower()
        or q in str(g.get("id", "")).lower()
        or q in str(g.get("genre", "")).lower()
        or q in str(g.get("setting", "")).lower()
        or q in str(g.get("ownership", "")).lower()
        or q in str(g.get("compatNote", "")).lower()
    ]

    matched_media = [
        item for item in media_items
        if q in str(item.get("name", "")).lower()
        or q in str(item.get("alt", "")).lower()
        or q in str(item.get("origin", "")).lower()
        or q in str(item.get("media_type", "")).lower()
        or q in str(item.get("franchise_id", "")).lower()
        or q in str(item.get("watchlist_status", "")).lower()
    ]

    matched_books = [
        b for b in books
        if q in str(b.get("title", "")).lower()
        or q in str(b.get("author", "")).lower()
        or q in str(b.get("subject", "")).lower()
    ]

    matched_phones = [
        p for p in phones
        if q in str(p.get("name", "")).lower()
        or q in str(p.get("brand", "")).lower()
        or q in str(p.get("soc", "")).lower()
        or any(q in str(g.get("name", "")).lower() for g in p.get("supported_games", []))
        or any(q in str(a.get("name", "")).lower() for a in p.get("supported_apps", []))
    ]

    matched_github = [
        repo for repo in github_items
        if q in str(repo.get("name", "")).lower()
        or q in str(repo.get("full_name", "")).lower()
        or q in str(repo.get("description", "")).lower()
        or q in str((repo.get("parent") or {}).get("full_name", "")).lower()
    ]

    return {
        "query": query,
        "pc": matched_pc,
        "gpus": matched_gpus,
        "ai_models": matched_models,
        "games": matched_games,
        "media": matched_media,
        "book": matched_books,
        "phone": matched_phones,
        "github": matched_github,
    }


def run_cli_summary(query: str | None = None, as_json: bool = False) -> None:
    """Print multi-domain database summary or search results."""
    pc_data = load_pc_data()
    ai_data = load_ai_data()
    models = ai_data.get("models")
    if models is None:
        models = ai_data.get("records", [])
    games = load_games_data()
    gpus = pc_data.get("gpus", [])
    media_items = load_media_data()
    books = load_book_data().get("books", [])
    phones = load_phone_data().get("phones", [])
    github_items = load_github_data()

    if as_json:
        if query:
            payload = search_databases(query)
        else:
            payload = {
                "counts": {
                    "pc": _count_pc_parts(pc_data),
                    "pc_gpus": len(gpus),
                    "pc_cpus": len(pc_data.get("cpus", [])),
                    "games": len(games),
                    "ai_models": len(models),
                    "media": len(media_items),
                    "book": len(books),
                    "phone": len(phones),
                    "github": len(github_items),
                },
                "top_ai_models": [_extract_ai_model_fields(m) for m in models[:6]],
                "sample_games": [
                    {
                        "name": g.get("name", "Unknown"),
                        "genre": g.get("genre", "RTS"),
                        "price_model": g.get("priceModel", "paid"),
                        "price_usd": g.get("priceUsd", 0),
                        "playable_fps": g.get("bench", {}).get("playable", {}).get("fps", "~30-40"),
                    }
                    for g in games[:6]
                ],
                "pc_gpus": [
                    {
                        "id": gpu.get("id"),
                        "name": gpu.get("name", "Unknown"),
                        "tdp_watts": gpu.get("tdp_watts", 0),
                        "system_peak_watts": gpu.get("system_peak_watts", 0),
                        "psu_550w_verdict": gpu.get("psu_550w_verdict", "pass"),
                        "price_bdt_used": gpu.get("price_bdt_used", 0),
                    }
                    for gpu in gpus[:6]
                ],
            }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    print("\n" + "=" * 76)
    print(" DATABASE MANAGER — MULTI-DOMAIN DATABASE SUMMARY")
    print("=" * 76)

    if not query:
        print("\nTOTAL INVENTORY (7 REGISTERED DOMAINS):")
        print(f"  • PC & Hardware Catalog:   {_count_pc_parts(pc_data)} parts ({len(gpus)} GPUs, {len(pc_data.get('cpus', []))} CPUs)")
        print(f"  • PC Games Database:       {len(games)} PC & strategy titles ({sum(1 for g in games if g.get('ownership') == 'owned')} owned, {sum(1 for g in games if g.get('ownership') != 'owned')} wishlist)")
        print(f"  • AI Models & Pricing:     {len(models)} models benchmarked")
        print(f"  • Media & Adaptations:     {len(media_items)} entries (comics, novels, anime, series)")
        print(f"  • Book Collection:         {len(books)} tracked books")
        print(f"  • Phone & Mobile:          {len(phones)} devices")
        print(f"  • GitHub Repositories:     {len(github_items)} tracked repos")

        print("\nTOP AI MODELS (BY INTELLIGENCE INDEX):")
        print(f"  {'Model Name':<28} {'Vendor':<12} {'Index':<8} {'Pricing In/Out ($/M)'}")
        print("  " + "-" * 70)
        for m in models[:6]:
            f = _extract_ai_model_fields(m)
            intel_str = str(f["intelligence_index"]) if f["intelligence_index"] is not None else "N/A"
            print(f"  {str(f['name'])[:26]:<28} {str(f['provider'])[:10]:<12} {intel_str:<8} ${f['prompt_per_m']} / ${f['completion_per_m']}")

        print("\nPC UPGRADE GPU CANDIDATES (550W PSU TRANSIENT GUARD):")
        print(f"  {'GPU Model':<28} {'TDP':<8} {'Peak Spike':<14} {'550W Status':<12} {'Used BDT'}")
        print("  " + "-" * 70)
        for gpu in gpus[:6]:
            name = gpu.get("name", "Unknown")[:26]
            tdp = f"{gpu.get('tdp_watts', 0)}W"
            spike = f"~{gpu.get('system_peak_watts', 0)}W"
            status = gpu.get("psu_550w_verdict", "pass").upper()
            bdt = f"৳{gpu.get('price_bdt_used', 0):,}" if gpu.get("price_bdt_used") else "Base"
            print(f"  {name:<28} {tdp:<8} {spike:<14} {status:<12} {bdt}")

        print("\n" + "=" * 76)
        print(" Web Portal available at: http://127.0.0.1:8770")
        print(" Run 'python src/server.py' to launch server, or pass search keyword.")
        print("=" * 76 + "\n")
        return

    results = search_databases(query)
    print(f"\nSEARCH RESULTS FOR '{query}':")

    if results["pc"]:
        print(f"\n[PC Parts — {len(results['pc'])} matches]")
        for item in results["pc"]:
            print(f"  • [{item.get('category')}] {item.get('name')} — {item.get('brand', 'N/A')}")

    if results["ai_models"]:
        print(f"\n[AI Models — {len(results['ai_models'])} matches]")
        for f in results["ai_models"]:
            intel = f["intelligence_index"] if f["intelligence_index"] is not None else "N/A"
            print(f"  • {f['name']} ({f['provider']}) — Intelligence: {intel}")

    if results["games"]:
        print(f"\n[PC Games — {len(results['games'])} matches]")
        for g in results["games"]:
            print(f"  • {g.get('name')} — Note: {g.get('compatNote', 'Compatible')}")

    if results["media"]:
        print(f"\n[Media & Adaptations — {len(results['media'])} matches]")
        for m in results["media"]:
            print(f"  • [{m.get('media_type', 'comic')}] {m.get('name')} ({m.get('origin')}) — {m.get('link')}")

    if results["book"]:
        print(f"\n[Book Collection — {len(results['book'])} matches]")
        for b in results["book"]:
            print(f"  • {b.get('title')} by {b.get('author')} [{b.get('ownership_status')}/{b.get('reading_status')}]")

    if results["phone"]:
        print(f"\n[Phone & Mobile — {len(results['phone'])} matches]")
        for p in results["phone"]:
            print(f"  • {p.get('name')} ({p.get('soc')}, {p.get('ram_gb')}GB RAM)")

    if results["github"]:
        print(f"\n[GitHub Repositories — {len(results['github'])} matches]")
        for r in results["github"]:
            conc = (r.get("latest_run") or {}).get("conclusion") or "none"
            print(f"  • {r.get('full_name')} (CI: {conc}) — {r.get('description') or 'No description'}")

    if not any(results[k] for k in ("pc", "ai_models", "games", "media", "book", "phone", "github")):
        print("  (No matching records found across any domain.)")

    print("\n" + "=" * 76 + "\n")


class ReusableThreadingHTTPServer(http.server.ThreadingHTTPServer):
    """Multi-threaded HTTP server with port reuse and daemon worker threads."""

    allow_reuse_address = True
    daemon_threads = True


def start_server(port: int = PORT) -> None:
    """Start the multi-threaded HTTP server on specified port."""
    with ReusableThreadingHTTPServer(("127.0.0.1", port), DatabaseHandler) as httpd:
        print("\n=======================================================")
        print(" Database Manager Server running on:")
        print(f"   http://127.0.0.1:{port}")
        print(f"   Static root: {WEB_DIR}")
        print("   Endpoints:   /api/status, /api/domains, /api/pc, /api/games,")
        print("                /api/ai, /api/media, /api/book, /api/phone, /api/github")
        print("   Press Ctrl+C to stop.")
        print("=======================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")


def main() -> None:
    """Parse CLI arguments and dispatch execution."""
    parser = argparse.ArgumentParser(
        description="Database Manager — Multi-Domain Benchmark & Compatibility Manager"
    )
    parser.add_argument(
        "--cli",
        nargs="?",
        const="",
        help="Run in terminal CLI mode. Pass an optional search keyword.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output when running with --cli.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=PORT,
        help=f"Port to bind web server (default: {PORT})",
    )
    args = parser.parse_args()

    if args.cli is not None or args.json:
        query = args.cli if args.cli not in (None, "") else None
        run_cli_summary(query, as_json=args.json)
    else:
        start_server(args.port)


if __name__ == "__main__":
    main()
