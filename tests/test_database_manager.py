#!/usr/bin/env python3
"""Zero-dependency unittest regression suite for Database Manager."""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

import db_export  # noqa: E402
import server  # noqa: E402


class TestDbExport(unittest.TestCase):
    def test_parse_context_window_variants(self) -> None:
        self.assertEqual(db_export.parse_context_window("1M"), 1_000_000)
        self.assertEqual(db_export.parse_context_window("200k"), 200_000)
        self.assertEqual(db_export.parse_context_window(128000), 128_000)
        self.assertEqual(db_export.parse_context_window(None), 128_000)
        self.assertEqual(db_export.parse_context_window("invalid"), 128_000)

    def test_compile_database_atomic_and_install_gb_populated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test.sqlite"
            db_export.compile_database(target_path=db_path)
            self.assertTrue(db_path.exists())
            self.assertFalse(db_path.with_suffix(".sqlite.tmp").exists())

            conn = sqlite3.connect(db_path)
            try:
                cur = conn.cursor()
                ai_cnt = cur.execute("SELECT COUNT(*) FROM ai_models").fetchone()[0]
                game_cnt = cur.execute("SELECT COUNT(*) FROM pc_games").fetchone()[0]
                bench_cnt = cur.execute("SELECT COUNT(*) FROM game_benchmarks").fetchone()[0]
                nonzero_gb = cur.execute("SELECT COUNT(*) FROM pc_games WHERE install_gb > 0").fetchone()[0]
                comp_cnt = cur.execute("SELECT COUNT(*) FROM pc_components").fetchone()[0]
                gpu_cnt = cur.execute("SELECT COUNT(*) FROM pc_gpus").fetchone()[0]
                cpu_cnt = cur.execute("SELECT COUNT(*) FROM pc_cpus").fetchone()[0]
                media_cnt = cur.execute("SELECT COUNT(*) FROM media_catalog").fetchone()[0]
                book_cnt = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
                phone_cnt = cur.execute("SELECT COUNT(*) FROM phones").fetchone()[0]
                self.assertGreaterEqual(ai_cnt, 45)
                self.assertGreaterEqual(game_cnt, 160)
                self.assertGreaterEqual(bench_cnt, 150)
                self.assertGreaterEqual(nonzero_gb, 160)
                self.assertGreaterEqual(comp_cnt, 80)
                self.assertGreaterEqual(gpu_cnt, 15)
                self.assertGreaterEqual(cpu_cnt, 6)
                self.assertGreaterEqual(media_cnt, 104)
                self.assertGreaterEqual(book_cnt, 4)
                self.assertGreaterEqual(phone_cnt, 4)
            finally:
                conn.close()

    def test_separated_domain_sqlite_table_isolation(self) -> None:
        counts = db_export.compile_separated_domains()
        self.assertEqual(set(counts.keys()), {"pc", "games", "ai", "media", "book", "phone", "github"})

        pc_conn = sqlite3.connect(db_export.DATA_DIR / "pc" / "pc.sqlite")
        book_conn = sqlite3.connect(db_export.DATA_DIR / "book" / "book.sqlite")
        try:
            pc_tables = {r[0] for r in pc_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            book_tables = {r[0] for r in book_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            self.assertIn("pc_components", pc_tables)
            self.assertIn("pc_gpus", pc_tables)
            self.assertNotIn("ai_models", pc_tables)
            self.assertNotIn("books", pc_tables)
            self.assertEqual(book_tables, {"books", "_meta"})
        finally:
            pc_conn.close()
            book_conn.close()

    def test_verify_database_handles_empty_tables(self) -> None:
        conn = sqlite3.connect(":memory:")
        try:
            db_export.create_schema(conn)
            db_export.verify_database(conn)
        finally:
            conn.close()


class TestServerCliAndHttp(unittest.TestCase):
    def test_search_databases_matches_provider_and_scores(self) -> None:
        res = server.search_databases("anthropic")
        self.assertGreaterEqual(len(res["ai_models"]), 1)
        for m in res["ai_models"]:
            self.assertNotEqual(m["provider"], "N/A")
            self.assertIsNotNone(m["intelligence_index"])

        res_gpu = server.search_databases("rx 6600")
        self.assertGreaterEqual(len(res_gpu["gpus"]), 1)

    def test_http_endpoints_headers_and_cors(self) -> None:
        httpd = server.ReusableThreadingHTTPServer(("127.0.0.1", 0), server.DatabaseHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{port}"

            # 1. /api/status with loopback Origin
            req = urllib.request.Request(f"{base}/api/status", headers={"Origin": base})
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
                self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), base)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(data["status"], "online")
                self.assertGreaterEqual(data["counts"]["pc"], 70)
                self.assertGreaterEqual(data["counts"]["games"], 51)
                self.assertGreaterEqual(data["counts"]["ai_models"], 45)
                self.assertGreaterEqual(data["counts"]["media"], 104)
                self.assertGreaterEqual(data["counts"]["book"], 4)
                self.assertGreaterEqual(data["counts"]["phone"], 4)
                self.assertIn("groups", data["registry"])
                self.assertTrue(data.get("capabilities", {}).get("github_async_refresh"))
                labels = {d["domain"]: d.get("short_label") for d in data.get("domains", [])}
                self.assertEqual(labels.get("pc"), "PC")
                self.assertEqual(labels.get("ai"), "LLM")

            # 2. /api/pc with untrusted Origin must not reflect CORS
            req_evil = urllib.request.Request(f"{base}/api/pc", headers={"Origin": "https://evil.example"})
            with urllib.request.urlopen(req_evil, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                self.assertIsNone(resp.headers.get("Access-Control-Allow-Origin"))
                pc_payload = json.loads(resp.read().decode("utf-8"))
                self.assertIn("gpus", pc_payload)
                self.assertIn("psus", pc_payload)

            # 2b. Alias-aware /api/domain/<alias> lookup & new book/phone endpoints
            with urllib.request.urlopen(f"{base}/api/domain/learning", timeout=5) as resp:
                alias_res = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(alias_res["domain"], "book")
                self.assertGreaterEqual(len(alias_res["data"]["books"]), 4)
            with urllib.request.urlopen(f"{base}/api/phone", timeout=5) as resp:
                phones = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(len(phones["phones"]), 4)

            # 2c. Strict Alpha 2 cutover: removed legacy endpoints return 404
            for retired in ("/api/hardware", "/api/cpus", "/api/components", "/api/manga", "/api/cross/ai-vram-fit"):
                with self.assertRaises(urllib.error.HTTPError) as ctx_ret:
                    urllib.request.urlopen(f"{base}{retired}", timeout=5)
                self.assertEqual(ctx_ret.exception.code, 404, f"Expected 404 for retired route {retired}")

            # 3. Directory listing must be forbidden (403)
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(f"{base}/games/js/", timeout=5)
            self.assertEqual(ctx.exception.code, 403)

            # 4. Shared cross-domain navigation bar & Overview Hub serve safely (zero innerHTML)
            with urllib.request.urlopen(f"{base}/shared/nav.js", timeout=5) as resp:
                nav_js = resp.read().decode("utf-8")
                self.assertEqual(resp.status, 200)
                self.assertNotIn("innerHTML", nav_js)
            with urllib.request.urlopen(f"{base}/index.html", timeout=5) as resp:
                idx_html = resp.read().decode("utf-8")
                self.assertIn("home-overview", idx_html)
            with urllib.request.urlopen(f"{base}/ai/index.html", timeout=5) as resp:
                ai_html = resp.read().decode("utf-8")
                self.assertIn("PROVIDER_THEMES", ai_html)
                self.assertIn("groupByProvider", ai_html)
                self.assertIn("matrixAccordion", ai_html)
                self.assertIn("tasksAccordion", ai_html)
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    unittest.main()
