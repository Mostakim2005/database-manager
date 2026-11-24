"""Sitemap crawler module for Media domain."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from media import SITEMAPS_DIR
from media.fetch_helper import safe_get


def fetch_sitemaps(
    total_lists: int = 112,
    delay_sec: float = 1.0,
    sitemaps_dir: Path = SITEMAPS_DIR,
) -> int:
    """Download sitemap XML files ``list-1.xml`` through ``list-N.xml``."""
    sitemaps_dir.mkdir(parents=True, exist_ok=True)
    print(f"[media.crawler] Checking and fetching sitemaps in {sitemaps_dir}...")

    downloaded = 0
    for i in range(1, total_lists + 1):
        fpath = sitemaps_dir / f"list-{i}.xml"
        if not fpath.exists() or fpath.stat().st_size < 100:
            url = f"https://comix.to/sitemap/list-{i}.xml"
            body = ""
            res = safe_get(url, timeout=15.0, delay_sec=0.0, retries=1)
            if res and res[0] == 200 and "<urlset" in res[1]:
                body = res[1]
            else:
                proc = subprocess.run(
                    ["curl", "-s", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", url],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode == 0 and "<urlset" in proc.stdout:
                    body = proc.stdout

            if body:
                fpath.write_text(body, encoding="utf-8")
                downloaded += 1
                if i % 10 == 0 or i == total_lists:
                    print(f"[media.crawler] Downloaded list-{i}.xml (enforcing {delay_sec}s delay)")
            else:
                print(f"[media.crawler] Warning: Failed to retrieve list-{i}.xml")
            if delay_sec > 0:
                time.sleep(delay_sec)

    xml_count = len(list(sitemaps_dir.glob("*.xml")))
    print(f"[media.crawler] Crawl complete. {downloaded} new sitemaps downloaded ({xml_count} total).")
    return xml_count
