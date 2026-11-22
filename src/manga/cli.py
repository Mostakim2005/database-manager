"""Unified CLI entry point for Manga domain inside Database Manager."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from manga.adaptation_refresh import run_adaptation_refresh  # noqa: E402
from manga.crawler import fetch_sitemaps  # noqa: E402
from manga.indexer import build_index  # noqa: E402
from manga.link_health import audit_catalog_links_offline, check_catalog_links_live  # noqa: E402
from manga.sync_vault import load_catalog, sync_to_obsidian  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Manga Manager Domain CLI (Database Manager)")
    parser.add_argument("--verify", action="store_true", help="Verify catalog & sitemap index counts")
    parser.add_argument("--crawl", action="store_true", help="Crawl comix.to XML sitemaps with polite delay")
    parser.add_argument("--sync", action="store_true", help="Sync manga catalog to Obsidian Manhua Links.md")
    parser.add_argument("--doctor", action="store_true", help="Run offline catalog consistency & coverage audit")
    parser.add_argument("--propose", action="store_true", help="Propose canonical comix.to link upgrades from sitemaps")
    parser.add_argument("--update", action="store_true", help="Probe public sources / refresh catalog proposals")
    parser.add_argument("--add", action="store_true", help="Propose (or --apply) adding a new title")
    parser.add_argument("--all", action="store_true", help="Run doctor + propose + probe workflow")
    parser.add_argument("--check-links", action="store_true", help="Audit reading & streaming link health")
    parser.add_argument("--live", action="store_true", help="Enable polite live HTTP probing for --check-links")
    parser.add_argument("--limit", type=int, default=10, help="Max links/titles to probe in live mode")
    parser.add_argument("--title", help="Title for --add or --update probe")
    parser.add_argument("--origin", default="Manga", help="Origin label for --add")
    parser.add_argument("--alt", default="", help="Alternate title(s) for --add or --update")
    parser.add_argument("--apply", action="store_true", help="Persist proposed changes to manga_catalog.json")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    if args.crawl:
        count = fetch_sitemaps()
        if args.json:
            print(json.dumps({"crawled_sitemaps": count}, indent=2))
        return

    if args.sync:
        synced = sync_to_obsidian()
        if args.json:
            print(json.dumps({"synced_titles": synced}, indent=2))
        return

    if args.check_links:
        report = (
            check_catalog_links_live(limit=args.limit)
            if args.live
            else audit_catalog_links_offline()
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    for mode_flag, mode_name in (
        (args.all, "all"),
        (args.add, "add"),
        (args.update, "update"),
        (args.propose, "propose"),
        (args.doctor, "doctor"),
    ):
        if mode_flag:
            report = run_adaptation_refresh(
                mode=mode_name,
                title=args.title,
                origin=args.origin,
                alt=args.alt,
                apply=args.apply,
                limit=args.limit,
            )
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return

    # Default or --verify
    catalog = load_catalog()
    urls = build_index(allow_missing=True)
    direct = sum(1 for item in catalog if "comix.to/title/" in item.get("link", ""))
    payload = {
        "total_titles": len(catalog),
        "direct_comix_links": direct,
        "cached_sitemap_urls": len(urls),
        "healthy": len(catalog) > 0,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("\n=== Manga Domain Verification ===")
        print(f"  Total catalog titles:       {payload['total_titles']}")
        print(f"  Direct comix.to links:      {payload['direct_comix_links']}")
        print(f"  Cached sitemap URLs:        {payload['cached_sitemap_urls']}\n")


if __name__ == "__main__":
    main()
