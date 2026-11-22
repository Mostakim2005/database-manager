#!/usr/bin/env python3
"""Database Manager — Automated Game & LLM (Including Chinese/OSS) Taxonomy Classifier.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_ai_model(model: dict[str, Any], chinese_labs: list[str]) -> dict[str, Any]:
    """Assign origin bucket (Chinese OSS, Western Frontier, etc.) and capability tags."""
    haystack = " ".join(
        str(model.get(k, "") or "") for k in ("id", "name", "provider", "provider_family", "vendor")
    ).lower()
    is_chinese = any(lab in haystack for lab in chinese_labs)

    fc_caps = (model.get("fact_check", {}).get("capabilities") or {}) if isinstance(model.get("fact_check"), dict) else {}
    is_open = bool(
        model.get("open_weights")
        or fc_caps.get("open_weights")
        or str(model.get("classification", "")).lower() in ("open-source", "open_weights", "open source")
    )

    if is_chinese and is_open:
        origin = "chinese_oss"
    elif is_chinese:
        origin = "chinese_proprietary"
    elif is_open:
        origin = "western_oss"
    else:
        origin = "western_frontier"

    scores = model.get("scores") if isinstance(model.get("scores"), dict) else {}
    pricing = model.get("pricing") if isinstance(model.get("pricing"), dict) else {}
    tags: list[str] = []
    if is_chinese:
        tags.append("chinese_lab")
    if is_open:
        tags.append("open_weights")
    if pricing.get("is_free"):
        tags.append("free_tier")
    elif pricing.get("prompt_per_m") is not None and float(pricing["prompt_per_m"]) <= 0.5:
        tags.append("budget_value")
    if (scores.get("intelligence_index") or 0) >= 50:
        tags.append("frontier_intelligence")
    if (scores.get("code_arena_elo") or 0) >= 1320:
        tags.append("top_coding")
    if (model.get("context_tokens") or 0) >= 1_000_000:
        tags.append("long_context_1m")

    return {
        "id": model.get("id"),
        "name": model.get("name"),
        "provider": model.get("provider") or model.get("provider_family") or "Unknown",
        "origin_bucket": origin,
        "is_chinese": is_chinese,
        "is_open_weights": is_open,
        "tags": tags,
    }


def classify_ai_catalog(only_chinese_oss: bool = False) -> dict[str, Any]:
    """Classify every model in data/ai/models_master.json."""
    tax = _load_json(DATA_DIR / "ai" / "taxonomy.json")
    raw = _load_json(DATA_DIR / "ai" / "models_master.json")
    models = raw.get("models", [])
    classified = [classify_ai_model(m, tax["chinese_labs"]) for m in models]
    if only_chinese_oss:
        classified = [c for c in classified if c["is_chinese"] or c["is_open_weights"]]
    bucket_counts = dict(Counter(c["origin_bucket"] for c in classified))
    return {"total": len(classified), "bucket_counts": bucket_counts, "models": classified}


def classify_game(game: dict[str, Any]) -> dict[str, Any]:
    """Assign multi-axis gameplay, hardware-friendliness, and storage tags to a game."""
    tags: list[str] = []
    if game.get("priceModel") == "f2p":
        tags.append("free_to_play")
    if float(game.get("gpuMinTier") or 10) <= 3.0:
        tags.append("vega7_friendly")
    if (game.get("storageAdvice") or {}).get("verdict") == "hdd-fine":
        tags.append("hdd_safe")
    else:
        tags.append("ssd_recommended")
    if (game.get("campaign") or {}).get("exists"):
        tags.append("has_campaign")
    if (game.get("players") or {}).get("status") in ("very-active", "active"):
        tags.append("active_multiplayer")

    return {
        "id": game.get("id"),
        "name": game.get("name"),
        "genre": game.get("genre", "other"),
        "setting": game.get("setting", "other"),
        "tags": tags,
    }


def classify_games_catalog() -> dict[str, Any]:
    """Classify all games in data/games/games.json and attach discovery expansion seeds."""
    tax = _load_json(DATA_DIR / "games" / "taxonomy.json")
    games = _load_json(DATA_DIR / "games" / "games.json")
    classified = [classify_game(g) for g in games]
    genre_counts = dict(Counter(c["genre"] for c in classified))
    return {
        "total": len(classified),
        "genre_counts": genre_counts,
        "discovery_seeds": tax.get("discovery_expansion_seeds", []),
        "games": classified,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify Games & LLM catalogs into multi-axis taxonomies")
    parser.add_argument("--games", action="store_true", help="Classify PC games catalog")
    parser.add_argument("--ai", action="store_true", help="Classify AI models catalog")
    parser.add_argument("--chinese-oss", action="store_true", help="Filter AI output to Chinese & Open-Source models")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    out: dict[str, Any] = {}
    if args.games or not args.ai:
        out["games"] = classify_games_catalog()
    if args.ai or not args.games:
        out["ai"] = classify_ai_catalog(only_chinese_oss=args.chinese_oss)

    if args.json:
        print(json.dumps(out, indent=2))
        return

    if "ai" in out:
        ai = out["ai"]
        print(f"\n=== AI CATALOG CLASSIFICATION ({ai['total']} models) ===")
        for bucket, cnt in sorted(ai["bucket_counts"].items()):
            print(f"  • {bucket:<22} {cnt}")
    if "games" in out:
        gm = out["games"]
        print(f"\n=== GAMES CATALOG CLASSIFICATION ({gm['total']} titles) ===")
        for genre, cnt in sorted(gm["genre_counts"].items()):
            print(f"  • {genre:<22} {cnt}")
        print(f"  • Curated discovery expansion seeds: {len(gm['discovery_seeds'])}")
    print("")


if __name__ == "__main__":
    main()
