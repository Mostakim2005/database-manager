#!/usr/bin/env python3
"""Database Manager — SQLite Consolidated & Isolated Domain Export Pipeline.

Compiles JSON/CSV datasets across all registered domains (`pc`, `games`, `ai`,
`media`, `book`, `phone`, `github`) into:
  1. Consolidated multi-domain SQLite: `data/database.sqlite`
  2. Strictly isolated per-domain SQLite files: `data/<domain>/<domain>.sqlite`

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Callable

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SQLITE_PATH = DATA_DIR / "database.sqlite"
REGISTRY_PATH = DATA_DIR / "registry.json"


# ---------------------------------------------------------------------------
# Isolated Per-Domain Schema Creators
# ---------------------------------------------------------------------------

def create_ai_schema(conn: sqlite3.Connection) -> None:
    """Create normalized AI models table and indexes."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_models (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            vendor TEXT,
            openrouter_slug TEXT,
            intelligence_index REAL,
            coding_elo REAL,
            terminalbench_pct REAL,
            price_in_1m REAL,
            price_out_1m REAL,
            context_window INTEGER,
            open_weights INTEGER,
            raw_json TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_vendor ON ai_models(vendor);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_intel ON ai_models(intelligence_index DESC);")
    conn.commit()


def create_games_schema(conn: sqlite3.Connection) -> None:
    """Create normalized PC games and benchmark tables and indexes."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pc_games (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            genre TEXT,
            ownership TEXT,
            steam_app_id INTEGER,
            price_model TEXT,
            price_usd REAL,
            campaign_quality REAL,
            ai_score REAL,
            graphics_score REAL,
            setting TEXT,
            install_gb REAL,
            gpu_min_tier REAL,
            gpu_rec_tier REAL,
            compat_note TEXT,
            playable_fps TEXT,
            raw_json TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_genre ON pc_games(genre);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_ownership ON pc_games(ownership);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_price ON pc_games(price_usd);")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS game_benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            cpu_name TEXT NOT NULL,
            gpu_id TEXT NOT NULL,
            resolution TEXT NOT NULL,
            preset TEXT NOT NULL,
            avg_fps REAL,
            low_1pct_fps REAL,
            low_01pct_fps REAL,
            source_url TEXT,
            recorded_at TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bench_game_gpu ON game_benchmarks(game_id, gpu_id);")
    conn.commit()


def create_pc_schema(conn: sqlite3.Connection) -> None:
    """Create unified PC components, GPUs, CPUs, and retail prices tables."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pc_components (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            brand TEXT,
            price_bdt REAL,
            price_usd REAL,
            specs_json TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comp_cat ON pc_components(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comp_brand ON pc_components(brand);")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pc_gpus (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            vendor TEXT,
            tier REAL,
            vram_gb REAL,
            vram_type TEXT,
            tdp_watts REAL,
            transient_multiplier REAL,
            gpu_peak_spike_watts REAL,
            system_peak_watts REAL,
            continuous_system_watts REAL,
            psu_550w_verdict TEXT,
            target_res TEXT,
            price_bdt_used REAL,
            price_bdt_retail REAL,
            price_usd REAL,
            raw_json TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gpu_tier ON pc_gpus(tier);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gpu_psu ON pc_gpus(psu_550w_verdict);")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pc_cpus (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            socket TEXT,
            cores INTEGER,
            threads INTEGER,
            base_clock_ghz REAL,
            boost_clock_ghz REAL,
            l3_cache_mb REAL,
            tdp_watts REAL,
            tier REAL,
            integrated_gpu TEXT,
            price_bdt REAL,
            price_usd REAL,
            notes TEXT,
            raw_json TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cpu_socket ON pc_cpus(socket);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cpu_tier ON pc_cpus(tier);")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hardware_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gpu_id TEXT NOT NULL,
            market TEXT NOT NULL,
            condition TEXT NOT NULL,
            currency TEXT NOT NULL,
            price REAL NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT,
            recorded_at TEXT NOT NULL
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_gpu_market ON hardware_prices(gpu_id, market);")
    conn.commit()


def create_media_schema(conn: sqlite3.Connection) -> None:
    """Create unified Media & Adaptations catalog table and indexes."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS media_catalog (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            alt TEXT,
            media_type TEXT NOT NULL,
            tier TEXT,
            sub_format TEXT,
            nsfw INTEGER,
            watchlist_status TEXT,
            parent_id TEXT,
            franchise_id TEXT,
            franchise_title TEXT,
            link TEXT,
            origin TEXT,
            anime TEXT,
            live_action TEXT,
            poster_url TEXT,
            description TEXT,
            release_year INTEGER,
            added_at TEXT,
            updated_at TEXT,
            has_direct_link INTEGER,
            has_anime INTEGER,
            has_live_action INTEGER,
            has_poster INTEGER,
            relations_json TEXT,
            raw_json TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_type ON media_catalog(media_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_tier ON media_catalog(tier);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_nsfw ON media_catalog(nsfw);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_year ON media_catalog(release_year);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_added ON media_catalog(added_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_franchise ON media_catalog(franchise_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_origin ON media_catalog(origin);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_name ON media_catalog(name);")
    conn.commit()


def create_book_schema(conn: sqlite3.Connection) -> None:
    """Create Book collection & reading tracker table and indexes."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            subject TEXT,
            format TEXT,
            ownership_status TEXT,
            reading_status TEXT,
            rating REAL,
            pages INTEGER,
            notes TEXT,
            raw_json TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_book_status ON books(ownership_status, reading_status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_book_subject ON books(subject);")
    conn.commit()


def create_phone_schema(conn: sqlite3.Connection) -> None:
    """Create Phone & Mobile specs + app/game support table and indexes."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS phones (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            brand TEXT,
            soc TEXT,
            gpu TEXT,
            ram_gb REAL,
            storage_gb REAL,
            display_hz REAL,
            display_type TEXT,
            battery_mah INTEGER,
            charging_watts REAL,
            os TEXT,
            price_bdt REAL,
            price_usd REAL,
            supported_games_count INTEGER,
            supported_apps_count INTEGER,
            supported_games_json TEXT,
            supported_apps_json TEXT,
            notes TEXT,
            raw_json TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_phone_brand ON phones(brand);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_phone_price ON phones(price_bdt);")
    conn.commit()


def create_github_schema(conn: sqlite3.Connection) -> None:
    """Create sanitized GitHub repositories table and indexes."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS github_repos (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            full_name TEXT NOT NULL,
            is_fork INTEGER,
            is_private INTEGER,
            default_branch TEXT,
            pushed_at TEXT,
            updated_at TEXT,
            description TEXT,
            parent_full_name TEXT,
            ahead_by INTEGER,
            behind_by INTEGER,
            latest_release_tag TEXT,
            ci_status TEXT,
            ci_conclusion TEXT,
            unbuilt_commits_count INTEGER,
            unreleased_commits_count INTEGER,
            raw_json TEXT
        );
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_pushed ON github_repos(pushed_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_ci ON github_repos(ci_conclusion);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_fork ON github_repos(is_fork);")
    conn.commit()


SCHEMA_CREATORS: dict[str, Callable[[sqlite3.Connection], None]] = {
    "ai": create_ai_schema,
    "games": create_games_schema,
    "pc": create_pc_schema,
    "media": create_media_schema,
    "book": create_book_schema,
    "phone": create_phone_schema,
    "github": create_github_schema,
}


def create_schema(conn: sqlite3.Connection) -> None:
    """Create normalized relational tables and indexes across all registered domains."""
    for creator in SCHEMA_CREATORS.values():
        creator(conn)


def create_extended_domain_tables(conn: sqlite3.Connection, domain: str) -> None:
    """Create schema tables strictly for the requested domain."""
    creator = SCHEMA_CREATORS.get(domain)
    if creator:
        creator(conn)


# ---------------------------------------------------------------------------
# Normalization Helpers & Exporters
# ---------------------------------------------------------------------------

def _first_not_none(*values: Any, default: Any = None) -> Any:
    """Return the first value that is not None (preserving explicit 0 / 0.0)."""
    for v in values:
        if v is not None:
            return v
    return default


def parse_context_window(ctx: Any) -> int:
    """Parse context window strings like '1M', '200k', or integer values."""
    if not ctx:
        return 128000
    if isinstance(ctx, (int, float)):
        return int(ctx)
    s = str(ctx).strip().upper()
    if s.endswith("M"):
        try:
            return int(float(s[:-1]) * 1000000)
        except ValueError:
            return 1000000
    if s.endswith("K"):
        try:
            return int(float(s[:-1]) * 1000)
        except ValueError:
            return 128000
    try:
        return int(float(s))
    except ValueError:
        return 128000


def export_ai_models(conn: sqlite3.Connection, data_root: Path = DATA_DIR) -> int:
    """Ingest AI models from JSON catalog into SQLite."""
    ai_json_path = data_root / "ai" / "models_master.json"
    if not ai_json_path.exists():
        ai_json_path = data_root / "ai" / "model-comparison.json"
    if not ai_json_path.exists():
        print(f"Warning: No AI models JSON found at {ai_json_path}")
        return 0

    with open(ai_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    models = data.get("models", data.get("records", []))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ai_models;")

    count = 0
    for m in models:
        model_id = str(m.get("id") or m.get("model") or m.get("name", "")).lower().replace(" ", "-")
        name = m.get("name") or m.get("model", "Unknown")
        vendor = m.get("provider") or m.get("vendor") or m.get("brand") or ""
        slug_val = m.get("openrouter_slug") or m.get("slug") or m.get("command_code", "")
        slug = slug_val if isinstance(slug_val, str) else json.dumps(slug_val)

        scores = m.get("scores", {}) if isinstance(m.get("scores"), dict) else {}
        intel = float(_first_not_none(scores.get("intelligence_index"), m.get("intelligence_index"), m.get("aa_intelligence_raw"), m.get("aa_index_v5"), default=0.0))

        elo = scores.get("code_arena_elo") or m.get("effective_scores", {}).get("code_arena_elo") or m.get("coding_elo") or m.get("or_coding")
        bench = scores.get("stem_accuracy_pct") or m.get("terminalbench_hard_percent") or m.get("benchmarks", {}).get("terminalbench_hard_pct")

        pricing = m.get("pricing", {}) if isinstance(m.get("pricing"), dict) else {}
        pin = _first_not_none(pricing.get("prompt_per_m"), m.get("price_in_1m"), default=0.0)
        pout = _first_not_none(pricing.get("completion_per_m"), m.get("price_out_1m"), default=0.0)
        ctx = m.get("context_window") or m.get("context") or m.get("context_tokens") or 128000
        fc_caps = (m.get("fact_check", {}).get("capabilities") or {}) if isinstance(m.get("fact_check"), dict) else {}
        open_w = 1 if (
            m.get("open_weights")
            or fc_caps.get("open_weights")
            or str(m.get("classification", "")).lower() in ("open_weights", "open-source", "open source")
        ) else 0

        cursor.execute(
            """
            INSERT OR REPLACE INTO ai_models (
                id, name, vendor, openrouter_slug, intelligence_index,
                coding_elo, terminalbench_pct, price_in_1m, price_out_1m,
                context_window, open_weights, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                model_id,
                name,
                vendor,
                slug,
                intel,
                float(elo) if elo is not None else None,
                float(bench) if bench is not None else None,
                float(pin) if pin else 0.0,
                float(pout) if pout else 0.0,
                parse_context_window(ctx),
                open_w,
                json.dumps(m, ensure_ascii=False),
            ),
        )
        count += 1

    conn.commit()
    return count


def export_pc_games(conn: sqlite3.Connection, data_root: Path = DATA_DIR) -> int:
    """Ingest PC Games from JSON catalog into SQLite."""
    games_json_path = data_root / "games" / "games.json"
    if not games_json_path.exists():
        print(f"Warning: No PC games JSON found at {games_json_path}")
        return 0

    with open(games_json_path, "r", encoding="utf-8") as f:
        games = json.load(f)

    cursor = conn.cursor()
    cursor.execute("DELETE FROM pc_games;")

    count = 0
    for g in games:
        game_id = g.get("id") or str(g.get("name", "")).lower().replace(" ", "-")
        name = g.get("name", "Unknown")
        genre = g.get("genre", "")
        ownership = g.get("ownership", "wishlist")
        steam_app_id = g.get("steamAppId")
        steam_app_id = int(steam_app_id) if steam_app_id is not None else None
        p_model = g.get("priceModel", "paid")
        price = float(g.get("priceUsd") or 0.0)

        camp = g.get("campaign", {})
        camp_q = float(camp.get("quality", 0.0)) if isinstance(camp, dict) else None

        ai = g.get("ai", {})
        ai_s = float(ai.get("score", 0.0)) if isinstance(ai, dict) else None

        gfx = g.get("graphics", {})
        gfx_s = float(gfx.get("score", 0.0)) if isinstance(gfx, dict) else None

        setting = g.get("setting", "")
        install_gb = float(_first_not_none(g.get("installGB"), g.get("size", {}).get("installGB") if isinstance(g.get("size"), dict) else None, default=0.0))
        gpu_min = float(g.get("gpuMinTier") or 0.0)
        gpu_rec = float(g.get("gpuRecTier") or 0.0)
        note = g.get("compatNote", "")
        fps = g.get("bench", {}).get("playable", {}).get("fps", "")

        cursor.execute(
            """
            INSERT OR REPLACE INTO pc_games (
                id, name, genre, ownership, steam_app_id, price_model, price_usd,
                campaign_quality, ai_score, graphics_score, setting, install_gb,
                gpu_min_tier, gpu_rec_tier, compat_note, playable_fps, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                game_id,
                name,
                genre,
                ownership,
                steam_app_id,
                p_model,
                price,
                camp_q,
                ai_s,
                gfx_s,
                setting,
                install_gb,
                gpu_min,
                gpu_rec,
                note,
                fps,
                json.dumps(g, ensure_ascii=False),
            ),
        )
        count += 1

    conn.commit()
    return count


def export_game_benchmarks(conn: sqlite3.Connection, data_root: Path = DATA_DIR) -> int:
    """Ingest real-world FPS benchmarks from `data/games/benchmarks.csv` into SQLite."""
    csv_path = data_root / "games" / "benchmarks.csv"
    if not csv_path.exists():
        return 0

    cur = conn.cursor()
    cur.execute("DELETE FROM game_benchmarks;")
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cur.execute(
                """
                INSERT INTO game_benchmarks (
                    game_id, cpu_name, gpu_id, resolution, preset,
                    avg_fps, low_1pct_fps, low_01pct_fps, source_url, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    r["game_id"].strip(),
                    r["cpu_name"].strip(),
                    r["gpu_id"].strip(),
                    r["resolution"].strip(),
                    r["preset"].strip(),
                    float(r["avg_fps"]),
                    float(r["low_1pct_fps"]),
                    float(r["low_01pct_fps"]),
                    (r.get("source_url") or "").strip(),
                    (r.get("recorded_at") or "").strip(),
                ),
            )
            count += 1
    conn.commit()
    return count


def export_pc_domain(conn: sqlite3.Connection, data_root: Path = DATA_DIR) -> int:
    """Ingest unified PC parts, GPUs, and CPUs from `data/pc/pc.json` into SQLite."""
    pc_json_path = data_root / "pc" / "pc.json"
    if not pc_json_path.exists():
        print(f"Warning: No PC JSON found at {pc_json_path}")
        return 0

    with open(pc_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cursor = conn.cursor()
    cursor.execute("DELETE FROM pc_components;")
    cursor.execute("DELETE FROM pc_gpus;")
    cursor.execute("DELETE FROM pc_cpus;")

    categories = [
        "cpus", "gpus", "motherboards", "ram", "ssds", "hdds",
        "psus", "monitors", "tvs", "keyboards", "mice", "graphics_tablets",
    ]
    comp_count = 0
    for cat in categories:
        for item in data.get(cat, []):
            cid = item.get("id")
            if not cid:
                continue
            cursor.execute(
                """
                INSERT OR REPLACE INTO pc_components (
                    id, category, name, brand, price_bdt, price_usd, specs_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid,
                    cat,
                    item.get("name", cid),
                    item.get("brand"),
                    float(item.get("price_bdt") or 0.0),
                    float(item.get("price_usd") or 0.0),
                    json.dumps(item, ensure_ascii=False),
                ),
            )
            comp_count += 1

    for gpu in data.get("gpus", []):
        cursor.execute(
            """
            INSERT OR REPLACE INTO pc_gpus (
                id, name, vendor, tier, vram_gb, vram_type, tdp_watts,
                transient_multiplier, gpu_peak_spike_watts, system_peak_watts,
                continuous_system_watts, psu_550w_verdict, target_res,
                price_bdt_used, price_bdt_retail, price_usd, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                gpu.get("id"),
                gpu.get("name"),
                gpu.get("vendor") or gpu.get("brand") or "",
                float(gpu.get("tier") or 0.0),
                float(gpu.get("vram_gb") or 0.0),
                gpu.get("vram_type", ""),
                float(gpu.get("tdp_watts") or 0.0),
                float(gpu.get("transient_multiplier") or 1.35),
                float(gpu.get("gpu_peak_spike_watts") or 0.0),
                float(gpu.get("system_peak_watts") or 0.0),
                float(gpu.get("continuous_system_watts") or 0.0),
                gpu.get("psu_550w_verdict", "pass"),
                gpu.get("target_res", ""),
                float(gpu.get("price_bdt_used") or 0.0),
                float(gpu.get("price_bdt_retail") or gpu.get("price_bdt") or 0.0),
                float(gpu.get("price_usd") or 0.0),
                json.dumps(gpu, ensure_ascii=False),
            ),
        )

    for c in data.get("cpus", []):
        cursor.execute(
            """
            INSERT OR REPLACE INTO pc_cpus (
                id, name, socket, cores, threads, base_clock_ghz, boost_clock_ghz,
                l3_cache_mb, tdp_watts, tier, integrated_gpu, price_bdt, price_usd,
                notes, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                c.get("id"),
                c.get("name"),
                c.get("socket"),
                int(c.get("cores") or 0),
                int(c.get("threads") or 0),
                float(c.get("base_clock_ghz") or 0.0),
                float(c.get("boost_clock_ghz") or 0.0),
                float(c.get("l3_cache_mb") or 0.0),
                float(c.get("tdp_watts") or 0.0),
                float(c.get("tier") or 0.0),
                c.get("integrated_gpu", "None"),
                float(c.get("price_bdt") or 0.0),
                float(c.get("price_usd") or 0.0),
                c.get("notes", ""),
                json.dumps(c, ensure_ascii=False),
            ),
        )

    conn.commit()
    return comp_count


def export_hardware_prices(conn: sqlite3.Connection, data_root: Path = DATA_DIR) -> int:
    """Populate historical/reference GPU price snapshots from `data/pc/pc.json`."""
    pc_path = data_root / "pc" / "pc.json"
    if not pc_path.exists():
        return 0
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = json.loads(pc_path.read_text(encoding="utf-8"))
    cur = conn.cursor()
    cur.execute("DELETE FROM hardware_prices;")
    rows = 0
    for gpu in data.get("gpus", []):
        gid = gpu.get("id")
        if not gid:
            continue
        if gpu.get("price_bdt_retail"):
            cur.execute(
                "INSERT INTO hardware_prices (gpu_id, market, condition, currency, price, source_name, source_url, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (gid, "BD", "new", "BDT", float(gpu["price_bdt_retail"]), "BD Retail Baseline", "", now),
            )
            rows += 1
        if gpu.get("price_bdt_used"):
            cur.execute(
                "INSERT INTO hardware_prices (gpu_id, market, condition, currency, price, source_name, source_url, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (gid, "BD", "used", "BDT", float(gpu["price_bdt_used"]), "BD Used Baseline", "", now),
            )
            rows += 1
        if gpu.get("price_usd"):
            cur.execute(
                "INSERT INTO hardware_prices (gpu_id, market, condition, currency, price, source_name, source_url, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (gid, "US", "reference", "USD", float(gpu["price_usd"]), "US Reference Baseline", "", now),
            )
            rows += 1
    conn.commit()
    return rows


def export_media(conn: sqlite3.Connection, data_root: Path = DATA_DIR) -> int:
    """Ingest unified Media & Adaptations catalog from JSON into SQLite."""
    media_json_path = data_root / "media" / "media_catalog.json"
    if not media_json_path.exists():
        return 0

    with open(media_json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    cursor = conn.cursor()
    cursor.execute("DELETE FROM media_catalog;")

    count = 0
    for idx, item in enumerate(items):
        name = str(item.get("name") or f"media-{idx}").strip()
        slug = str(item.get("id") or "").strip() or (re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or f"media-{idx}")
        media_type = str(item.get("media_type") or "comic").strip()
        franchise_id = str(item.get("franchise_id") or "").strip()
        link = str(item.get("link") or "")
        anime = str(item.get("anime") or "**None**")
        live_action = str(item.get("live_action") or "**None**")
        relations = item.get("relations") if isinstance(item.get("relations"), list) else []
        poster_url = str(item.get("poster_url") or "")
        cursor.execute(
            """
            INSERT OR REPLACE INTO media_catalog (
                id, name, alt, media_type, tier, sub_format, nsfw, watchlist_status,
                parent_id, franchise_id, franchise_title, link, origin, anime, live_action,
                poster_url, description, release_year, added_at, updated_at,
                has_direct_link, has_anime, has_live_action, has_poster,
                relations_json, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                name,
                str(item.get("alt", "")),
                media_type,
                str(item.get("tier") or ""),
                str(item.get("sub_format") or ""),
                1 if item.get("nsfw") else 0,
                str(item.get("watchlist_status") or ""),
                str(item.get("parent_id") or ""),
                franchise_id,
                str(item.get("franchise_title") or ""),
                link,
                str(item.get("origin", "")),
                anime,
                live_action,
                poster_url,
                str(item.get("description") or ""),
                int(item["release_year"]) if isinstance(item.get("release_year"), int) else None,
                str(item.get("added_at") or ""),
                str(item.get("updated_at") or ""),
                1 if ("comix.to/title/" in link or (link.startswith("https://") and not link.startswith("https://comix.to/browser"))) else 0,
                0 if anime.startswith("**None**") else 1,
                0 if live_action.startswith("**None**") else 1,
                1 if poster_url else 0,
                json.dumps(relations, ensure_ascii=False),
                json.dumps(item, ensure_ascii=False),
            ),
        )
        count += 1

    conn.commit()
    return count


def export_books(conn: sqlite3.Connection, data_root: Path = DATA_DIR) -> int:
    """Ingest Book collection catalog from JSON into SQLite."""
    book_json_path = data_root / "book" / "books.json"
    if not book_json_path.exists():
        return 0

    with open(book_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("books", data.get("records", [])) if isinstance(data, dict) else data
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books;")

    count = 0
    for idx, b in enumerate(items):
        bid = str(b.get("id") or f"book-{idx}").strip()
        cursor.execute(
            """
            INSERT OR REPLACE INTO books (
                id, title, author, subject, format, ownership_status, reading_status,
                rating, pages, notes, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bid,
                str(b.get("title") or "Untitled"),
                str(b.get("author") or ""),
                str(b.get("subject") or ""),
                str(b.get("format") or "paperback"),
                str(b.get("ownership_status") or "owned"),
                str(b.get("reading_status") or "queued"),
                float(b.get("rating") or 0.0),
                int(b.get("pages") or 0),
                str(b.get("notes") or ""),
                json.dumps(b, ensure_ascii=False),
            ),
        )
        count += 1

    conn.commit()
    return count


def export_phones(conn: sqlite3.Connection, data_root: Path = DATA_DIR) -> int:
    """Ingest Phone & Mobile specs + supported games/apps from JSON into SQLite."""
    phone_json_path = data_root / "phone" / "phones.json"
    if not phone_json_path.exists():
        return 0

    with open(phone_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("phones", data.get("records", [])) if isinstance(data, dict) else data
    cursor = conn.cursor()
    cursor.execute("DELETE FROM phones;")

    count = 0
    for idx, p in enumerate(items):
        pid = str(p.get("id") or f"phone-{idx}").strip()
        games = p.get("supported_games") if isinstance(p.get("supported_games"), list) else []
        apps = p.get("supported_apps") if isinstance(p.get("supported_apps"), list) else []
        cursor.execute(
            """
            INSERT OR REPLACE INTO phones (
                id, name, brand, soc, gpu, ram_gb, storage_gb, display_hz, display_type,
                battery_mah, charging_watts, os, price_bdt, price_usd,
                supported_games_count, supported_apps_count, supported_games_json, supported_apps_json,
                notes, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pid,
                str(p.get("name") or pid),
                str(p.get("brand") or ""),
                str(p.get("soc") or ""),
                str(p.get("gpu") or ""),
                float(p.get("ram_gb") or 0.0),
                float(p.get("storage_gb") or 0.0),
                float(p.get("display_hz") or 60.0),
                str(p.get("display_type") or ""),
                int(p.get("battery_mah") or 0),
                float(p.get("charging_watts") or 0.0),
                str(p.get("os") or ""),
                float(p.get("price_bdt") or 0.0),
                float(p.get("price_usd") or 0.0),
                len(games),
                len(apps),
                json.dumps(games, ensure_ascii=False),
                json.dumps(apps, ensure_ascii=False),
                str(p.get("notes") or ""),
                json.dumps(p, ensure_ascii=False),
            ),
        )
        count += 1

    conn.commit()
    return count


def export_github_repos(conn: sqlite3.Connection, source_path: Path | None = None, data_root: Path = DATA_DIR) -> int:
    """Ingest sanitized GitHub repository catalog from JSON into SQLite."""
    gh_json_path = source_path or (data_root / "github" / "repos_public.json")
    if not gh_json_path.exists():
        return 0

    with open(gh_json_path, "r", encoding="utf-8") as f:
        repos = json.load(f)

    cursor = conn.cursor()
    cursor.execute("DELETE FROM github_repos;")

    count = 0
    for idx, r in enumerate(repos):
        name = str(r.get("name") or f"repo-{idx}").strip()
        full_name = str(r.get("full_name") or name).strip()
        repo_id = re.sub(r"[^a-z0-9._-]+", "-", name.lower()).strip("-") or f"repo-{idx}"
        parent = r.get("parent") if isinstance(r.get("parent"), dict) else {}
        comp = r.get("upstream_comparison") if isinstance(r.get("upstream_comparison"), dict) else {}
        rel = r.get("latest_release") if isinstance(r.get("latest_release"), dict) else {}
        tag = r.get("latest_tag") if isinstance(r.get("latest_tag"), dict) else {}
        run = r.get("latest_run") if isinstance(r.get("latest_run"), dict) else {}

        latest_rel_tag = str(rel.get("tag_name") or tag.get("name") or "")
        cursor.execute(
            """
            INSERT OR REPLACE INTO github_repos (
                id, name, full_name, is_fork, is_private, default_branch,
                pushed_at, updated_at, description, parent_full_name,
                ahead_by, behind_by, latest_release_tag, ci_status, ci_conclusion,
                unbuilt_commits_count, unreleased_commits_count, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                repo_id,
                name,
                full_name,
                1 if r.get("is_fork") else 0,
                1 if r.get("is_private") else 0,
                str(r.get("default_branch") or "main"),
                str(r.get("pushed_at") or ""),
                str(r.get("updated_at") or ""),
                str(r.get("description") or ""),
                str(parent.get("full_name") or ""),
                int(comp.get("ahead_by") or 0),
                int(comp.get("behind_by") or 0),
                latest_rel_tag,
                str(run.get("status") or ""),
                str(run.get("conclusion") or ""),
                int(r.get("unbuilt_commits_count") or 0),
                int(r.get("unreleased_commits_count") or 0),
                json.dumps(r, ensure_ascii=False),
            ),
        )
        count += 1

    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Verification & Compilation Pipelines
# ---------------------------------------------------------------------------

def verify_database(conn: sqlite3.Connection) -> None:
    """Run integrity queries across all consolidated SQLite tables."""
    cursor = conn.cursor()
    print("\n" + "=" * 64)
    print(" SQLITE DATABASE INTEGRITY VERIFICATION")
    print("=" * 64)

    cursor.execute("SELECT COUNT(*), AVG(intelligence_index) FROM ai_models;")
    ai_count, avg_intel = cursor.fetchone()
    print(f"  [OK] ai_models:       {ai_count} records (Avg Intelligence: {(avg_intel or 0.0):.2f})")

    cursor.execute("SELECT COUNT(*), AVG(price_usd) FROM pc_games;")
    game_count, avg_price = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM game_benchmarks;")
    bench_count = cursor.fetchone()[0]
    print(f"  [OK] pc_games:        {game_count} records (Avg Price: ${(avg_price or 0.0):.2f}, Benchmarks: {bench_count})")

    cursor.execute("SELECT COUNT(*) FROM pc_components;")
    pc_comp_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*), AVG(tdp_watts) FROM pc_gpus;")
    gpu_count, avg_tdp = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM pc_cpus;")
    cpu_count = cursor.fetchone()[0]
    print(f"  [OK] pc:              {pc_comp_count} parts ({gpu_count} GPUs Avg TDP: {(avg_tdp or 0.0):.1f}W, {cpu_count} CPUs)")

    cursor.execute("SELECT COUNT(*), SUM(has_direct_link) FROM media_catalog;")
    media_count, direct_cnt = cursor.fetchone()
    print(f"  [OK] media_catalog:   {media_count} records (Direct links: {direct_cnt or 0})")

    cursor.execute("SELECT COUNT(*) FROM books;")
    book_count = cursor.fetchone()[0]
    print(f"  [OK] books:           {book_count} records")

    cursor.execute("SELECT COUNT(*) FROM phones;")
    phone_count = cursor.fetchone()[0]
    print(f"  [OK] phones:          {phone_count} records")

    cursor.execute("SELECT COUNT(*), SUM(is_fork), SUM(CASE WHEN ci_conclusion='success' THEN 1 ELSE 0 END) FROM github_repos;")
    gh_count, gh_forks, gh_pass = cursor.fetchone()
    print(f"  [OK] github_repos:    {gh_count} records (Forks: {gh_forks or 0}, CI Passing: {gh_pass or 0})")

    print("=" * 64 + "\n")


def compile_database(target_path: Path = SQLITE_PATH) -> None:
    """Compile all registered domains atomically into consolidated `data/database.sqlite`."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.with_suffix(".sqlite.tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    conn = sqlite3.connect(tmp_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA journal_mode=DELETE;")
        create_schema(conn)
        ai_cnt = export_ai_models(conn)
        game_cnt = export_pc_games(conn)
        bench_cnt = export_game_benchmarks(conn)
        pc_cnt = export_pc_domain(conn)
        export_hardware_prices(conn)
        media_cnt = export_media(conn)
        book_cnt = export_books(conn)
        phone_cnt = export_phones(conn)
        gh_cnt = export_github_repos(conn)
        verify_database(conn)
    except Exception:
        conn.close()
        if tmp_path.exists():
            tmp_path.unlink()
        raise
    else:
        conn.close()
        os.replace(tmp_path, target_path)
        print(f"Compiled consolidated SQLite database at: {target_path}")
        print(f"  • PC Domain parts:      {pc_cnt}")
        print(f"  • PC Games & Benches:   {game_cnt} games / {bench_cnt} benchmark rows")
        print(f"  • AI Models ingested:   {ai_cnt}")
        print(f"  • Media entries:        {media_cnt}")
        print(f"  • Books ingested:       {book_cnt}")
        print(f"  • Phones ingested:      {phone_cnt}")
        print(f"  • GitHub repos:         {gh_cnt}")


def _file_sha256(path: Path) -> str:
    """Compute SHA-256 hex digest of a file for drift telemetry."""
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_meta_table(
    conn: sqlite3.Connection,
    domain: str,
    schema_version: str,
    record_count: int,
    source_path: Path,
) -> None:
    """Create and populate the standardized _meta freshness & drift table."""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS _meta (
            domain TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            content_sha256 TEXT NOT NULL,
            source_file TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    updated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if source_path.exists():
        try:
            rel_src = str(source_path.relative_to(ROOT_DIR)).replace("\\", "/")
        except ValueError:
            rel_src = str(source_path).replace("\\", "/")
    else:
        rel_src = str(source_path).replace("\\", "/")
    cur.execute(
        """
        INSERT OR REPLACE INTO _meta (
            domain, schema_version, record_count, content_sha256, source_file, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (domain, schema_version, record_count, _file_sha256(source_path), rel_src, updated_at),
    )
    conn.commit()


def _seed_auxiliary_tables(conn: sqlite3.Connection, domain: str, data_root: Path = DATA_DIR) -> None:
    """Populate domain-specific auxiliary tables inside an isolated domain SQLite."""
    if domain == "pc":
        export_hardware_prices(conn, data_root=data_root)
    elif domain == "games":
        export_game_benchmarks(conn, data_root=data_root)


def compile_separated_domains(data_root: Path = DATA_DIR) -> dict[str, int]:
    """Compile each domain into its own strictly isolated atomic SQLite database."""
    counts: dict[str, int] = {}
    domain_specs: list[tuple[str, Path, Path, str, Callable[..., int]]] = [
        ("pc", data_root / "pc" / "pc.sqlite", data_root / "pc" / "pc.json", "2.0.0", export_pc_domain),
        ("games", data_root / "games" / "games.sqlite", data_root / "games" / "games.json", "4.0.0", export_pc_games),
        ("ai", data_root / "ai" / "ai.sqlite", data_root / "ai" / "models_master.json", "2.0.0", export_ai_models),
        ("media", data_root / "media" / "media.sqlite", data_root / "media" / "media_catalog.json", "2.0.0", export_media),
        ("book", data_root / "book" / "book.sqlite", data_root / "book" / "books.json", "2.0.0", export_books),
        ("phone", data_root / "phone" / "phone.sqlite", data_root / "phone" / "phones.json", "2.0.0", export_phones),
        ("github", data_root / "github" / "github.sqlite", data_root / "github" / "repos_public.json", "1.0.0", export_github_repos),
    ]
    for domain, db_path, src_path, schema_ver, exporter in domain_specs:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = db_path.with_suffix(".sqlite.tmp")
        if tmp_path.exists():
            tmp_path.unlink()
        conn = sqlite3.connect(tmp_path)
        try:
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute("PRAGMA journal_mode=DELETE;")
            create_extended_domain_tables(conn, domain)
            cnt = exporter(conn, data_root=data_root)
            _seed_auxiliary_tables(conn, domain, data_root=data_root)
            _write_meta_table(conn, domain, schema_ver, cnt, src_path)
        except Exception:
            conn.close()
            if tmp_path.exists():
                tmp_path.unlink()
            raise
        else:
            conn.close()
            os.replace(tmp_path, db_path)
            counts[domain] = cnt
    return counts


def init_domain_scaffold(name: str, data_root: Path = DATA_DIR) -> Path:
    """Scaffold a new isolated domain folder, starter JSON, schema, and registry entry."""
    slug = re.sub(r"[^a-z0-9_]+", "_", name.strip().lower()).strip("_")
    if not slug:
        raise ValueError("Domain name must contain at least one alphanumeric character.")
    domain_dir = data_root / slug
    domain_dir.mkdir(parents=True, exist_ok=True)

    json_file = domain_dir / f"{slug}.json"
    if not json_file.exists():
        json_file.write_text(
            json.dumps({"metadata": {"domain": slug, "version": "1.0.0"}, "records": []}, indent=2) + "\n",
            encoding="utf-8",
        )

    schema_file = domain_dir / "schema.json"
    if not schema_file.exists():
        schema_file.write_text(
            json.dumps(
                {
                    "domain": slug,
                    "schema_version": "1.0.0",
                    "records_key": "records",
                    "required_fields": ["id", "name"],
                    "field_types": {"id": "str", "name": "str"},
                    "ranges": {},
                    "unique_key": "id",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    reg_path = data_root / "registry.json"
    if reg_path.exists():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
    else:
        reg = {"version": "2.0.0", "groups": {}, "domains": {}, "cross_domain_views": []}

    label = slug.replace("_", " ").title()
    next_order = len(reg.get("domains", {})) + 1
    reg.setdefault("domains", {})[slug] = {
        "display_name": label,
        "short_label": label,
        "unit_label": "records",
        "aliases": [slug],
        "group": "general",
        "tab_order": next_order,
        "show_in_portal": False,
        "web_path": f"{slug}/index.html",
        "api_path": f"/api/{slug}",
        "title": label,
        "source_json": f"data/{slug}/{slug}.json",
        "records_key": "records",
        "schema_file": f"data/{slug}/schema.json",
        "sqlite_file": f"data/{slug}/{slug}.sqlite",
        "primary_table": f"{slug}_records",
        "max_age_days": 30,
        "scraper_tiers": ["tier0_api", "tier1_httpx"],
    }
    reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    return domain_dir


def main() -> None:
    """CLI Entry point."""
    parser = argparse.ArgumentParser(description="Compile multi-domain SQLite databases")
    parser.add_argument("--verify", action="store_true", help="Verify existing database")
    parser.add_argument("--init-domain", metavar="NAME", help="Scaffold a new domain folder, schema, and registry entry")
    args = parser.parse_args()

    if args.init_domain:
        created = init_domain_scaffold(args.init_domain)
        print(f"Scaffolded new domain at: {created}")
        print(f"  • Updated registry: {REGISTRY_PATH}")
        return

    if args.verify:
        if not SQLITE_PATH.exists():
            print(f"Error: {SQLITE_PATH} does not exist.")
            sys.exit(1)
        conn = sqlite3.connect(SQLITE_PATH)
        try:
            verify_database(conn)
        finally:
            conn.close()
    else:
        compile_database()
        dom_counts = compile_separated_domains()
        print("Compiled strictly isolated domain SQLite databases:")
        for d, cnt in dom_counts.items():
            print(f"  • data/{d}/{d}.sqlite ({cnt} records + _meta)")


if __name__ == "__main__":
    main()
