#!/usr/bin/env python3
"""Database Manager — SQLite ATTACH Cross-Domain Query Hub.

Attaches isolated per-domain SQLite databases (`pc.sqlite`, `games.sqlite`,
`ai.sqlite`, `media.sqlite`, `book.sqlite`, `phone.sqlite`, `github.sqlite`,
plus any future registered domains) into one in-memory federated SQLite session
and exposes cross-domain analytical views (`games x pc`, `cpus x gpus`,
`game_benchmarks x pc`).

AI models remain decoupled from local GPU VRAM constraints.
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
        return {"version": "2.0.0", "groups": {}, "domains": {}, "cross_domain_views": []}
    return json.loads(registry_path.read_text(encoding="utf-8"))


def resolve_domain_key(name_or_alias: str, reg: dict[str, Any] | None = None) -> str | None:
    """Resolve a canonical domain key from ID, display_name, short_label, or aliases."""
    manifest = reg if reg is not None else load_registry()
    needle = str(name_or_alias or "").strip().lower()
    if not needle:
        return None
    domains = manifest.get("domains", {})
    if needle in domains:
        return needle
    for dom_key, cfg in domains.items():
        if str(cfg.get("display_name", "")).strip().lower() == needle:
            return dom_key
        if str(cfg.get("short_label", "")).strip().lower() == needle:
            return dom_key
        for alias in cfg.get("aliases", []):
            if str(alias).strip().lower() == needle:
                return dom_key
    return None


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

    # Logical cross-domain view 1: PC Games x Unified PC GPUs
    if "games" in attached and "pc" in attached:
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
                g.ownership,
                g.steam_app_id,
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
            CROSS JOIN pc.pc_gpus h;
            """
        )

        # Logical cross-domain view 2: Measured Game Benchmarks x Unified PC GPUs
        conn.execute(
            """
            CREATE TEMP VIEW v_game_benchmarks_with_pc AS
            SELECT
                b.id AS benchmark_id,
                b.game_id,
                COALESCE(g.name, b.game_id) AS game_name,
                g.genre,
                g.ownership,
                b.cpu_name,
                b.gpu_id,
                COALESCE(h.name, b.gpu_id) AS gpu_name,
                h.tier AS gpu_tier,
                h.vram_gb,
                h.tdp_watts,
                h.system_peak_watts,
                h.psu_550w_verdict,
                h.price_bdt_retail AS gpu_price_bdt_retail,
                b.resolution,
                b.preset,
                b.avg_fps,
                b.low_1pct_fps,
                b.low_01pct_fps,
                b.source_url,
                b.recorded_at
            FROM games.game_benchmarks b
            LEFT JOIN games.pc_games g ON b.game_id = g.id
            LEFT JOIN pc.pc_gpus h ON b.gpu_id = h.id;
            """
        )

    # Logical cross-domain view 3: PC CPUs x PC GPUs platform power & upgrade combos
    if "pc" in attached:
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
            FROM pc.pc_cpus c
            CROSS JOIN pc.pc_gpus h;
            """
        )

    return conn


def query_domain_health(root_dir: Path = ROOT_DIR) -> list[dict[str, Any]]:
    """Return freshness, display metadata, grouping, record count, and SHA-256 status for every registered domain."""
    reg = load_registry(root_dir / "data" / "registry.json")
    groups = reg.get("groups", {})
    now = datetime.datetime.now(datetime.timezone.utc)
    results: list[dict[str, Any]] = []

    ordered_domains = sorted(
        reg.get("domains", {}).items(),
        key=lambda kv: (int(kv[1].get("tab_order", 999)), kv[0]),
    )

    for domain, cfg in ordered_domains:
        db_path = root_dir / cfg.get("sqlite_file", "")
        max_age = int(cfg.get("max_age_days", 30))
        grp_id = str(cfg.get("group", "general"))
        grp_cfg = groups.get(grp_id, {}) if isinstance(groups, dict) else {}
        entry: dict[str, Any] = {
            "domain": domain,
            "display_name": cfg.get("display_name", cfg.get("title", domain)),
            "short_label": cfg.get("short_label", cfg.get("display_name", domain)),
            "unit_label": cfg.get("unit_label", "records"),
            "aliases": cfg.get("aliases", []),
            "group": grp_id,
            "group_display_name": grp_cfg.get("display_name", grp_id.replace("_", " ").title()),
            "group_order": int(grp_cfg.get("order", 99)),
            "tab_order": int(cfg.get("tab_order", 999)),
            "show_in_portal": bool(cfg.get("show_in_portal", True)),
            "web_path": cfg.get("web_path", f"{domain}/index.html"),
            "api_path": cfg.get("api_path", f"/api/{domain}"),
            "title": cfg.get("title", cfg.get("display_name", domain)),
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


def query_game_benchmarks_with_pc(
    gpu_id: str | None = None,
    game_id: str | None = None,
    root_dir: Path = ROOT_DIR,
) -> dict[str, Any]:
    """Query measured FPS benchmarks joined with unified PC GPU specs and game titles."""
    conn = open_federated_connection(root_dir)
    try:
        clauses: list[str] = []
        params: list[Any] = []
        if gpu_id:
            clauses.append("gpu_id = ?")
            params.append(gpu_id)
        if game_id:
            clauses.append("game_id = ?")
            params.append(game_id)
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = conn.execute(
            f"""
            SELECT * FROM v_game_benchmarks_with_pc
            {where_sql}
            ORDER BY game_name ASC, avg_fps DESC
            """,
            tuple(params),
        ).fetchall()
        items = [dict(r) for r in rows]
        return {
            "gpu_id": gpu_id,
            "game_id": game_id,
            "total_benchmarks": len(items),
            "benchmarks": items,
        }
    except sqlite3.OperationalError as e:
        return {"error": str(e), "benchmarks": []}
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


def query_games_storage_summary(root_dir: Path = ROOT_DIR) -> dict[str, Any]:
    """Summarize game install footprints across owned vs wishlist against PC SSD/HDD options."""
    conn = open_federated_connection(root_dir)
    try:
        game_rows = conn.execute(
            "SELECT id, name, ownership, install_gb, raw_json FROM games.pc_games"
        ).fetchall()
        drive_rows = conn.execute(
            "SELECT id, category, name, price_bdt, price_usd, specs_json FROM pc.pc_components WHERE category IN ('ssds', 'hdds')"
        ).fetchall()

        total_gb = 0.0
        owned_gb = 0.0
        wishlist_gb = 0.0
        ssd_priority_gb = 0.0
        hdd_safe_gb = 0.0
        for r in game_rows:
            gb = float(r["install_gb"] or 0.0)
            total_gb += gb
            if r["ownership"] == "owned":
                owned_gb += gb
            else:
                wishlist_gb += gb
            raw = json.loads(r["raw_json"] or "{}")
            verdict = (raw.get("storageAdvice") or {}).get("verdict", "hdd-fine")
            if verdict == "hdd-fine":
                hdd_safe_gb += gb
            else:
                ssd_priority_gb += gb

        drives = []
        for d in drive_rows:
            sp = json.loads(d["specs_json"] or "{}")
            cap_gb = sp.get("capacity_gb") or (float(sp.get("capacity_tb") or 0) * 1000.0)
            drives.append(
                {
                    "id": d["id"],
                    "category": d["category"],
                    "name": d["name"],
                    "capacity_gb": cap_gb,
                    "price_bdt": d["price_bdt"],
                    "recording_tech": sp.get("recording_tech"),
                    "interface": sp.get("interface"),
                }
            )

        return {
            "total_games": len(game_rows),
            "total_install_gb": round(total_gb, 1),
            "owned_install_gb": round(owned_gb, 1),
            "wishlist_install_gb": round(wishlist_gb, 1),
            "ssd_priority_gb": round(ssd_priority_gb, 1),
            "hdd_safe_gb": round(hdd_safe_gb, 1),
            "pc_storage_options": drives,
        }
    except sqlite3.OperationalError as e:
        return {"error": str(e)}
    finally:
        conn.close()
