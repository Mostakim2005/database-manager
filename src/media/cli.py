"""Unified CLI entry point for Media domain inside Database Manager."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from media import load_catalog  # noqa: E402
from media.adaptation_refresh import run_adaptation_refresh  # noqa: E402
from media.crawler import fetch_sitemaps  # noqa: E402
from media.franchise_builder import rebuild_and_save_catalog  # noqa: E402
from media.indexer import build_index  # noqa: E402
from media.link_health import audit_catalog_links_offline, check_catalog_links_live  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Media & Adaptations Domain CLI (Database Manager)")
    parser.add_argument("--verify", action="store_true", help="Verify catalog & sitemap index counts")
    parser.add_argument("--crawl", action="store_true", help="Crawl comix.to XML sitemaps with polite delay")
    parser.add_argument("--doctor", action="store_true", help="Run offline catalog consistency & coverage audit")
    parser.add_argument("--propose", action="store_true", help="Propose canonical comix.to link upgrades from sitemaps")
    parser.add_argument("--update", action="store_true", help="Probe public sources / refresh catalog proposals")
    parser.add_argument("--rebuild", action="store_true", help="Deduplicate, import Obsidian batch, and split multi-tier franchises")
    parser.add_argument("--enrich", action="store_true", help="Fetch public synopses, NSFW flags, and download local poster cache")
    parser.add_argument("--add", action="store_true", help="Propose (or --apply) adding a new media entry")
    parser.add_argument("--all", action="store_true", help="Run doctor + propose + probe workflow")
    parser.add_argument("--check-links", action="store_true", help="Audit reading & streaming link health")
    parser.add_argument("--live", action="store_true", help="Enable polite live HTTP probing for --check-links")
    parser.add_argument("--limit", type=int, default=10, help="Max links/titles to probe in live mode")
    parser.add_argument("--title", help="Title for --add or --update probe")
    parser.add_argument("--origin", default="Manga", help="Origin label for --add")
    parser.add_argument("--media-type", default="comic", choices=["comic", "light_novel", "anime", "donghua", "movie", "tv_series"], help="Media subdomain type for --add")
    parser.add_argument("--alt", default="", help="Alternate title(s) for --add or --update")
    parser.add_argument("--apply", action="store_true", help="Persist proposed changes to media_catalog.json")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    if args.rebuild or args.enrich:
        res = rebuild_and_save_catalog(enrich=args.enrich, download_posters=args.enrich)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    if args.crawl:
        count = fetch_sitemaps()
        if args.json:
            print(json.dumps({"crawled_sitemaps": count}, indent=2))
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
                media_type=args.media_type,
                alt=args.alt,
                apply=args.apply,
                limit=args.limit,
            )
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return

    catalog = load_catalog()
    urls = build_index(allow_missing=True)
    direct = sum(1 for item in catalog if "comix.to/title/" in item.get("link", ""))
    linked = sum(1 for item in catalog if item.get("relations"))
    payload = {
        "total_titles": len(catalog),
        "direct_comix_links": direct,
        "interlinked_entries": linked,
        "cached_sitemap_urls": len(urls),
        "healthy": len(catalog) > 0,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("\n=== Media Domain Verification ===")
        print(f"  Total catalog entries:      {payload['total_titles']}")
        print(f"  Direct comix.to links:      {payload['direct_comix_links']}")
        print(f"  Franchise-linked entries:   {payload['interlinked_entries']}")
        print(f"  Cached sitemap URLs:        {payload['cached_sitemap_urls']}\n")


if __name__ == "__main__":
    main()
