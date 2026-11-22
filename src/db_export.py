#!/usr/bin/env python3
"""Database Manager — SQLite Consolidated Export Pipeline.

Compiles disparate JSON/CSV datasets across AI models, PC games, and hardware
specifications into a single high-performance SQLite database:
`data/database.sqlite`.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SQLITE_PATH = DATA_DIR / "database.sqlite"


def create_schema(conn: sqlite3.Connection) -> None:
    """Create normalized relational tables and indexes."""
    cursor = conn.cursor()

    # 1. AI Models Table
    cursor.execute("""
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
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_vendor ON ai_models(vendor);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_intel ON ai_models(intelligence_index DESC);")

    # 2. PC Games Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pc_games (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        genre TEXT,
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
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_genre ON pc_games(genre);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_price ON pc_games(price_usd);")

    # 3. Hardware GPUs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hardware_gpus (
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
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gpu_tier ON hardware_gpus(tier);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gpu_psu ON hardware_gpus(psu_550w_verdict);")

    conn.commit()


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


def export_ai_models(conn: sqlite3.Connection) -> int:
    """Ingest AI models from JSON catalog into SQLite."""
    ai_json_path = DATA_DIR / "ai" / "models_master.json"
    if not ai_json_path.exists():
        ai_json_path = DATA_DIR / "ai" / "model-comparison.json"
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
        open_w = 1 if (m.get("open_weights") or m.get("classification") == "open_weights") else 0

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


def export_pc_games(conn: sqlite3.Connection) -> int:
    """Ingest PC Games from JSON catalog into SQLite."""
    games_json_path = DATA_DIR / "games" / "games.json"
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
                id, name, genre, price_model, price_usd, campaign_quality,
                ai_score, graphics_score, setting, install_gb, gpu_min_tier,
                gpu_rec_tier, compat_note, playable_fps, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                game_id,
                name,
                genre,
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


def export_hardware_gpus(conn: sqlite3.Connection) -> int:
    """Ingest Hardware GPUs from JSON catalog into SQLite."""
    hw_json_path = DATA_DIR / "hardware" / "hardware_specs.json"
    if not hw_json_path.exists():
        print(f"Warning: No hardware JSON found at {hw_json_path}")
        return 0

    with open(hw_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    gpus = data.get("gpus", [])
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hardware_gpus;")

    count = 0
    for gpu in gpus:
        cursor.execute(
            """
            INSERT OR REPLACE INTO hardware_gpus (
                id, name, vendor, tier, vram_gb, vram_type, tdp_watts,
                transient_multiplier, gpu_peak_spike_watts, system_peak_watts,
                continuous_system_watts, psu_550w_verdict, target_res,
                price_bdt_used, price_bdt_retail, price_usd, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                gpu.get("id"),
                gpu.get("name"),
                gpu.get("vendor"),
                float(gpu.get("tier", 0)),
                float(gpu.get("vram_gb", 0)),
                gpu.get("vram_type", ""),
                float(gpu.get("tdp_watts", 0)),
                float(gpu.get("transient_multiplier", 1.35)),
                float(gpu.get("gpu_peak_spike_watts", 0)),
                float(gpu.get("system_peak_watts", 0)),
                float(gpu.get("continuous_system_watts", 0)),
                gpu.get("psu_550w_verdict", "pass"),
                gpu.get("target_res", ""),
                float(gpu.get("price_bdt_used", 0)),
                float(gpu.get("price_bdt_retail", 0)),
                float(gpu.get("price_usd", 0)),
                json.dumps(gpu, ensure_ascii=False),
            ),
        )
        count += 1

    conn.commit()
    return count


def verify_database(conn: sqlite3.Connection) -> None:
    """Run test queries across all tables and print results."""
    cursor = conn.cursor()
    print("\n" + "=" * 60)
    print(" 🔍 SQLITE DATABASE INTEGRITY VERIFICATION")
    print("=" * 60)

    # Count AI
    cursor.execute("SELECT COUNT(*), AVG(intelligence_index) FROM ai_models;")
    ai_count, avg_intel = cursor.fetchone()
    print(f"  ✓ ai_models:     {ai_count} records (Avg Intelligence: {(avg_intel or 0.0):.2f})")

    # Count Games
    cursor.execute("SELECT COUNT(*), AVG(price_usd) FROM pc_games;")
    game_count, avg_price = cursor.fetchone()
    print(f"  ✓ pc_games:      {game_count} records (Avg Price: ${(avg_price or 0.0):.2f})")

    # Count GPUs
    cursor.execute("SELECT COUNT(*), AVG(tdp_watts) FROM hardware_gpus;")
    gpu_count, avg_tdp = cursor.fetchone()
    print(f"  ✓ hardware_gpus: {gpu_count} records (Avg TDP: {(avg_tdp or 0.0):.1f}W)")

    print("=" * 60 + "\n")


def compile_database(target_path: Path = SQLITE_PATH) -> None:
    """Run full compilation pipeline atomically via temp file swap."""
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
        gpu_cnt = export_hardware_gpus(conn)
        verify_database(conn)
    except Exception:
        conn.close()
        if tmp_path.exists():
            tmp_path.unlink()
        raise
    else:
        conn.close()
        os.replace(tmp_path, target_path)
        print(f"Compiled SQLite database at: {target_path}")
        print(f"  • AI Models ingested:   {ai_cnt}")
        print(f"  • PC Games ingested:    {game_cnt}")
        print(f"  • Hardware GPUs ingested:{gpu_cnt}")


def main() -> None:
    """CLI Entry point."""
    parser = argparse.ArgumentParser(description="Compile multi-domain SQLite database")
    parser.add_argument("--verify", action="store_true", help="Verify existing database")
    args = parser.parse_args()

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


if __name__ == "__main__":
    main()
