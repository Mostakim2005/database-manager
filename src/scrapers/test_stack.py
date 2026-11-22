#!/usr/bin/env python3
"""Interactive & CI-safe probe to test installed scraper tiers and adapters.

Examples:
    python src/scrapers/test_stack.py
    python src/scrapers/test_stack.py --live --dry-run
    python src/scrapers/test_stack.py --fb-file fb_posts.txt --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from scrapers.adapters import (  # noqa: E402
    fetch_openrouter_models,
    fetch_steam_app_specs,
    parse_bd_retail_html,
    parse_facebook_group_posts,
)
from scrapers.base import (  # noqa: E402
    compute_record_diff,
    detect_installed_tiers,
    fetch_with_fallback,
    format_diff_report,
)

SAMPLE_BD_HTML = """
<div class="p-item">
  <h4 class="p-item-name"><a href="#">Sapphire Pulse RX 6600 8GB</a></h4>
  <div class="p-item-price">28,500৳</div>
</div>
<div class="p-item">
  <h4 class="p-item-name"><a href="#">ZOTAC RTX 4060 8GB Twin Edge</a></h4>
  <div class="p-item-price">39,900৳</div>
</div>
"""

SAMPLE_FB_TEXT = """
Selling my Sapphire RX 6600 8GB, 1 year used, box available. Price: 21.5k tk fixed. Location Mirpur.

GTX 1660 Super 6GB fresh condition, asking 14,500 BDT slightly negotiable.
"""


def run_offline_self_test() -> dict[str, object]:
    """Verify parsers and dry-run diff engine with zero network calls."""
    bd_items = parse_bd_retail_html(SAMPLE_BD_HTML, source_name="Star Tech Fixture")
    fb_items = parse_facebook_group_posts(SAMPLE_FB_TEXT)
    diff = compute_record_diff(
        existing=[{"id": "rx-6600", "price_bdt": 29500}],
        incoming=[{"id": "rx-6600", "price_bdt": 28500}, {"id": "rtx-4060", "price_bdt": 39900}],
    )
    return {
        "bd_retail_parsed": len(bd_items),
        "fb_posts_parsed": len(fb_items),
        "diff_summary": {
            "added": diff["added_count"],
            "changed": diff["changed_count"],
            "removed": diff["removed_count"],
        },
        "diff_text": format_diff_report(diff, label="Offline Fixture Dry-Run"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Test Database Manager multi-tier scraper stack")
    parser.add_argument("--live", action="store_true", help="Run live network probes against public targets")
    parser.add_argument("--dry-run", action="store_true", help="Preview diffs without modifying any dataset")
    parser.add_argument("--fb-file", help="Path to copied Facebook Group text file to parse safely offline")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    tiers = detect_installed_tiers()
    offline = run_offline_self_test()
    report: dict[str, object] = {"installed_tiers": tiers, "offline_self_test": offline}

    if args.fb_file:
        text = Path(args.fb_file).read_text(encoding="utf-8")
        report["fb_file_listings"] = parse_facebook_group_posts(text)

    if args.live:
        or_res, or_models = fetch_openrouter_models()
        steam_res, steam_data = fetch_steam_app_specs(813780)  # Age of Empires II: DE
        star_res = fetch_with_fallback("https://www.startech.com.bd/component/graphics-card", tiers=("tier1", "tier2", "tier0"))
        ryans_res = fetch_with_fallback("https://www.ryans.com/category/desktop-component-graphics-card", tiers=("tier1", "tier2", "tier0"))
        bikroy_res = fetch_with_fallback("https://bikroy.com/en/ads/bangladesh?query=rx+6600", tiers=("tier2", "tier1", "tier0"))

        report["live_probes"] = {
            "openrouter_tier0": {"ok": or_res.ok, "tier": or_res.tier_used, "models_found": len(or_models), "error": or_res.error},
            "steam_tier0": {"ok": steam_res.ok, "tier": steam_res.tier_used, "game": steam_data.get("name"), "error": steam_res.error},
            "startech_bd": {"ok": star_res.ok, "tier": star_res.tier_used, "status": star_res.status_code, "error": star_res.error},
            "ryans_bd": {"ok": ryans_res.ok, "tier": ryans_res.tier_used, "status": ryans_res.status_code, "error": ryans_res.error},
            "bikroy_bd": {"ok": bikroy_res.ok, "tier": bikroy_res.tier_used, "status": bikroy_res.status_code, "error": bikroy_res.error},
        }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("\n=== SCRAPER TIER AVAILABILITY ===")
    for name, info in tiers.items():
        mark = "INSTALLED" if info["available"] else "missing"
        print(f"  [{mark:<9}] {name}")
    print("\n" + str(offline["diff_text"]))
    print(f"  • BD Retail fixture parsed: {offline['bd_retail_parsed']} cards")
    print(f"  • FB Group fixture parsed:  {offline['fb_posts_parsed']} listings")
    if args.fb_file:
        print(f"  • Custom FB file parsed:    {len(report.get('fb_file_listings', []))} listings")
    if args.live:
        print("\n=== LIVE NETWORK PROBES ===")
        for k, v in report["live_probes"].items():  # type: ignore[union-attr]
            print(f"  • {k}: {v}")
    print("")


if __name__ == "__main__":
    main()
