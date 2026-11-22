#!/usr/bin/env python3
"""Database Manager — Hybrid Multi-Domain Schema & Freshness Verifier.

Validates every domain registered in data/registry.json against its declarative
data/<domain>/schema.json contract (required fields, types, enums, ranges,
unique IDs) and verifies separated SQLite freshness metadata.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def _get_nested(obj: dict[str, Any], dotted: str) -> Any:
    cur: Any = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _check_type(val: Any, expected: str) -> bool:
    if val is None:
        return True
    if expected == "str":
        return isinstance(val, str)
    if expected == "number":
        return isinstance(val, (int, float)) and not isinstance(val, bool)
    if expected == "int":
        return isinstance(val, int) and not isinstance(val, bool)
    if expected == "bool":
        return isinstance(val, bool)
    return True


def verify_domain(domain: str, cfg: dict[str, Any], root_dir: Path = ROOT_DIR) -> dict[str, Any]:
    """Validate one domain JSON dataset against its schema.json contract."""
    errors: list[str] = []
    warnings: list[str] = []

    src_path = root_dir / cfg["source_json"]
    schema_path = root_dir / cfg["schema_file"]

    if not src_path.exists():
        return {"domain": domain, "ok": False, "record_count": 0, "errors": [f"Missing source JSON: {src_path}"], "warnings": []}
    if not schema_path.exists():
        return {"domain": domain, "ok": False, "record_count": 0, "errors": [f"Missing schema file: {schema_path}"], "warnings": []}

    raw = json.loads(src_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    rec_key = schema.get("records_key")
    records = raw.get(rec_key, []) if rec_key else raw
    if not isinstance(records, list):
        return {"domain": domain, "ok": False, "record_count": 0, "errors": ["Expected list of records"], "warnings": []}

    seen_ids: set[str] = set()
    unique_key = schema.get("unique_key", "id")

    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            errors.append(f"[{domain}#{idx}] Record is not a JSON object")
            continue
        rid = str(rec.get(unique_key, f"row-{idx}"))
        if unique_key in rec:
            if rid in seen_ids:
                errors.append(f"[{domain}] Duplicate {unique_key}: {rid}")
            seen_ids.add(rid)

        for req in schema.get("required_fields", []):
            if rec.get(req) is None or rec.get(req) == "":
                errors.append(f"[{domain}:{rid}] Missing required field '{req}'")

        for f_name, f_type in schema.get("field_types", {}).items():
            val = _get_nested(rec, f_name)
            if not _check_type(val, f_type):
                errors.append(f"[{domain}:{rid}] Field '{f_name}' expected {f_type}, got {type(val).__name__}")

        for f_name, allowed in schema.get("enums", {}).items():
            val = _get_nested(rec, f_name)
            if val is not None and val not in allowed:
                errors.append(f"[{domain}:{rid}] Field '{f_name}' value '{val}' not in {allowed}")

        for f_name, bounds in schema.get("ranges", {}).items():
            val = _get_nested(rec, f_name)
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                lo, hi = bounds
                if val < lo or val > hi:
                    errors.append(f"[{domain}:{rid}] Field '{f_name}' value {val} out of range [{lo}, {hi}]")

    sqlite_path = root_dir / cfg.get("sqlite_file", "")
    if not sqlite_path.exists():
        warnings.append(f"Separated SQLite not compiled yet: {cfg.get('sqlite_file')}")

    return {
        "domain": domain,
        "ok": len(errors) == 0,
        "record_count": len(records),
        "errors": errors,
        "warnings": warnings,
    }


def verify_all(domain_filter: str | None = None, root_dir: Path = ROOT_DIR) -> dict[str, Any]:
    """Validate all domains in data/registry.json (or a single domain)."""
    reg_path = root_dir / "data" / "registry.json"
    if not reg_path.exists():
        return {"ok": False, "domains": [], "error": f"Missing {reg_path}"}
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    results = []
    for dom, cfg in reg.get("domains", {}).items():
        if domain_filter and dom != domain_filter:
            continue
        results.append(verify_domain(dom, cfg, root_dir=root_dir))
    return {"ok": all(r["ok"] for r in results) and len(results) > 0, "domains": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify multi-domain JSON schemas & SQLite freshness")
    parser.add_argument("--domain", help="Verify only a single registered domain")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    report = verify_all(domain_filter=args.domain)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n=== MULTI-DOMAIN SCHEMA VERIFICATION ===")
        for r in report["domains"]:
            status = "PASS" if r["ok"] else "FAIL"
            print(f"  [{status}] {r['domain']}: {r['record_count']} records ({len(r['errors'])} errors, {len(r['warnings'])} warnings)")
            for err in r["errors"][:10]:
                print(f"      - ERROR: {err}")
            for warn in r["warnings"][:5]:
                print(f"      - WARN:  {warn}")
        print("")

    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
