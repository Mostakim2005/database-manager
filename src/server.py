#!/usr/bin/env python3
"""Database Manager — Unified Local Server & Multi-Domain CLI Tool.

Serves interactive web dashboards for AI benchmarks, PC game compatibility, and
hardware planning on http://127.0.0.1:8770, with built-in REST API and CLI
search queries.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import argparse
import http.server
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# Directory anchors
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
DATA_DIR = ROOT_DIR / "data"
WEB_DIR = ROOT_DIR / "web"

PORT = 8770


def load_ai_data() -> dict[str, Any]:
    """Load AI models data from JSON."""
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
    """Load PC Games data from JSON."""
    games_json = DATA_DIR / "games" / "games.json"
    if games_json.exists():
        try:
            with open(games_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load games data from {games_json}: {e}\n")
    return []


def load_hardware_data() -> dict[str, Any]:
    """Load Hardware and PSU safety data from JSON."""
    hw_json = DATA_DIR / "hardware" / "hardware_specs.json"
    if hw_json.exists():
        try:
            with open(hw_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load hardware data from {hw_json}: {e}\n")
    return {"system_baseline": {}, "gpus": []}


def load_cpus_data() -> list[dict[str, Any]]:
    """Load Desktop CPUs data from JSON."""
    cpus_json = DATA_DIR / "cpus" / "cpus.json"
    if cpus_json.exists():
        try:
            with open(cpus_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("cpus", data.get("records", []))
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load CPUs data from {cpus_json}: {e}\n")
    return []


def load_components_data() -> dict[str, Any]:
    """Load PC & Peripherals components data from JSON."""
    comp_json = DATA_DIR / "pc_components" / "components.json"
    if comp_json.exists():
        try:
            with open(comp_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load components data from {comp_json}: {e}\n")
    return {}


def load_manga_data() -> list[dict[str, Any]]:
    """Load Manga, Manhwa & Adaptations catalog from JSON."""
    manga_json = DATA_DIR / "manga" / "manga_catalog.json"
    if manga_json.exists():
        try:
            with open(manga_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to load manga data from {manga_json}: {e}\n")
    return []


def load_github_data() -> list[dict[str, Any]]:
    """Load GitHub repository data (local live_cache.json if present else repos_public.json)."""
    try:
        from github.scanner import get_cached_repos
        return get_cached_repos()
    except Exception as e:
        sys.stderr.write(f"[ERROR] Failed to load GitHub data: {e}\n")
    return []


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

    def do_GET(self) -> None:
        """Handle GET requests with API routing."""
        url_path = self.path.split("?", 1)[0].rstrip("/")

        if url_path == "/api/status":
            ai_data = load_ai_data()
            ai_models = ai_data.get("models")
            if ai_models is None:
                ai_models = ai_data.get("records", [])
            comp_data = load_components_data()
            comp_count = sum(len(v) for v in comp_data.values() if isinstance(v, list))
            self._send_json(
                {
                    "status": "online",
                    "version": "1.0.0",
                    "repo": "Mostakim2005/database-manager",
                    "counts": {
                        "ai_models": len(ai_models),
                        "games": len(load_games_data()),
                        "gpus": len(load_hardware_data().get("gpus", [])),
                        "cpus": len(load_cpus_data()),
                        "pc_components": comp_count,
                        "manga": len(load_manga_data()),
                        "github": len(load_github_data()),
                    },
                }
            )
            return

        if url_path == "/api/ai":
            self._send_json(load_ai_data())
            return

        if url_path == "/api/games":
            self._send_json(load_games_data())
            return

        if url_path == "/api/hardware":
            self._send_json(load_hardware_data())
            return

        if url_path == "/api/cpus":
            self._send_json(load_cpus_data())
            return

        if url_path == "/api/components":
            self._send_json(load_components_data())
            return

        if url_path == "/api/domains":
            from db_hub import load_registry, query_domain_health
            self._send_json({"registry": load_registry(), "health": query_domain_health()})
            return

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

        if url_path == "/api/cross/ai-vram-fit":
            from db_hub import query_ai_vram_fit
            qs = parse_qs(urlparse(self.path).query)
            gpu_id = qs.get("gpu", ["rx-6600"])[0]
            self._send_json(query_ai_vram_fit(gpu_id=gpu_id))
            return

        if url_path == "/api/cross/cpu-gpu-combos":
            from db_hub import query_cpu_gpu_combos
            qs = parse_qs(urlparse(self.path).query)
            cpu_id = qs.get("cpu", ["ryzen-5-5600gt"])[0]
            self._send_json(query_cpu_gpu_combos(cpu_id=cpu_id))
            return

        if url_path == "/api/cross/check-build":
            from compatibility_engine import evaluate_default_build
            self._send_json(evaluate_default_build())
            return

        if url_path == "/api/ai/classified":
            from catalog_classifier import classify_ai_catalog
            qs = parse_qs(urlparse(self.path).query)
            only_chinese_oss = qs.get("chinese_oss", ["false"])[0].lower() in ("true", "1", "yes")
            self._send_json(classify_ai_catalog(only_chinese_oss=only_chinese_oss))
            return

        if url_path == "/api/games/classified":
            from catalog_classifier import classify_games_catalog
            self._send_json(classify_games_catalog())
            return

        if url_path == "/api/manga":
            qs = parse_qs(urlparse(self.path).query)
            q = qs.get("q", [""])[0].strip().lower()
            origin_f = qs.get("origin", [""])[0].strip().lower()
            items = load_manga_data()
            if q:
                items = [
                    it for it in items
                    if q in str(it.get("name", "")).lower()
                    or q in str(it.get("alt", "")).lower()
                    or q in str(it.get("anime", "")).lower()
                    or q in str(it.get("live_action", "")).lower()
                ]
            if origin_f:
                items = [it for it in items if origin_f in str(it.get("origin", "")).lower()]
            self._send_json(items)
            return

        if url_path == "/api/manga/classified":
            from catalog_classifier import classify_manga_catalog
            self._send_json(classify_manga_catalog())
            return

        if url_path == "/api/manga/doctor":
            from manga.adaptation_refresh import inspect_catalog_doctor, propose_link_upgrades
            catalog = load_manga_data()
            self._send_json(
                {
                    "doctor": inspect_catalog_doctor(catalog),
                    "link_proposals": propose_link_upgrades(catalog),
                }
            )
            return

        if url_path == "/api/manga/links":
            from manga.link_health import audit_catalog_links_offline, check_catalog_links_live
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

        # Drain small request body safely
        try:
            content_len = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            content_len = 0
        if content_len > 65536:
            self._send_json({"status": "error", "error": "Payload too large"}, status=413)
            return
        if content_len > 0:
            self.rfile.read(content_len)

        url_path = self.path.split("?", 1)[0].rstrip("/")
        if url_path == "/api/github/refresh":
            from github.scanner import scan_all_repositories, triage_repositories
            try:
                repos = scan_all_repositories(force_refresh=True, blocking=False)
            except RuntimeError as exc:
                self._send_json({"status": "busy", "error": str(exc)}, status=409)
                return
            self._send_json(triage_repositories(repos))
            return

        if url_path == "/api/github/export":
            from github.exporter import export_markdown_report
            dest = export_markdown_report(load_github_data())
            self._send_json({"status": "ok", "destination": dest})
            return

        self._send_json({"status": "error", "error": "Not Found"}, status=404)

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
    """Search AI models, PC games, and hardware GPUs for a case-insensitive query."""
    q = query.lower().strip()
    ai_data = load_ai_data()
    models = ai_data.get("models")
    if models is None:
        models = ai_data.get("records", [])
    games = load_games_data()
    gpus = load_hardware_data().get("gpus", [])
    manga_items = load_manga_data()

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
        if q in str(g.get("name", "")).lower() or q in str(g.get("genre", "")).lower()
    ]

    matched_gpus = [
        gpu for gpu in gpus
        if q in str(gpu.get("name", "")).lower() or q in str(gpu.get("vendor", "")).lower()
    ]

    matched_manga = [
        item for item in manga_items
        if q in str(item.get("name", "")).lower()
        or q in str(item.get("alt", "")).lower()
        or q in str(item.get("origin", "")).lower()
    ]

    github_items = load_github_data()
    matched_github = [
        repo for repo in github_items
        if q in str(repo.get("name", "")).lower()
        or q in str(repo.get("full_name", "")).lower()
        or q in str(repo.get("description", "")).lower()
        or q in str((repo.get("parent") or {}).get("full_name", "")).lower()
    ]

    return {
        "query": query,
        "ai_models": matched_models,
        "games": matched_games,
        "gpus": matched_gpus,
        "manga": matched_manga,
        "github": matched_github,
    }


def run_cli_summary(query: str | None = None, as_json: bool = False) -> None:
    """Print multi-domain database summary or search results."""
    ai_data = load_ai_data()
    models = ai_data.get("models")
    if models is None:
        models = ai_data.get("records", [])
    games = load_games_data()
    hw_data = load_hardware_data()
    gpus = hw_data.get("gpus", [])
    manga_items = load_manga_data()
    github_items = load_github_data()

    if as_json:
        if query:
            payload = search_databases(query)
        else:
            payload = {
                "counts": {
                    "ai_models": len(models),
                    "games": len(games),
                    "gpus": len(gpus),
                    "manga": len(manga_items),
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
                "hardware_gpus": [
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
    print(" 🚀 DATABASE MANAGER — MULTI-DOMAIN DATABASE SUMMARY")
    print("=" * 76)

    if not query:
        print("\n📊 TOTAL INVENTORY:")
        print(f"  • AI Models Catalog:       {len(models)} models benchmarked")
        print(f"  • PC Games Database:       {len(games)} strategy & RTS titles")
        print(f"  • Hardware GPU Tiers:      {len(gpus)} upgrade profiles")
        print(f"  • Manga & Adaptations:     {len(manga_items)} catalog titles")
        print(f"  • GitHub Repositories:     {len(github_items)} tracked repos")
        print("  • Baseline PC:             Ryzen 5 5600GT (Vega 7, 16MB L3, 550W PSU)")

        print("\n🤖 TOP AI MODELS (BY INTELLIGENCE INDEX):")
        print(f"  {'Model Name':<28} {'Vendor':<12} {'Index':<8} {'Pricing In/Out ($/M)'}")
        print("  " + "-" * 70)
        for m in models[:6]:
            f = _extract_ai_model_fields(m)
            intel_str = str(f["intelligence_index"]) if f["intelligence_index"] is not None else "N/A"
            print(f"  {str(f['name'])[:26]:<28} {str(f['provider'])[:10]:<12} {intel_str:<8} ${f['prompt_per_m']} / ${f['completion_per_m']}")

        print("\n🎮 SAMPLE RTS GAMES & VEGA 7 COMPATIBILITY:")
        print(f"  {'Game Title':<28} {'Genre':<14} {'Price':<10} {'Vega 7 Playable FPS'}")
        print("  " + "-" * 70)
        for g in games[:6]:
            title = g.get("name", "Unknown")[:26]
            genre = g.get("genre", "RTS")[:12]
            price = f"${g.get('priceUsd', 0)}" if g.get("priceModel") == "paid" else "Free"
            fps = g.get("bench", {}).get("playable", {}).get("fps", "~30-40")
            print(f"  {title:<28} {genre:<14} {price:<10} {fps}")

        print("\n⚡ HARDWARE UPGRADE CANDIDATES (550W PSU GUARD):")
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
        print(" 💡 Web Portal available at: http://127.0.0.1:8770")
        print("    Run 'python src/server.py' to launch server, or pass search keyword.")
        print("=" * 76 + "\n")
        return

    results = search_databases(query)
    print(f"\n🔍 SEARCH RESULTS FOR '{query}':")

    matched_models = results["ai_models"]
    if matched_models:
        print(f"\n[AI Models — {len(matched_models)} matches]")
        for f in matched_models:
            intel = f["intelligence_index"] if f["intelligence_index"] is not None else "N/A"
            print(f"  • {f['name']} ({f['provider']}) — Intelligence: {intel}")

    matched_games = results["games"]
    if matched_games:
        print(f"\n[PC Games — {len(matched_games)} matches]")
        for g in matched_games:
            title = g.get("name")
            verdict = g.get("compatNote", "Compatible")
            print(f"  • {title} — Note: {verdict}")

    matched_gpus = results["gpus"]
    if matched_gpus:
        print(f"\n[Hardware GPUs — {len(matched_gpus)} matches]")
        for gpu in matched_gpus:
            name = gpu.get("name")
            status = gpu.get("psu_badge") or gpu.get("psu_550w_verdict", "pass").upper()
            spike = gpu.get("system_peak_watts", 0)
            print(f"  • {name} — Peak Spike: ~{spike}W | PSU: {status}")

    matched_manga = results.get("manga", [])
    if matched_manga:
        print(f"\n[Manga & Adaptations — {len(matched_manga)} matches]")
        for m in matched_manga:
            print(f"  • {m.get('name')} ({m.get('origin')}) — {m.get('link')}")

    matched_github = results.get("github", [])
    if matched_github:
        print(f"\n[GitHub Repositories — {len(matched_github)} matches]")
        for r in matched_github:
            conc = (r.get("latest_run") or {}).get("conclusion") or "none"
            print(f"  • {r.get('full_name')} (CI: {conc}) — {r.get('description') or 'No description'}")

    if not (matched_models or matched_games or matched_gpus or matched_manga or matched_github):
        print("  (No matching records found across AI models, PC games, hardware GPUs, manga, or GitHub repos.)")

    print("\n" + "=" * 76 + "\n")


class ReusableThreadingHTTPServer(http.server.ThreadingHTTPServer):
    """Multi-threaded HTTP server with port reuse and daemon worker threads."""

    allow_reuse_address = True
    daemon_threads = True


def start_server(port: int = PORT) -> None:
    """Start the multi-threaded HTTP server on specified port."""
    with ReusableThreadingHTTPServer(("127.0.0.1", port), DatabaseHandler) as httpd:
        print("\n=======================================================")
        print(" 🚀 Database Manager Server running on:")
        print(f"    http://127.0.0.1:{port}")
        print(f"    Static root: {WEB_DIR}")
        print("    Endpoints:   /api/status, /api/ai, /api/games, /api/hardware")
        print("    Press Ctrl+C to stop.")
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
