# Architectural Decisions, Pivots & Landmines (`DECISIONS_AND_TRAPS.md`)
> **1-Line Summary:** Architectural pivot log and critical engineering landmines for PC Hardware Planner.

## 1. Architectural Decisions & Pivot History

### [DECISION: Discrete-Preset-Database] | Aliases: static benchmark database, offline first
> **1-Line Summary:** Embedded local benchmark database chosen over external live API scraping.
* **Decision Maker:** `[DECIDED BY: HUMAN]`
* **Original User Intention:** Ensure the plugin works 100% offline without failing on external network timeouts or broken scraper endpoints.
* **Options Considered:**
  * **Option A (Rejected):** Real-time web scraping on every view load (unreliable, slow, breaks offline).
  * **Option B (Chosen):** Offline bundled dataset with manual and on-demand JSON override options.

## 2. Do-Not-Touch Engineering Landmines (Traps)

### [TRAP: Chart-Canvas-Destruction] | Aliases: memory leak, canvas reuse crash
> **1-Line Summary:** Recreating a Chart.js canvas without calling `.destroy()` on the prior chart leaks WebGL/canvas contexts and crashes Obsidian.
* **Strict Rule:** **NEVER** re-render a chart element without checking `if (this.currentChart) { this.currentChart.destroy(); }`.
* **Protected Code Anchors (Grep Targets):**
  * `src/main.ts` -> `cleanupActiveCharts`

### [TRAP: Single-Rail-12V-Transient-Overshoot] | Aliases: 550w shutdown, cx550 tripping
> **1-Line Summary:** High-end GPUs (e.g. RTX 3080/RX 6800XT) have 200% transient spikes that trip 550W Bronze PSUs even if nominal TDP is ~250W.
* **Strict Rule:** **NEVER** evaluate PSU safety based solely on average TDP; always incorporate transient multiplier.
* **Protected Code Anchors (Grep Targets):**
  * `src/psu.ts` -> `TRANSIENT_EXCURSION_MULTIPLIER`
