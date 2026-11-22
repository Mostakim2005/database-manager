#!/usr/bin/env python3
"""Database Manager — Full PC & Peripherals Programmatic Compatibility Engine.

Evaluates physical, electrical, bandwidth, and ergonomic interlinks across:
CPUs, GPUs, Motherboards, RAM, SSDs, HDDs, Monitors, TVs, Keyboards, Mice,
and Graphics Tablets.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
COMPONENTS_PATH = ROOT_DIR / "data" / "pc_components" / "components.json"


def load_components(path: Path = COMPONENTS_PATH) -> dict[str, Any]:
    """Load the full PC & peripherals component catalog."""
    return json.loads(path.read_text(encoding="utf-8"))


def _transient_multiplier(tdp_watts: float) -> float:
    if tdp_watts >= 250:
        return 2.0
    if tdp_watts >= 180:
        return 1.65
    return 1.35


def evaluate_build(build: dict[str, Any]) -> dict[str, Any]:
    """Run all cross-component compatibility & bottleneck rules on a PC + peripherals build."""
    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    cpu = build.get("cpu") or {}
    mobo = build.get("motherboard") or {}
    ram = build.get("ram") or {}
    gpu = build.get("gpu") or {}
    ssds: list[dict[str, Any]] = build.get("ssds") or []
    hdds: list[dict[str, Any]] = build.get("hdds") or []
    monitor = build.get("monitor")
    tv = build.get("tv")
    keyboard = build.get("keyboard")
    mouse = build.get("mouse")
    tablet = build.get("graphics_tablet")
    psu_watts = float(build.get("psu_watts", 550))
    base_watts = float(build.get("base_system_watts", 85))

    # 1. CPU <-> Motherboard socket
    if cpu and mobo:
        if cpu.get("socket") != mobo.get("socket"):
            errors.append(
                f"Socket mismatch: CPU {cpu.get('name')} ({cpu.get('socket')}) does not fit Motherboard {mobo.get('name')} ({mobo.get('socket')})."
            )
        if not gpu and not cpu.get("has_igpu"):
            errors.append(
                f"No display output: CPU {cpu.get('name')} has no integrated GPU and no discrete GPU is selected."
            )

    # 2. Motherboard <-> RAM
    if mobo and ram:
        if mobo.get("ddr_gen") != ram.get("ddr_gen"):
            errors.append(
                f"RAM mismatch: {ram.get('name')} ({ram.get('ddr_gen')}) is incompatible with {mobo.get('name')} ({mobo.get('ddr_gen')})."
            )
        if int(ram.get("sticks", 0)) > int(mobo.get("ram_slots", 0)):
            errors.append(
                f"RAM slot overflow: {ram.get('sticks')} sticks exceed motherboard's {mobo.get('ram_slots')} DIMM slots."
            )
        if int(ram.get("speed_mt", 0)) > int(mobo.get("max_ram_mt", 99999)):
            warnings.append(
                f"RAM speed {ram.get('speed_mt')} MT/s exceeds motherboard spec ({mobo.get('max_ram_mt')} MT/s); will downclock."
            )

    # 3. Storage (SSDs & HDDs) <-> Motherboard & CPU PCIe generation
    nvme_count = sum(1 for s in ssds if "nvme" in str(s.get("interface", "")).lower())
    sata_ssd_count = sum(1 for s in ssds if "sata" in str(s.get("interface", "")).lower())
    total_sata = sata_ssd_count + len(hdds)

    if mobo:
        if nvme_count > int(mobo.get("m2_slots", 0)):
            errors.append(f"M.2 slot overflow: {nvme_count} NVMe SSDs selected but motherboard has {mobo.get('m2_slots')} M.2 slot(s).")
        if total_sata > int(mobo.get("sata_ports", 0)):
            errors.append(f"SATA port overflow: {total_sata} SATA drives exceed motherboard's {mobo.get('sata_ports')} SATA ports.")

    effective_pcie = min(int(cpu.get("pcie_gen", 4) or 4), int(mobo.get("pcie_gen", 4) or 4)) if (cpu or mobo) else 4
    for s in ssds:
        if int(s.get("pcie_gen", 0)) > effective_pcie:
            notes.append(
                f"PCIe cap: {s.get('name')} (PCIe Gen {s.get('pcie_gen')}) will run at Gen {effective_pcie} speeds (~3,500 MB/s max on Gen 3) — fully compatible."
            )
    for h in hdds:
        if str(h.get("recording_tech", "")).upper() == "SMR":
            warnings.append(
                f"SMR HDD warning: {h.get('name')} uses SMR recording, which degrades sustained writes and large game patching; prefer CMR or SSD."
            )
    if hdds and not ssds:
        warnings.append("HDD-only build: Modern streaming RTS/strategy games will experience texture pop-in and traversal stutter without an SSD.")

    # 4. CPU + GPU <-> PSU Transient Excursion Guard
    psu_summary: dict[str, Any] = {"psu_watts": psu_watts, "status": "pass"}
    if gpu:
        tdp = float(gpu.get("tdp_watts", 0))
        mult = _transient_multiplier(tdp)
        cpu_extra = max(0.0, float(cpu.get("tdp_watts", 65)) - 65.0)
        continuous = round(tdp + base_watts + cpu_extra, 1)
        peak = round(tdp * mult + base_watts + cpu_extra, 1)
        headroom = round(psu_watts - peak, 1)
        psu_summary.update({"continuous_watts": continuous, "peak_spike_watts": peak, "multiplier": mult, "headroom_watts": headroom})
        if peak > psu_watts:
            psu_summary["status"] = "fail"
            errors.append(
                f"PSU OCP Trip Risk: {gpu.get('name')} transient spike (~{peak}W at {mult}x) exceeds {psu_watts}W PSU by {abs(headroom)}W."
            )
        elif continuous > 0.75 * psu_watts or peak > 0.85 * psu_watts:
            psu_summary["status"] = "warn"
            warnings.append(f"Heavy PSU Load: Continuous {continuous}W / Peak ~{peak}W on {psu_watts}W PSU.")

        if int(gpu.get("pcie_gen", 4)) > effective_pcie and int(gpu.get("pcie_lanes", 16)) <= 8:
            notes.append(
                f"PCIe x8 Gen {effective_pcie} note: {gpu.get('name')} is an x8 Gen {gpu.get('pcie_gen')} card running on Gen {effective_pcie} (~2-5% avg impact at 1080p)."
            )

    # 5. GPU <-> Monitor & TV Display Interlinks
    display_ports_used = 0
    if monitor:
        display_ports_used += 1
        if gpu and monitor.get("resolution") == "4K" and gpu.get("target_res") == "1080p":
            warnings.append(f"Resolution mismatch: {gpu.get('name')} targets 1080p while {monitor.get('name')} is 4K.")
        if monitor.get("resolution") == "1440p" and int(monitor.get("refresh_hz", 60)) >= 144:
            notes.append(f"Display cable note: Connect {monitor.get('name')} via DisplayPort 1.4 for full {monitor.get('refresh_hz')}Hz + VRR.")

    if tv:
        display_ports_used += 1
        if not tv.get("chroma_444", True):
            warnings.append(f"TV PC clarity warning: {tv.get('name')} lacks 4:4:4 chroma subsampling — desktop text may look fuzzy.")
        if float(tv.get("input_lag_ms", 0)) > 20.0:
            warnings.append(f"TV input lag warning: {tv.get('name')} has {tv.get('input_lag_ms')}ms input lag (>20ms feels sluggish for RTS/mouse control).")
        if tv.get("resolution") == "4K" and int(tv.get("refresh_hz", 60)) >= 120 and str(tv.get("hdmi_version", "2.0")) < "2.1":
            errors.append(f"TV bandwidth limit: {tv.get('name')} needs HDMI 2.1 for 4K 120Hz+.")

    # 6. Graphics Tablet <-> GPU / Motherboard
    if tablet:
        if tablet.get("requires_display_port"):
            display_ports_used += 1
            if mobo and not mobo.get("usb_c_dp_alt"):
                notes.append(
                    f"Pen Display cable note: {mobo.get('name')} lacks USB-C DP-Alt-Mode; connect {tablet.get('name')} using its 3-in-1 HDMI + USB cable to the GPU."
                )

    if gpu:
        gpu_outputs = gpu.get("outputs") or {}
        total_gpu_ports = int(gpu_outputs.get("hdmi_count", 1)) + int(gpu_outputs.get("dp_count", 3))
        if display_ports_used > total_gpu_ports:
            errors.append(f"Display output overflow: {display_ports_used} displays/pen-displays exceed GPU's {total_gpu_ports} outputs.")

    # 7. USB Port Budget (Keyboard + Mouse + Tablet)
    usb_needed = sum(int(p.get("usb_ports_needed", 0)) for p in (keyboard, mouse, tablet) if p)
    if mobo and usb_needed > int(mobo.get("usb_ports", 0)):
        errors.append(f"USB port overflow: Peripherals need {usb_needed} USB ports, motherboard has {mobo.get('usb_ports')}.")

    # Total BDT / USD cost rollup
    all_parts = [p for p in (cpu, mobo, ram, gpu, monitor, tv, keyboard, mouse, tablet) if p] + list(ssds) + list(hdds)
    total_bdt = sum(float(p.get("price_bdt", 0)) for p in all_parts)
    total_usd = sum(float(p.get("price_usd", 0)) for p in all_parts)

    return {
        "compatible": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "notes": notes,
        "psu_analysis": psu_summary,
        "usb_ports_used": usb_needed,
        "display_outputs_used": display_ports_used,
        "estimated_total_bdt": round(total_bdt, 2),
        "estimated_total_usd": round(total_usd, 2),
    }


def evaluate_default_build() -> dict[str, Any]:
    """Evaluate a representative Ryzen 5 5600GT + RX 6600 + Peripherals build."""
    cat = load_components()
    by_id = lambda sec, key: next(x for x in cat[sec] if x["id"] == key)
    build = {
        "cpu": by_id("cpus", "ryzen-5-5600gt"),
        "motherboard": by_id("motherboards", "msi-b450m-pro-vdh-max"),
        "ram": by_id("ram", "corsair-16gb-ddr4-3200"),
        "gpu": by_id("gpus", "rx-6600"),
        "ssds": [by_id("ssds", "wd-sn580-1tb")],
        "hdds": [by_id("hdds", "wd-blue-1tb-cmr")],
        "monitor": by_id("monitors", "msi-g2412f-1080p-180"),
        "keyboard": by_id("keyboards", "keychron-k2-v2"),
        "mouse": by_id("mice", "logitech-g304"),
        "graphics_tablet": by_id("graphics_tablets", "xppen-artist-12-gen2"),
        "psu_watts": 550,
    }
    return evaluate_build(build)


def main() -> None:
    parser = argparse.ArgumentParser(description="PC & Peripherals Compatibility Engine")
    parser.add_argument("--demo", action="store_true", help="Evaluate default Ryzen 5 5600GT + RX 6600 build")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    result = evaluate_default_build()
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print("\n=== PC & PERIPHERALS COMPATIBILITY REPORT ===")
    print(f"  Compatible: {'YES' if result['compatible'] else 'NO'} ({result['error_count']} errors, {result['warning_count']} warnings)")
    print(f"  PSU Peak:   ~{result['psu_analysis'].get('peak_spike_watts', 0)}W / {result['psu_analysis']['psu_watts']}W ({result['psu_analysis']['status'].upper()})")
    print(f"  Total Est.: ৳{result['estimated_total_bdt']:,.0f} | ${result['estimated_total_usd']:,.0f}")
    for e in result["errors"]:
        print(f"  [ERROR] {e}")
    for w in result["warnings"]:
        print(f"  [WARN]  {w}")
    for n in result["notes"]:
        print(f"  [NOTE]  {n}")
    print("")


if __name__ == "__main__":
    main()
