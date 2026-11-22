#!/usr/bin/env python3
"""Database Manager — SQLite Consolidated Export Pipeline.

Compiles disparate JSON/CSV datasets across AI models, PC games, and hardware
specifications into a single high-performance SQLite database:
`data/database.sqlite`.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
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

    # 4. Manga Catalog Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS manga_catalog (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        alt TEXT,
        link TEXT,
        origin TEXT,
        anime TEXT,
        live_action TEXT,
        has_direct_link INTEGER,
        has_anime INTEGER,
        has_live_action INTEGER,
        raw_json TEXT
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manga_origin ON manga_catalog(origin);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manga_name ON manga_catalog(name);")

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


def export_cpus(conn: sqlite3.Connection) -> int:
    """Ingest Desktop CPUs from JSON catalog into SQLite."""
    cpus_json_path = DATA_DIR / "cpus" / "cpus.json"
    if not cpus_json_path.exists():
        return 0

    with open(cpus_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cpus = data.get("cpus", data.get("records", []))
    cursor = conn.cursor()
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
    cursor.execute("DELETE FROM pc_cpus;")

    count = 0
    for c in cpus:
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
                int(c.get("cores", 0)),
                int(c.get("threads", 0)),
                float(c.get("base_clock_ghz", 0)),
                float(c.get("boost_clock_ghz", 0)),
                float(c.get("l3_cache_mb", 0)),
                float(c.get("tdp_watts", 0)),
                float(c.get("tier", 0)),
                c.get("integrated_gpu", "None"),
                float(c.get("price_bdt", 0)),
                float(c.get("price_usd", 0)),
                c.get("notes", ""),
                json.dumps(c, ensure_ascii=False),
            ),
        )
        count += 1

    conn.commit()
    return count


def export_pc_components(conn: sqlite3.Connection) -> int:
    """Ingest full PC & peripherals components from JSON catalog into SQLite."""
    comp_json_path = DATA_DIR / "pc_components" / "components.json"
    if not comp_json_path.exists():
        return 0

    with open(comp_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

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
    cursor.execute("DELETE FROM pc_components;")

    count = 0
    categories = [
        "cpus", "gpus", "motherboards", "ram", "ssds", "hdds",
        "monitors", "tvs", "keyboards", "mice", "graphics_tablets"
    ]
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
                    float(item.get("price_bdt", 0)),
                    float(item.get("price_usd", 0)),
                    json.dumps(item, ensure_ascii=False),
                ),
            )
            count += 1

    conn.commit()
    return count


def export_manga(conn: sqlite3.Connection) -> int:
    """Ingest Manga, Manhwa & Adaptations catalog from JSON into SQLite."""
    manga_json_path = DATA_DIR / "manga" / "manga_catalog.json"
    if not manga_json_path.exists():
        return 0

    with open(manga_json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    cursor = conn.cursor()
    cursor.execute("DELETE FROM manga_catalog;")

    count = 0
    for idx, item in enumerate(items):
        name = str(item.get("name") or f"manga-{idx}").strip()
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or f"manga-{idx}"
        link = str(item.get("link", ""))
        anime = str(item.get("anime", "**None**"))
        live_action = str(item.get("live_action", "**None**"))
        cursor.execute(
            """
            INSERT OR REPLACE INTO manga_catalog (
                id, name, alt, link, origin, anime, live_action,
                has_direct_link, has_anime, has_live_action, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                name,
                str(item.get("alt", "")),
                link,
                str(item.get("origin", "")),
                anime,
                live_action,
                1 if "comix.to/title/" in link else 0,
                0 if anime.startswith("**None**") else 1,
                0 if live_action.startswith("**None**") else 1,
                json.dumps(item, ensure_ascii=False),
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

    # Count Manga
    cursor.execute("SELECT COUNT(*), SUM(has_direct_link) FROM manga_catalog;")
    manga_count, direct_cnt = cursor.fetchone()
    print(f"  ✓ manga_catalog: {manga_count} records (Direct links: {direct_cnt or 0})")

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
        cpu_cnt = export_cpus(conn)
        comp_cnt = export_pc_components(conn)
        manga_cnt = export_manga(conn)
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
        print(f"  • Desktop CPUs ingested:{cpu_cnt}")
        print(f"  • PC Components ingested:{comp_cnt}")
        print(f"  • Manga titles ingested:{manga_cnt}")




REGISTRY_PATH = DATA_DIR / "registry.json"


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
    rel_src = str(source_path.relative_to(ROOT_DIR)).replace("\\", "/") if source_path.exists() else str(source_path)
    cur.execute(
        """
        INSERT OR REPLACE INTO _meta (
            domain, schema_version, record_count, content_sha256, source_file, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (domain, schema_version, record_count, _file_sha256(source_path), rel_src, updated_at),
    )
    conn.commit()


def create_extended_domain_tables(conn: sqlite3.Connection, domain: str) -> None:
    """Create domain-specific auxiliary tables for benchmarks and price history."""
    cur = conn.cursor()
    if domain == "games":
        cur.execute(
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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_bench_game_gpu ON game_benchmarks(game_id, gpu_id);")
    elif domain == "hardware":
        cur.execute(
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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prices_gpu_market ON hardware_prices(gpu_id, market);")
    conn.commit()


def _seed_auxiliary_tables(conn: sqlite3.Connection, domain: str) -> None:
    """Populate initial benchmark / price snapshot rows from master JSON."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cur = conn.cursor()
    if domain == "hardware":
        hw_path = DATA_DIR / "hardware" / "hardware_specs.json"
        if hw_path.exists():
            data = json.loads(hw_path.read_text(encoding="utf-8"))
            cur.execute("DELETE FROM hardware_prices;")
            for gpu in data.get("gpus", []):
                gid = gpu.get("id")
                if not gid:
                    continue
                if gpu.get("price_bdt_retail"):
                    cur.execute(
                        "INSERT INTO hardware_prices (gpu_id, market, condition, currency, price, source_name, source_url, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (gid, "BD", "new", "BDT", float(gpu["price_bdt_retail"]), "BD Retail Baseline", "", now),
                    )
                if gpu.get("price_bdt_used"):
                    cur.execute(
                        "INSERT INTO hardware_prices (gpu_id, market, condition, currency, price, source_name, source_url, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (gid, "BD", "used", "BDT", float(gpu["price_bdt_used"]), "BD Used Baseline", "", now),
                    )
                if gpu.get("price_usd"):
                    cur.execute(
                        "INSERT INTO hardware_prices (gpu_id, market, condition, currency, price, source_name, source_url, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (gid, "US", "reference", "USD", float(gpu["price_usd"]), "US Reference Baseline", "", now),
                    )
            conn.commit()


def compile_separated_domains(data_root: Path = DATA_DIR) -> dict[str, int]:
    """Compile each domain into its own isolated atomic SQLite database."""
    counts: dict[str, int] = {}
    domain_specs = [
        ("ai", data_root / "ai" / "ai.sqlite", data_root / "ai" / "models_master.json", "2.0.0", export_ai_models),
        ("games", data_root / "games" / "games.sqlite", data_root / "games" / "games.json", "3.0.0", export_pc_games),
        ("hardware", data_root / "hardware" / "hardware.sqlite", data_root / "hardware" / "hardware_specs.json", "1.0.0", export_hardware_gpus),
        ("cpus", data_root / "cpus" / "cpus.sqlite", data_root / "cpus" / "cpus.json", "1.0.0", export_cpus),
        ("pc_components", data_root / "pc_components" / "pc_components.sqlite", data_root / "pc_components" / "components.json", "1.0.0", export_pc_components),
        ("manga", data_root / "manga" / "manga.sqlite", data_root / "manga" / "manga_catalog.json", "1.0.0", export_manga),
    ]
    for domain, db_path, src_path, schema_ver, exporter in domain_specs:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = db_path.with_suffix(".sqlite.tmp")
        if tmp_path.exists():
            tmp_path.unlink()
        conn = sqlite3.connect(tmp_path)
        try:
            conn.execute("PRAGMA foreign_keys=ON;")
            create_schema(conn)
            create_extended_domain_tables(conn, domain)
            cnt = exporter(conn)
            _seed_auxiliary_tables(conn, domain)
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
        reg = {"version": "1.0.0", "domains": {}, "cross_domain_views": []}

    reg.setdefault("domains", {})[slug] = {
        "title": slug.replace("_", " ").title(),
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
        print("Compiled separated domain SQLite databases:")
        for d, cnt in dom_counts.items():
            print(f"  • data/{d}/{d}.sqlite ({cnt} records + _meta)")


if __name__ == "__main__":
    main()
