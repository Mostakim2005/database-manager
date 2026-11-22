#!/usr/bin/env python3
"""Domain-specific scraper & safe offline parser adapters for Database Manager."""

from __future__ import annotations

import html
import importlib.util
import json
import re
from typing import Any

from scrapers.base import FetchResult, fetch_with_fallback


def parse_bd_retail_html(raw_html: str, source_name: str = "BD Retail") -> list[dict[str, Any]]:
    """Parse Bangladesh retail GPU product cards (Star Tech / Ryans / UCC style HTML).

    Uses selectolax when installed (Tier 1 speed) and falls back cleanly to stdlib regex.
    """
    items: list[dict[str, Any]] = []
    if importlib.util.find_spec("selectolax") is not None:
        from selectolax.parser import HTMLParser  # type: ignore[import-not-found]
        tree = HTMLParser(raw_html)
        for card in tree.css(".p-item, .product-card, .product-thumb"):
            title_el = card.css_first("h4 a, .p-item-name a, .product-title")
            price_el = card.css_first(".p-item-price, .price-new, .price")
            if not title_el or not price_el:
                continue
            name = title_el.text(strip=True)
            price_digits = re.sub(r"[^0-9]", "", price_el.text(strip=True))
            if name and price_digits:
                items.append(
                    {
                        "name": name,
                        "price_bdt": int(price_digits),
                        "currency": "BDT",
                        "condition": "new",
                        "source": source_name,
                    }
                )
        if items:
            return items

    # Stdlib fallback parser for minimal HTML cards
    pattern = re.compile(
        r'class="[^"]*(?:p-item-name|product-title)[^"]*"[^>]*>(?:<a[^>]*>)?([^<]+)(?:</a>)?.*?'
        r'class="[^"]*(?:p-item-price|price-new|price)[^"]*"[^>]*>[^0-9]*([0-9][0-9,]*)',
        re.IGNORECASE | re.DOTALL,
    )
    for m in pattern.finditer(raw_html):
        name = html.unescape(m.group(1)).strip()
        price_val = int(m.group(2).replace(",", ""))
        items.append(
            {
                "name": name,
                "price_bdt": price_val,
                "currency": "BDT",
                "condition": "new",
                "source": source_name,
            }
        )
    return items


def parse_facebook_group_posts(raw_text: str) -> list[dict[str, Any]]:
    """Safely parse copied/exported Facebook Group secondhand GPU posts offline.

    Never automates logged-in Facebook accounts. Extracts GPU model, BDT price
    (e.g., '22k', '22,500 tk', 'BDT 18500'), and condition markers from pasted text.
    """
    gpu_re = re.compile(
        r"\b((?:RX|RTX|GTX)\s*\d{3,4}(?:\s*(?:XT|Ti|SUPER|S))?)\b",
        re.IGNORECASE,
    )
    price_re = re.compile(
        r"(?:৳|BDT|Tk\.?|Price\s*[:\-]?)?\s*(\d{1,3}(?:,\d{3})+|\d{2,3}(?:\.\d+)?\s*k|\d{4,6})\s*(?:tk|bdt|taka)?\b",
        re.IGNORECASE,
    )

    listings: list[dict[str, Any]] = []
    blocks = [b.strip() for b in re.split(r"\n\s*\n+", raw_text) if b.strip()]
    for idx, block in enumerate(blocks):
        gm = gpu_re.search(block)
        if not gm:
            continue
        model = re.sub(r"\s+", " ", gm.group(1).upper()).strip()
        # Search for price outside the GPU model number itself
        remainder = block[: gm.start()] + " " + block[gm.end() :]
        pm = price_re.search(remainder)
        if not pm:
            continue
        raw_p = pm.group(1).lower().replace(",", "").strip()
        if raw_p.endswith("k"):
            price_bdt = int(float(raw_p[:-1]) * 1000)
        else:
            price_bdt = int(float(raw_p))
        if price_bdt < 3000 or price_bdt > 500000:
            continue
        listings.append(
            {
                "id": f"fb-{idx + 1}-{model.lower().replace(' ', '-')}",
                "gpu_model": model,
                "price_bdt": price_bdt,
                "currency": "BDT",
                "condition": "used",
                "source": "Facebook Group (Manual Paste)",
                "snippet": block[:140],
            }
        )
    return listings


def fetch_openrouter_models(timeout: int = 15) -> tuple[FetchResult, list[dict[str, Any]]]:
    """Tier 0 adapter: Fetch AI model catalog from OpenRouter public JSON API."""
    res = fetch_with_fallback("https://openrouter.ai/api/v1/models", tiers=("tier0", "tier1"), timeout=timeout)
    if not res.ok:
        return res, []
    try:
        payload = json.loads(res.content)
        return res, payload.get("data", [])
    except Exception as exc:
        res.ok = False
        res.error = f"JSON parse error: {exc}"
        return res, []


def fetch_steam_app_specs(app_id: int, timeout: int = 15) -> tuple[FetchResult, dict[str, Any]]:
    """Tier 0 adapter: Fetch PC game requirements and USD pricing from Steam Store API."""
    url = f"https://store.steampowered.com/api/appdetails?appids={int(app_id)}&cc=us&l=en"
    res = fetch_with_fallback(url, tiers=("tier0", "tier1"), timeout=timeout)
    if not res.ok:
        return res, {}
    try:
        payload = json.loads(res.content)
        entry = payload.get(str(app_id), {})
        if not entry.get("success"):
            return res, {}
        data = entry.get("data", {})
        return res, {
            "steam_appid": app_id,
            "name": data.get("name"),
            "is_free": data.get("is_free", False),
            "price_usd": (data.get("price_overview", {}).get("final", 0) / 100.0) if data.get("price_overview") else 0.0,
            "pc_requirements": data.get("pc_requirements", {}),
        }
    except Exception as exc:
        res.ok = False
        res.error = f"JSON parse error: {exc}"
        return res, {}
