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
    if (scores.get("intelligence_index") or 0) >= 55 or (scores.get("code_arena_elo") or 0) >= 1400:
        tier = "frontier"
        tags.append("frontier_intelligence")
    elif (scores.get("intelligence_index") or 0) >= 42:
        tier = "near_frontier"
        tags.append("near_frontier")
    elif (scores.get("intelligence_index") or 0) >= 25:
        tier = "mid_tier"
        tags.append("mid_tier")
    else:
        tier = "specialized"
        tags.append("specialized_tier")

    if (scores.get("code_arena_elo") or 0) >= 1320:
        tags.append("top_coding")
    if (model.get("context_tokens") or 0) >= 1_000_000:
        tags.append("long_context_1m")

    return {
        "id": model.get("id"),
        "name": model.get("name"),
        "provider": model.get("provider") or model.get("provider_family") or "Unknown",
        "origin_bucket": origin,
        "tier": tier,
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
    """Assign multi-axis gameplay, ownership, hardware-friendliness, and storage tags to a game."""
    tags: list[str] = []
    ownership = str(game.get("ownership") or "wishlist").lower()
    tags.append("owned_library" if ownership == "owned" else "wishlist")
    if game.get("steamAppId"):
        tags.append("steam_verified")
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
        "ownership": ownership,
        "steam_app_id": game.get("steamAppId"),
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
    ownership_counts = dict(Counter(c["ownership"] for c in classified))
    return {
        "total": len(classified),
        "ownership_counts": ownership_counts,
        "genre_counts": genre_counts,
        "discovery_seeds": tax.get("discovery_expansion_seeds", []),
        "games": classified,
    }


def classify_media_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Assign media_type subdomain, origin family, and adaptation/relation tags."""
    media_type = str(entry.get("media_type", "comic")).lower()
    origin_raw = str(entry.get("origin", "Unknown"))
    origin_l = origin_raw.lower()
    if "manhua" in origin_l:
        origin_family = "manhua"
    elif "manhwa" in origin_l:
        origin_family = "manhwa"
    elif "manga" in origin_l:
        origin_family = "manga"
    elif "web novel" in origin_l or "light novel" in origin_l or "novel" in origin_l:
        origin_family = "novel"
    else:
        origin_family = media_type

    anime = str(entry.get("anime", "**None**"))
    live = str(entry.get("live_action", "**None**"))
    link = str(entry.get("link", ""))
    tags: list[str] = [media_type, origin_family]
    if "comix.to/title/" in link:
        tags.append("direct_comix_link")
    elif "browse?q=" in link:
        tags.append("browse_fallback")
    if not anime.startswith("**None**"):
        if "fan motion" in anime.lower() or "unofficial" in anime.lower():
            tags.append("fan_motion_or_unofficial")
        else:
            tags.append("official_anime_or_donghua")
    if not live.startswith("**None**"):
        tags.append("has_live_action")
    if "in production" in (anime + " " + live).lower():
        tags.append("in_production")
    if entry.get("relations"):
        tags.append("interlinked_franchise")
    if entry.get("watchlist_status"):
        tags.append(str(entry["watchlist_status"]))

    return {
        "id": entry.get("id", ""),
        "name": entry.get("name", ""),
        "alt": entry.get("alt", ""),
        "media_type": media_type,
        "origin": origin_raw,
        "origin_family": origin_family,
        "franchise_id": entry.get("franchise_id", ""),
        "watchlist_status": entry.get("watchlist_status", ""),
        "tags": tags,
    }


def classify_media_catalog() -> dict[str, Any]:
    """Classify all entries in data/media/media_catalog.json."""
    media_path = DATA_DIR / "media" / "media_catalog.json"
    items = _load_json(media_path) if media_path.exists() else []
    classified = [classify_media_entry(item) for item in items]
    media_type_counts = dict(Counter(c["media_type"] for c in classified))
    origin_counts = dict(Counter(c["origin_family"] for c in classified))
    tag_counts = dict(Counter(t for c in classified for t in c["tags"]))
    return {
        "total": len(classified),
        "media_type_counts": media_type_counts,
        "origin_counts": origin_counts,
        "tag_counts": tag_counts,
        "media": classified,
    }


def classify_github_catalog() -> dict[str, Any]:
    """Classify GitHub repositories by activity bucket, CI status, and fork drift."""
    from github.scanner import get_cached_repos, triage_repositories

    triaged = triage_repositories(get_cached_repos())
    bucket_map: list[tuple[str, str]] = [
        ("section_1", "active_0_4d"),
        ("section_2", "mid_4_8d"),
        ("section_3", "dormant"),
    ]
    classified: list[dict[str, Any]] = []
    for sec_key, activity_bucket in bucket_map:
        for repo in triaged[sec_key]:
            run = repo.get("latest_run") or {}
            conc = run.get("conclusion")
            comp = repo.get("upstream_comparison") or {}
            tags: list[str] = [activity_bucket]
            tags.append("fork" if repo.get("is_fork") else ("private" if repo.get("is_private") else "owned"))
            if not run:
                tags.append("no_ci")
            elif conc == "success":
                tags.append("ci_passing")
            elif conc in ("failure", "cancelled", "timed_out", "action_required"):
                tags.append("ci_failing")
            else:
                tags.append("ci_running")
            if int(comp.get("behind_by") or 0) > 0:
                tags.append("behind_upstream")
            if int(repo.get("unreleased_commits_count") or 0) > 0:
                tags.append("unreleased_commits")
            if repo.get("stale_push_anomaly"):
                tags.append("push_commit_drift")

            classified.append(
                {
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "activity_bucket": activity_bucket,
                    "ci_conclusion": conc or ("running" if run else "none"),
                    "is_fork": bool(repo.get("is_fork")),
                    "tags": tags,
                }
            )

    bucket_counts = dict(Counter(c["activity_bucket"] for c in classified))
    tag_counts = dict(Counter(t for c in classified for t in c["tags"]))
    return {
        "total": len(classified),
        "bucket_counts": bucket_counts,
        "tag_counts": tag_counts,
        "repositories": classified,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify Games, LLM, Media & GitHub catalogs into multi-axis taxonomies")
    parser.add_argument("--games", action="store_true", help="Classify PC games catalog")
    parser.add_argument("--ai", action="store_true", help="Classify AI models catalog")
    parser.add_argument("--media", action="store_true", help="Classify Media & Adaptations catalog")
    parser.add_argument("--github", action="store_true", help="Classify GitHub repositories catalog")
    parser.add_argument("--chinese-oss", action="store_true", help="Filter AI output to Chinese & Open-Source models")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    out: dict[str, Any] = {}
    all_default = not (args.games or args.ai or args.media or args.github)
    if args.games or all_default:
        out["games"] = classify_games_catalog()
    if args.ai or all_default:
        out["ai"] = classify_ai_catalog(only_chinese_oss=args.chinese_oss)
    if args.media or all_default:
        out["media"] = classify_media_catalog()
    if args.github or all_default:
        out["github"] = classify_github_catalog()

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
    if "media" in out:
        md = out["media"]
        print(f"\n=== MEDIA CATALOG CLASSIFICATION ({md['total']} entries) ===")
        for mtype, cnt in sorted(md["media_type_counts"].items()):
            print(f"  • {mtype:<22} {cnt}")
    if "github" in out:
        gh = out["github"]
        print(f"\n=== GITHUB REPOS CLASSIFICATION ({gh['total']} repos) ===")
        for bucket, cnt in sorted(gh["bucket_counts"].items()):
            print(f"  • {bucket:<22} {cnt}")
    print("")


if __name__ == "__main__":
    main()
