# Project Operating Instructions (`AGENTS.md`)
> **Notice:** This project inherits user persona, confirmation gates, visual standards, and documentation blueprints from the global master `AGENTS.md`. Do not duplicate those rules here.

## 1. Project Tech Stack & Environment
* **Runtime / Language:** Node.js v20+, TypeScript 5+, esbuild, Chart.js
* **Framework / Host:** Obsidian Plugin API (`obsidian`)
* **Target OS / Build Output:** Desktop & Mobile (`runtime/main.js`, `runtime/manifest.json`, `runtime/styles.css`)

## 2. Mandatory Verification & Build Commands
* **Type Check:** `npx tsc --noEmit`
* **Lint:** `npm run lint`
* **Build / Package:** `npm run build`

## 3. Repository Directory Structure & Conventions
* `src/` - Modular source files (`main.ts`, `psu.ts`, `settings.ts`).
* `runtime/` - Compiled plug-and-play deliverable files for vault deployment.
* `docs/` - Core Markdown documentation suite (`PRODUCT.md`, `ARCHITECTURE.md`, `DECISIONS_AND_TRAPS.md`, `VISUAL_LOG.md`).
* `preview/` - On-demand interactive HTML/CSS/JS visual previews, created only when explicitly requested.

## 4. Critical Trap Pointers (1-Line Warnings Only)
* **TRAP 1:** Never reuse or re-instantiate Chart.js without calling `.destroy()` on the existing chart instance — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Chart-Canvas-Destruction]`.
* **TRAP 2:** Never bypass the 550W PSU single-rail transient spike safety threshold for Zen 3 + high-draw GPUs — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Single-Rail-12V-Transient-Overshoot]`.
