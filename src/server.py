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
import os
import socketserver
import sys
from pathlib import Path
from typing import Any

# Directory anchors
ROOT_DIR = Path(__file__).resolve().parent.parent
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
            return {"error": str(e), "models": []}
    return {"models": []}


def load_games_data() -> list[dict[str, Any]]:
    """Load PC Games data from JSON."""
    games_json = DATA_DIR / "games" / "games.json"
    if games_json.exists():
        try:
            with open(games_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def load_hardware_data() -> dict[str, Any]:
    """Load Hardware and PSU safety data from JSON."""
    hw_json = DATA_DIR / "hardware" / "hardware_specs.json"
    if hw_json.exists():
        try:
            with open(hw_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"system_baseline": {}, "gpus": []}


class DatabaseHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler serving web dashboard and REST API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests with API routing."""
        url_path = self.path.split("?")[0].rstrip("/")

        if url_path == "/api/status":
            self._send_json(
                {
                    "status": "online",
                    "version": "1.0.0",
                    "repo": "Mostakim2005/database-manager",
                    "counts": {
                        "ai_models": len(
                            load_ai_data().get(
                                "models", load_ai_data().get("records", [])
                            )
                        ),
                        "games": len(load_games_data()),
                        "gpus": len(load_hardware_data().get("gpus", [])),
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

        # Serve static web content from WEB_DIR
        super().do_GET()

    def _send_json(self, data: Any, status: int = 200) -> None:
        """Helper to send JSON response."""
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet log for cleaner terminal output."""
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def run_cli_summary(query: str | None = None) -> None:
    """Print multi-domain database summary or search results."""
    ai_data = load_ai_data()
    models = ai_data.get("models", ai_data.get("records", []))
    games = load_games_data()
    hw_data = load_hardware_data()
    gpus = hw_data.get("gpus", [])

    print("\n" + "=" * 76)
    print(" 🚀 DATABASE MANAGER — MULTI-DOMAIN DATABASE SUMMARY")
    print("=" * 76)

    if not query:
        print(f"\n📊 TOTAL INVENTORY:")
        print(f"  • AI Models Catalog:       {len(models)} models benchmarked")
        print(f"  • PC Games Database:       {len(games)} strategy & RTS titles")
        print(f"  • Hardware GPU Tiers:      {len(gpus)} upgrade profiles")
        print(f"  • Baseline PC:             Ryzen 5 5600GT (Vega 7, 16MB L3, 550W PSU)")

        print("\n🤖 TOP AI MODELS (BY INTELLIGENCE INDEX):")
        print(f"  {'Model Name':<28} {'Vendor':<12} {'Index':<8} {'Pricing In/Out ($/M)'}")
        print("  " + "-" * 70)
        for m in models[:6]:
            name = m.get("name", m.get("model", "Unknown"))[:26]
            vendor = (m.get("provider") or m.get("vendor") or "N/A")[:10]
            scores = m.get("scores", {}) if isinstance(m.get("scores"), dict) else {}
            intel = scores.get("intelligence_index") or m.get("intelligence_index") or m.get("aa_intelligence_raw") or m.get("aa_index_v5") or 0.0
            pricing = m.get("pricing", {}) if isinstance(m.get("pricing"), dict) else {}
            pin = pricing.get("prompt_per_m", m.get("price_in_1m", "-"))
            pout = pricing.get("completion_per_m", m.get("price_out_1m", "-"))
            print(f"  {name:<28} {vendor:<12} {intel:<8} ${pin} / ${pout}")

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

    q = query.lower()
    print(f"\n🔍 SEARCH RESULTS FOR '{query}':")

    # Search AI
    matched_models = [
        m for m in models
        if q in str(m.get("name", m.get("model", ""))).lower() or q in str(m.get("vendor", "")).lower()
    ]
    if matched_models:
        print(f"\n[AI Models — {len(matched_models)} matches]")
        for m in matched_models:
            name = m.get("name", m.get("model", "Unknown"))
            vendor = m.get("vendor", "N/A")
            intel = m.get("intelligence_index", m.get("aa_intelligence_raw", "N/A"))
            print(f"  • {name} ({vendor}) — Intelligence: {intel}")

    # Search Games
    matched_games = [
        g for g in games
        if q in str(g.get("name", "")).lower() or q in str(g.get("genre", "")).lower()
    ]
    if matched_games:
        print(f"\n[PC Games — {len(matched_games)} matches]")
        for g in matched_games:
            title = g.get("name")
            verdict = g.get("compatNote", "Compatible")
            print(f"  • {title} — Note: {verdict}")

    # Search Hardware
    matched_gpus = [
        gpu for gpu in gpus
        if q in str(gpu.get("name", "")).lower() or q in str(gpu.get("vendor", "")).lower()
    ]
    if matched_gpus:
        print(f"\n[Hardware GPUs — {len(matched_gpus)} matches]")
        for gpu in matched_gpus:
            name = gpu.get("name")
            status = gpu.get("psu_badge", "Safe")
            spike = gpu.get("system_peak_watts", 0)
            print(f"  • {name} — Peak Spike: ~{spike}W | PSU: {status}")

    print("\n" + "=" * 76 + "\n")


def start_server(port: int = PORT) -> None:
    """Start the HTTP server on specified port."""
    handler = DatabaseHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"\n=======================================================")
        print(f" 🚀 Database Manager Server running on:")
        print(f"    http://127.0.0.1:{port}")
        print(f"    Static root: {WEB_DIR}")
        print(f"    Endpoints:   /api/status, /api/ai, /api/games, /api/hardware")
        print(f"    Press Ctrl+C to stop.")
        print(f"=======================================================\n")
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
        "--port",
        type=int,
        default=PORT,
        help=f"Port to bind web server (default: {PORT})",
    )
    args = parser.parse_args()

    if args.cli is not None:
        run_cli_summary(args.cli if args.cli != "" else None)
    else:
        start_server(args.port)


if __name__ == "__main__":
    main()
