#!/usr/bin/env python3
"""Unit tests for full PC & Peripherals compatibility engine and Game/LLM taxonomy classifiers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

import catalog_classifier  # noqa: E402
import compatibility_engine  # noqa: E402


class TestCompatibilityEngine(unittest.TestCase):
    def test_default_5600gt_rx6600_build_is_compatible(self) -> None:
        res = compatibility_engine.evaluate_default_build()
        self.assertTrue(res["compatible"], f"Unexpected errors: {res['errors']}")
        self.assertEqual(res["psu_analysis"]["status"], "pass")
        self.assertGreater(res["estimated_total_bdt"], 0)
        # Should emit PCIe 3.0 note for Gen4 SSD and 3-in-1 cable note for pen display
        joined_notes = " ".join(res["notes"]).lower()
        self.assertIn("pcie", joined_notes)
        self.assertIn("pen display", joined_notes)

    def test_catches_socket_ddr_psu_tv_and_smr_issues(self) -> None:
        cat = compatibility_engine.load_components()
        by_id = lambda sec, key: next(x for x in cat[sec] if x["id"] == key)
        bad_build = {
            "cpu": by_id("cpus", "ryzen-5-7600"),  # AM5
            "motherboard": by_id("motherboards", "msi-b450m-pro-vdh-max"),  # AM4 + DDR4
            "ram": by_id("ram", "gskill-32gb-ddr5-6000"),  # DDR5
            "gpu": by_id("gpus", "rx-7800-xt"),  # 263W -> 611W peak on 550W PSU
            "hdds": [by_id("hdds", "seagate-barracuda-2tb-smr")],
            "tv": by_id("tvs", "budget-4k-60-tv"),
            "psu_watts": 550,
        }
        res = compatibility_engine.evaluate_build(bad_build)
        self.assertFalse(res["compatible"])
        err_text = " ".join(res["errors"]).lower()
        warn_text = " ".join(res["warnings"]).lower()
        self.assertIn("socket mismatch", err_text)
        self.assertIn("ram mismatch", err_text)
        self.assertIn("psu ocp trip risk", err_text)
        self.assertIn("smr hdd", warn_text)
        self.assertIn("4:4:4", warn_text)


class TestCatalogClassifiers(unittest.TestCase):
    def test_ai_classifier_identifies_chinese_oss_and_western_frontier(self) -> None:
        res = catalog_classifier.classify_ai_catalog()
        self.assertGreaterEqual(res["total"], 26)
        self.assertGreater(res["bucket_counts"].get("chinese_oss", 0), 0)
        self.assertGreater(res["bucket_counts"].get("western_frontier", 0), 0)

        cn_only = catalog_classifier.classify_ai_catalog(only_chinese_oss=True)
        self.assertGreater(cn_only["total"], 0)
        for m in cn_only["models"]:
            self.assertTrue(m["is_chinese"] or m["is_open_weights"])

    def test_games_classifier_and_discovery_seeds(self) -> None:
        res = catalog_classifier.classify_games_catalog()
        self.assertGreaterEqual(res["total"], 51)
        self.assertGreaterEqual(len(res["discovery_seeds"]), 5)
        self.assertIn("classic-rts", res["genre_counts"])


if __name__ == "__main__":
    unittest.main()
