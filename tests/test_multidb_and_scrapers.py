#!/usr/bin/env python3
"""Unit & integration tests for separated domain SQLite hub, verifier, scaffold CLI, and scrapers."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

import db_export  # noqa: E402
import db_hub  # noqa: E402
import db_verify  # noqa: E402
import server  # noqa: E402
from scrapers.adapters import parse_bd_retail_html, parse_facebook_group_posts  # noqa: E402
from scrapers.base import compute_record_diff, detect_installed_tiers  # noqa: E402
from scrapers.bd_hardware import compute_live_price_sync  # noqa: E402
from scrapers.benchmark_ingest import ingest_csv  # noqa: E402
from scrapers.multi_site_ai import sync_multi_site_ai  # noqa: E402
from scrapers.multi_site_components import sync_multi_site_components  # noqa: E402
from scrapers.multi_site_games import sync_multi_site_games  # noqa: E402
from scrapers.test_stack import SAMPLE_BD_HTML, SAMPLE_FB_TEXT, run_offline_self_test  # noqa: E402


class TestMultiDomainHubAndVerify(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        db_export.compile_separated_domains()

    def test_schema_verification_passes_all_domains(self) -> None:
        report = db_verify.verify_all()
        self.assertTrue(report["ok"], f"Schema verification errors: {report}")
        names = {d["domain"] for d in report["domains"]}
        self.assertEqual(names, {"pc", "games", "ai", "media", "book", "phone", "github"})
        reg = db_hub.load_registry()
        self.assertEqual(db_hub.resolve_domain_key("learning", reg), "book")
        self.assertEqual(db_hub.resolve_domain_key("manga", reg), "media")
        self.assertEqual(db_hub.resolve_domain_key("hardware", reg), "pc")

    def test_domain_health_and_cross_domain_views(self) -> None:
        health = db_hub.query_domain_health()
        self.assertEqual(len(health), 7)
        for item in health:
            self.assertTrue(item["compiled"])
            self.assertGreater(item["record_count"], 0)
            self.assertFalse(item["is_stale"])
            self.assertEqual(len(item["content_sha256"]), 64)
            self.assertTrue(item.get("display_name"))
            self.assertTrue(item.get("group"))

        self.assertFalse(hasattr(db_hub, "query_ai_vram_fit"))

        g_res = db_hub.query_games_by_gpu(gpu_id="rx-6600", max_psu_watts=550)
        self.assertTrue(g_res["psu_safe"])
        self.assertGreaterEqual(g_res["total_games"], 51)
        self.assertGreater(g_res["recommended_count"], 0)

        b_res = db_hub.query_game_benchmarks_with_pc(gpu_id="rx-6600")
        self.assertGreater(b_res["total_benchmarks"], 0)
        self.assertIn("avg_fps", b_res["benchmarks"][0])
        self.assertIn("gpu_name", b_res["benchmarks"][0])

        combos_res = db_hub.query_cpu_gpu_combos(cpu_id="ryzen-5-5600gt")
        self.assertGreater(combos_res["total_combos"], 0)
        self.assertIn("cpu_id", combos_res["combos"][0])
        self.assertIn("gpu_id", combos_res["combos"][0])

    def test_init_domain_scaffold_in_temp_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            data_root = Path(td)
            created = db_export.init_domain_scaffold("Budget Laptops", data_root=data_root)
            self.assertTrue((created / "budget_laptops.json").exists())
            self.assertTrue((created / "schema.json").exists())
            reg = json.loads((data_root / "registry.json").read_text(encoding="utf-8"))
            self.assertIn("budget_laptops", reg["domains"])
            self.assertEqual(reg["domains"]["budget_laptops"]["display_name"], "Budget Laptops")

    def test_cross_domain_http_endpoints(self) -> None:
        httpd = server.ReusableThreadingHTTPServer(("127.0.0.1", 0), server.DatabaseHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{port}"
            with urllib.request.urlopen(f"{base}/api/domains", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(len(data["health"]), 7)
            with urllib.request.urlopen(f"{base}/api/cross/games-by-gpu?gpu=rx-6600&psu=550", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data["psu_safe"])
                self.assertGreaterEqual(data["total_games"], 51)
            with urllib.request.urlopen(f"{base}/api/cross/game-benchmarks?gpu=rx-6600", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertGreater(data["total_benchmarks"], 0)
            with urllib.request.urlopen(f"{base}/api/cross/cpu-gpu-combos?cpu=ryzen-5-5600gt", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertGreater(data["total_combos"], 0)
            with urllib.request.urlopen(f"{base}/api/cross/check-build", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data["compatible"])
                self.assertEqual(data["error_count"], 0)
            with urllib.request.urlopen(f"{base}/api/cross/games-storage", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(data["total_games"], 150)
                self.assertGreater(len(data["pc_storage_options"]), 5)
            with urllib.request.urlopen(f"{base}/api/ai/classified?chinese_oss=true", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertGreater(data["total"], 0)
                self.assertIn("chinese_oss", data["bucket_counts"])
            with urllib.request.urlopen(f"{base}/api/games/classified", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(data["total"], 51)
                self.assertGreater(len(data["discovery_seeds"]), 0)
        finally:
            httpd.shutdown()
            httpd.server_close()


class TestScrapersAndDryRunDiff(unittest.TestCase):
    def test_bd_retail_and_fb_parsers(self) -> None:
        bd = parse_bd_retail_html(SAMPLE_BD_HTML, source_name="Star Tech")
        self.assertEqual(len(bd), 2)
        self.assertEqual(bd[0]["price_bdt"], 28500)

        fb = parse_facebook_group_posts(SAMPLE_FB_TEXT)
        self.assertEqual(len(fb), 2)
        self.assertEqual(fb[0]["gpu_model"], "RX 6600")
        self.assertEqual(fb[0]["price_bdt"], 21500)
        self.assertEqual(fb[1]["gpu_model"], "GTX 1660 SUPER")
        self.assertEqual(fb[1]["price_bdt"], 14500)

    def test_dry_run_diff_and_tier_probe(self) -> None:
        diff = compute_record_diff(
            existing=[{"id": "a", "v": 1}, {"id": "b", "v": 2}],
            incoming=[{"id": "a", "v": 1}, {"id": "b", "v": 3}, {"id": "c", "v": 4}],
        )
        self.assertEqual(diff["unchanged_count"], 1)
        self.assertEqual(diff["changed_count"], 1)
        self.assertEqual(diff["added_count"], 1)
        self.assertEqual(diff["removed_count"], 0)

        tiers = detect_installed_tiers()
        self.assertTrue(tiers["tier0_stdlib"]["available"])
        offline = run_offline_self_test()
        self.assertEqual(offline["bd_retail_parsed"], 2)
        self.assertEqual(offline["fb_posts_parsed"], 2)

    def test_bd_hardware_offline_diff_and_benchmark_ingest(self) -> None:
        catalog, diff_table = compute_live_price_sync(offline=True)
        self.assertGreater(len(diff_table), 0)
        self.assertIn("rx-6600", [row["id"] for row in diff_table])

        ingested = ingest_csv()
        self.assertGreaterEqual(ingested, 40)


class TestMultiSiteCatalogExpansion(unittest.TestCase):
    def test_multi_retailer_components_reconciliation(self) -> None:
        catalog, diff_table = sync_multi_site_components(offline=True)
        comps = [item for k, v in catalog.items() if isinstance(v, list) for item in v]
        self.assertGreaterEqual(len(comps), 55)
        # Check categories
        categories = {k for k, v in catalog.items() if isinstance(v, list)}
        expected_cats = {
            "cpus", "gpus", "motherboards", "ram", "ssds", "hdds",
            "monitors", "tvs", "keyboards", "mice", "graphics_tablets"
        }
        self.assertTrue(expected_cats.issubset(categories))

        # Check reconciliation fields
        for c in comps:
            self.assertIn("id", c)
            self.assertIn("price_bdt", c)
            self.assertIn("sources", c)
            self.assertIsInstance(c["sources"], list)
            if c.get("retailer_prices"):
                min_p = min(c["retailer_prices"].values())
                self.assertEqual(c["price_bdt"], min_p)
                self.assertEqual(c["best_retailer"], min(c["retailer_prices"], key=c["retailer_prices"].get))

    def test_multi_site_games_expansion(self) -> None:
        games, stats = sync_multi_site_games(offline=True)
        self.assertGreaterEqual(stats["total"], 150)
        seen_ids = set()
        seen_names = set()
        owned = 0
        wishlist = 0
        for g in games:
            self.assertIn("id", g)
            self.assertIn("name", g)
            self.assertIn("genre", g)
            self.assertIn("ownership", g)
            self.assertIn("priceModel", g)
            self.assertIn("hddSp", g)
            self.assertIn("storageAdvice", g)
            self.assertGreater(g["installGB"], 0)
            self.assertNotIn(g["id"], seen_ids)
            self.assertNotIn(g["name"], seen_names)
            seen_ids.add(g["id"])
            seen_names.add(g["name"])
            if g["ownership"] == "owned":
                owned += 1
            else:
                wishlist += 1
        self.assertGreaterEqual(owned, 105)
        self.assertGreaterEqual(wishlist, 48)

    def test_cross_domain_benchmarks_and_storage_summary(self) -> None:
        b_res = db_hub.query_game_benchmarks_with_pc()
        self.assertGreater(b_res["total_benchmarks"], 40)
        for row in b_res["benchmarks"]:
            self.assertIsNotNone(row["genre"], f"Unjoined benchmark game_id: {row['game_id']}")

        s_res = db_hub.query_games_storage_summary()
        self.assertGreaterEqual(s_res["total_games"], 150)
        self.assertGreater(s_res["owned_install_gb"], 2000.0)
        self.assertGreater(len(s_res["pc_storage_options"]), 5)

    def test_wishlist_unread_tags_on_game_adaptations(self) -> None:
        books = json.loads((ROOT_DIR / "data" / "book" / "books.json").read_text(encoding="utf-8"))["books"]
        witcher_books = [b for b in books if "witcher" in b["title"].lower() or "metro 2033" in b["title"].lower()]
        self.assertGreaterEqual(len(witcher_books), 3)
        for b in witcher_books:
            self.assertEqual(b["ownership_status"], "wishlist")
            self.assertEqual(b["reading_status"], "queued")

        media = json.loads((ROOT_DIR / "data" / "media" / "media_catalog.json").read_text(encoding="utf-8"))
        wl_items = [m for m in media if m.get("watchlist_status")]
        self.assertGreaterEqual(len(wl_items), 6)
        for m in wl_items:
            self.assertIn(m["watchlist_status"], ("plan_to_watch", "plan_to_read"))

    def test_multi_source_ai_reconciliation(self) -> None:
        data, stats = sync_multi_site_ai(offline=True)
        self.assertGreaterEqual(stats["total"], 45)
        models = data.get("models", [])
        providers = {m["provider"] for m in models}
        self.assertIn("DeepSeek", providers)
        self.assertIn("Alibaba", providers)
        self.assertIn("Meta", providers)
        for m in models:
            self.assertIn("id", m)
            self.assertIn("scores", m)
            if "fact_check" in m and isinstance(m["fact_check"], dict):
                self.assertIn("capabilities", m["fact_check"])
                self.assertIn("sources", m["fact_check"])

    def test_all_seven_domains_record_counts(self) -> None:
        health = db_hub.query_domain_health()
        counts = {h["domain"]: h["record_count"] for h in health}
        self.assertGreaterEqual(counts.get("pc", 0), 70)
        self.assertGreaterEqual(counts.get("games", 0), 51)
        self.assertGreaterEqual(counts.get("ai", 0), 45)
        self.assertGreaterEqual(counts.get("media", 0), 104)
        self.assertGreaterEqual(counts.get("book", 0), 4)
        self.assertGreaterEqual(counts.get("phone", 0), 4)
        self.assertGreaterEqual(counts.get("github", 0), 35)


class TestMediaDomainIntegration(unittest.TestCase):
    def test_media_doctor_classifier_and_offline_links(self) -> None:
        import media
        from media import adaptation_refresh, link_health
        import catalog_classifier

        self.assertFalse((ROOT_DIR / "src" / "media" / "sync_vault.py").exists())
        catalog = media.load_catalog()
        self.assertGreaterEqual(len(catalog), 110)

        doc = adaptation_refresh.inspect_catalog_doctor(catalog)
        self.assertTrue(doc["healthy"], f"Media doctor reported issues: {doc}")
        self.assertGreater(doc["direct_comix_links"], 80)

        links_report = link_health.audit_catalog_links_offline()
        self.assertTrue(links_report["healthy"])
        self.assertGreater(links_report["total_links"], 100)
        self.assertIn("comix.to", links_report["top_hosts"])

        cls_report = catalog_classifier.classify_media_catalog()
        self.assertEqual(cls_report["total"], len(catalog))
        self.assertIn("manhua", cls_report["origin_counts"])
        self.assertIn("tv_series", cls_report["media_type_counts"])
        self.assertIn("light_novel", cls_report["media_type_counts"])

    def test_media_sitemap_proposals_and_interconnected_franchises(self) -> None:
        import media
        from media import adaptation_refresh

        catalog = media.load_catalog()
        outlander = [m for m in catalog if "outlander" in m.get("name", "").lower()]
        self.assertGreaterEqual(len(outlander), 1)
        self.assertEqual(outlander[0]["media_type"], "tv_series")
        joy_items = [m for m in catalog if m.get("franchise_id") == "joy-of-life"]
        self.assertGreaterEqual(len(joy_items), 3)

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            sitemaps_dir = td_path / "sitemaps"
            sitemaps_dir.mkdir()
            (sitemaps_dir / "list-1.xml").write_text(
                "<urlset><url><loc>https://comix.to/title/abc1-rebirth-of-the-ultimate-master</loc></url></urlset>",
                encoding="utf-8",
            )
            fake_catalog = [
                {
                    "id": "rebirth-ultimate-master",
                    "name": "Rebirth of the Ultimate Master",
                    "alt": "The Ultimate of All Ages",
                    "media_type": "comic",
                    "link": "https://comix.to/browse?q=Rebirth&sort=relevance%3Adesc",
                    "origin": "Chinese Manhua",
                    "anime": "**None**",
                    "live_action": "**None**",
                }
            ]
            proposals = adaptation_refresh.propose_link_upgrades(fake_catalog, sitemaps_dir=sitemaps_dir)
            self.assertEqual(len(proposals), 1)
            self.assertEqual(proposals[0]["proposed_link"], "https://comix.to/title/abc1-rebirth-of-the-ultimate-master")

    def test_media_http_endpoints_and_fetch_helper(self) -> None:
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from media import fetch_helper

        class ProbeHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/missing":
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<html><body>Joy of Life probe</body></html>")

            def log_message(self, *args):
                pass

        probe_srv = HTTPServer(("127.0.0.1", 0), ProbeHandler)
        probe_port = probe_srv.server_address[1]
        probe_thread = threading.Thread(target=probe_srv.serve_forever, daemon=True)
        probe_thread.start()

        api_srv = server.ReusableThreadingHTTPServer(("127.0.0.1", 0), server.DatabaseHandler)
        api_port = api_srv.server_address[1]
        api_thread = threading.Thread(target=api_srv.serve_forever, daemon=True)
        api_thread.start()

        orig_cf = fetch_helper.HAVE_CURL_CFFI
        try:
            fetch_helper.HAVE_CURL_CFFI = False
            ok_res = fetch_helper.probe_url_status(f"http://127.0.0.1:{probe_port}/ok", delay_sec=0)
            self.assertTrue(ok_res["ok"])
            self.assertEqual(ok_res["state"], "ok")

            bad_res = fetch_helper.probe_url_status(f"http://127.0.0.1:{probe_port}/missing", delay_sec=0)
            self.assertFalse(bad_res["ok"])
            self.assertEqual(bad_res["state"], "broken")

            base = f"http://127.0.0.1:{api_port}"
            with urllib.request.urlopen(f"{base}/api/media?q=Joy%20of%20Life", timeout=5) as resp:
                items = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(len(items), 3)
            with urllib.request.urlopen(f"{base}/api/media?media_type=tv_series", timeout=5) as resp:
                series = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(len(series), 2)
            with urllib.request.urlopen(f"{base}/api/media/doctor", timeout=5) as resp:
                doc = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(doc["doctor"]["healthy"])
            with urllib.request.urlopen(f"{base}/api/media/links", timeout=5) as resp:
                lnk = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(lnk["healthy"])
            with urllib.request.urlopen(f"{base}/api/media/classified", timeout=5) as resp:
                cls = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(cls["total"], 110)
        finally:
            fetch_helper.HAVE_CURL_CFFI = orig_cf
            probe_srv.shutdown()
            probe_srv.server_close()
            api_srv.shutdown()
            api_srv.server_close()


if __name__ == "__main__":
    unittest.main()
