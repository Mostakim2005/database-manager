#!/usr/bin/env python3
"""Database Manager — SQLite ATTACH Cross-Domain Query Hub.

Attaches separated per-domain SQLite databases (ai.sqlite, games.sqlite,
hardware.sqlite, plus any future registered domains) into one in-memory
federated SQLite session and exposes logical cross-domain queries.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
REGISTRY_PATH = DATA_DIR / "registry.json"


def load_registry(registry_path: Path = REGISTRY_PATH) -> dict[str, Any]:
    """Load the central multi-domain registry manifest."""
    if not registry_path.exists():
        return {"version": "1.0.0", "domains": {}, "cross_domain_views": []}
    return json.loads(registry_path.read_text(encoding="utf-8"))


def open_federated_connection(root_dir: Path = ROOT_DIR) -> sqlite3.Connection:
    """Open an in-memory SQLite hub with all compiled domain databases ATTACHed."""
    reg = load_registry(root_dir / "data" / "registry.json")
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    attached: set[str] = set()
    for domain, cfg in reg.get("domains", {}).items():
        sqlite_rel = cfg.get("sqlite_file", "")
        db_path = root_dir / sqlite_rel
        if db_path.exists() and domain.isidentifier():
            conn.execute(f"ATTACH DATABASE ? AS {domain}", (str(db_path),))
            attached.add(domain)

    # Logical cross-domain view 1: PC Games x Hardware GPUs
    if "games" in attached and "hardware" in attached:
        conn.execute(
            """
            CREATE TEMP VIEW v_games_by_gpu AS
            SELECT
                h.id AS gpu_id,
                h.name AS gpu_name,
                h.tier AS gpu_tier,
                h.vram_gb,
                h.tdp_watts,
                h.system_peak_watts,
                h.psu_550w_verdict,
                h.price_bdt_used,
                h.price_bdt_retail,
                h.price_usd,
                g.id AS game_id,
                g.name AS game_name,
                g.genre,
                g.gpu_min_tier,
                g.gpu_rec_tier,
                g.install_gb,
                g.playable_fps,
                CASE
                    WHEN h.tier >= g.gpu_rec_tier THEN 'recommended'
                    WHEN h.tier >= g.gpu_min_tier THEN 'playable'
                    ELSE 'below_min'
                END AS tier_match
            FROM games.pc_games g
            CROSS JOIN hardware.hardware_gpus h;
            """
        )

    # Logical cross-domain view 2: Open-Weights AI Models x Hardware GPU VRAM
    if "ai" in attached and "hardware" in attached:
        conn.execute(
            """
            CREATE TEMP VIEW v_local_ai_vram_fit AS
            SELECT
                h.id AS gpu_id,
                h.name AS gpu_name,
                h.vram_gb,
                h.psu_550w_verdict,
                a.id AS model_id,
                a.name AS model_name,
                a.vendor,
                a.intelligence_index,
                a.open_weights,
                CASE
                    WHEN h.vram_gb >= 16 THEN 'Fits 14B-32B Q4 locally'
                    WHEN h.vram_gb >= 12 THEN 'Fits 7B-14B Q4 locally'
                    WHEN h.vram_gb >= 8 THEN 'Fits 7B-8B Q4 locally'
                    ELSE 'API / Cloud Recommended (<8GB VRAM)'
                END AS local_fit_tier
            FROM ai.ai_models a
            CROSS JOIN hardware.hardware_gpus h
            WHERE a.open_weights = 1;
            """
        )

    # Logical cross-domain view 3: CPUs x GPUs platform power & upgrade combos
    if "cpus" in attached and "hardware" in attached:
        conn.execute(
            """
            CREATE TEMP VIEW v_cpu_gpu_combos AS
            SELECT
                c.id AS cpu_id,
                c.name AS cpu_name,
                c.socket,
                c.cores,
                c.threads,
                c.l3_cache_mb,
                c.tdp_watts AS cpu_tdp,
                h.id AS gpu_id,
                h.name AS gpu_name,
                h.tier AS gpu_tier,
                h.tdp_watts AS gpu_tdp,
                (c.tdp_watts + h.tdp_watts + 35) AS estimated_continuous_draw_watts,
                ROUND(c.tdp_watts + (h.tdp_watts * h.transient_multiplier) + 35) AS estimated_peak_spike_watts,
                CASE
                    WHEN (c.tdp_watts + (h.tdp_watts * h.transient_multiplier) + 35) > 550.0 THEN 'fail'
                    WHEN (c.tdp_watts + h.tdp_watts + 35) > 412.5 THEN 'warn'
                    ELSE 'pass'
                END AS psu_550w_combo_status,
                c.price_bdt AS cpu_price_bdt,
                h.price_bdt_retail AS gpu_price_bdt,
                (c.price_bdt + h.price_bdt_retail) AS total_upgrade_cost_bdt
            FROM cpus.pc_cpus c
            CROSS JOIN hardware.hardware_gpus h;
            """
        )

    return conn


def query_domain_health(root_dir: Path = ROOT_DIR) -> list[dict[str, Any]]:
    """Return freshness, record count, and SHA-256 status for every registered domain."""
    reg = load_registry(root_dir / "data" / "registry.json")
    now = datetime.datetime.now(datetime.timezone.utc)
    results: list[dict[str, Any]] = []

    for domain, cfg in reg.get("domains", {}).items():
        db_path = root_dir / cfg.get("sqlite_file", "")
        max_age = int(cfg.get("max_age_days", 30))
        entry: dict[str, Any] = {
            "domain": domain,
            "title": cfg.get("title", domain),
            "sqlite_file": cfg.get("sqlite_file"),
            "compiled": db_path.exists(),
            "max_age_days": max_age,
            "scraper_tiers": cfg.get("scraper_tiers", []),
        }
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                row = conn.execute("SELECT * FROM _meta WHERE domain = ?", (domain,)).fetchone()
                if row:
                    updated_str = row["updated_at"]
                    updated_dt = datetime.datetime.strptime(updated_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                        tzinfo=datetime.timezone.utc
                    )
                    age_days = max(0, (now - updated_dt).days)
                    entry.update(
                        {
                            "schema_version": row["schema_version"],
                            "record_count": row["record_count"],
                            "content_sha256": row["content_sha256"],
                            "updated_at": updated_str,
                            "age_days": age_days,
                            "is_stale": age_days > max_age,
                        }
                    )
            except sqlite3.OperationalError:
                entry["is_stale"] = True
            finally:
                conn.close()
        results.append(entry)
    return results


def query_games_by_gpu(gpu_id: str = "rx-6600", max_psu_watts: int = 550, root_dir: Path = ROOT_DIR) -> dict[str, Any]:
    """Query cross-domain v_games_by_gpu for a candidate GPU and PSU ceiling."""
    conn = open_federated_connection(root_dir)
    try:
        rows = conn.execute(
            """
            SELECT * FROM v_games_by_gpu
            WHERE gpu_id = ?
            ORDER BY
                CASE tier_match WHEN 'recommended' THEN 1 WHEN 'playable' THEN 2 ELSE 3 END,
                game_name ASC
            """,
            (gpu_id,),
        ).fetchall()
        items = [dict(r) for r in rows]
        psu_safe = bool(items and (items[0]["system_peak_watts"] or 0) <= max_psu_watts)
        return {
            "gpu_id": gpu_id,
            "max_psu_watts": max_psu_watts,
            "psu_safe": psu_safe,
            "total_games": len(items),
            "recommended_count": sum(1 for x in items if x["tier_match"] == "recommended"),
            "playable_count": sum(1 for x in items if x["tier_match"] == "playable"),
            "games": items,
        }
    except sqlite3.OperationalError as e:
        return {"error": str(e), "games": []}
    finally:
        conn.close()


def query_ai_vram_fit(gpu_id: str = "rx-6600", root_dir: Path = ROOT_DIR) -> dict[str, Any]:
    """Query cross-domain v_local_ai_vram_fit for a candidate GPU."""
    conn = open_federated_connection(root_dir)
    try:
        rows = conn.execute(
            """
            SELECT * FROM v_local_ai_vram_fit
            WHERE gpu_id = ?
            ORDER BY intelligence_index DESC
            """,
            (gpu_id,),
        ).fetchall()
        items = [dict(r) for r in rows]
        return {"gpu_id": gpu_id, "matched_open_models": len(items), "models": items}
    except sqlite3.OperationalError as e:
        return {"error": str(e), "models": []}
    finally:
        conn.close()


def query_cpu_gpu_combos(cpu_id: str = "ryzen-5-5600gt", root_dir: Path = ROOT_DIR) -> dict[str, Any]:
    """Query cross-domain v_cpu_gpu_combos for a target CPU."""
    conn = open_federated_connection(root_dir)
    try:
        rows = conn.execute(
            """
            SELECT * FROM v_cpu_gpu_combos
            WHERE cpu_id = ?
            ORDER BY estimated_peak_spike_watts ASC
            """,
            (cpu_id,),
        ).fetchall()
        items = [dict(r) for r in rows]
        return {
            "cpu_id": cpu_id,
            "total_combos": len(items),
            "safe_combos_550w": sum(1 for c in items if c.get("psu_550w_combo_status") == "pass"),
            "combos": items,
        }
    except sqlite3.OperationalError as e:
        return {"error": str(e), "combos": []}
    finally:
        conn.close()
