# Product Intent & Feature Map (`PRODUCT.md`)
> **1-Line Summary:** Unified benchmark, compatibility, and specifications database manager across AI models, PC games, and hardware upgrades.

## 1. Core Vision & User Experience Intent
* **What This App Does (Plain English):** Consolidates multiple fragmented datasets into one unified database and web portal: tracking AI model intelligence and coding benchmarks, 43 researched PC strategy games with compatibility scores for a Ryzen 5 5600GT (Vega 7) setup, and hardware GPU upgrade forecasting with PSU transient spike safety analysis.
* **How It Must Feel to Use:** Ultra-fast, zero-dependency, local-first dashboard with dark-mode glassmorphic styling, instant client-side filtering, and dual terminal CLI and SQLite query capabilities.

## 2. Active Features (Do Not Break)

### [FEATURE: AI-Model-Benchmark-Matrix] | Aliases: ai matrix, frontier models, coding elo, token pricing
> **1-Line Summary:** Interactive 26+ frontier model matrix with Artificial Analysis intelligence indexes, Coding Arena ELOs, reasoning effort simulations, and token pricing telemetry.
* **User Intention (Non-Negotiable):** Provide an objective comparison of frontier AI models to identify optimal intelligence-to-cost tradeoffs.
* **Visual / UI Behavior:** Lives in `web/ai/index.html` (and Tab 1 of the Unified Portal) featuring sortable columns, tier chips, and effort sliders.
* **Code Anchors (Grep Targets):**
  * `web/ai/model_matrix/app.js` -> `renderTable`, `normalizeEffortKey`
  * `data/ai/models_master.json` -> `models`

### [FEATURE: GameRank-Compatibility-Simulator] | Aliases: game rank, vega 7 rts, fps preset, upgrade simulator
> **1-Line Summary:** Evaluates 43 strategy/RTS titles against a reference Ryzen 5 5600GT (Vega 7 iGPU, 16GB, HDD) with real-time FPS simulator for GPU upgrade tiers.
* **User Intention (Non-Negotiable):** Show exact playable FPS and compatibility verdicts before purchasing games or upgrading hardware.
* **Visual / UI Behavior:** Lives in `web/games/index.html` (and Tab 2 of the Unified Portal) with card/table views, GPU simulator dropdown, and detail modals.
* **Code Anchors (Grep Targets):**
  * `web/games/js/rank.js` -> `compatScoreFor`, `computeUpgradedCompat`
  * `data/games/games.json` -> `window.GAMES`

### [FEATURE: PSU-Transient-Spike-Guard] | Aliases: psu guard, hardware planner, 550w headroom, transient spike
> **1-Line Summary:** Evaluates GPU upgrade paths against a 550W Bronze PSU (43A single +12V rail) calculating microsecond transient excursions and Over-Current Protection (OCP) trip risks.
* **User Intention (Non-Negotiable):** Prevent system shutdowns by warning against high-TDP cards that produce 2.0x microsecond power spikes.
* **Visual / UI Behavior:** Lives in `web/hardware/index.html` (and Tab 3 of the Unified Portal) with color-coded safety badges (Safe, Caution, Trip Risk) and dynamic headroom meters.
* **Code Anchors (Grep Targets):**
  * `web/hardware/index.html` -> `updateCalculator`
  * `data/hardware/hardware_specs.json` -> `transient_rules`, `gpus`

### [FEATURE: Unified-Web-Portal] | Aliases: master dashboard, web portal, tab switcher
> **1-Line Summary:** Single-page glassmorphic portal integrating AI Matrix, GameRank, and Hardware Guard with persistent popout links and live status strip.
* **User Intention (Non-Negotiable):** Access all three benchmark and planning tools from one unified browser window on `http://127.0.0.1:8770`.
* **Visual / UI Behavior:** Sticky header with tabs, popouts, and full-height responsive viewport switching.
* **Code Anchors (Grep Targets):**
  * `web/index.html` -> `switchTab`

### [FEATURE: Multi-Domain-CLI-And-REST-API] | Aliases: server py, cli search, json endpoints
> **1-Line Summary:** Standard Python HTTP server serving static dashboards and JSON API endpoints (`/api/ai`, `/api/games`, `/api/hardware`), with a formatted terminal search CLI.
* **User Intention (Non-Negotiable):** Run zero-dependency local queries directly from PowerShell or external scripts without launching a heavy browser.
* **Visual / UI Behavior:** Prints formatted terminal tables via `python src/server.py --cli [query]` or machine-readable JSON via `--json`.
* **Code Anchors (Grep Targets):**
  * `src/server.py` -> `run_cli_summary`, `DatabaseHandler.do_GET`

### [FEATURE: Consolidated-SQLite-Pipeline] | Aliases: db export, sqlite compiler, database sqlite
> **1-Line Summary:** Automated compilation script that maps AI, Game, and Hardware JSON catalogs into relational tables in `data/database.sqlite`.
* **User Intention (Non-Negotiable):** Enable standard SQL queries and analytical aggregation across all three data domains.
* **Visual / UI Behavior:** CLI execution via `python src/db_export.py` reporting verified record counts and schema validation.
* **Code Anchors (Grep Targets):**
  * `src/db_export.py` -> `compile_database`, `verify_database`

## 3. Planned Features & App-Merge Wishlist

### [WISHLIST: Live-Price-Scrapers] | Aliases: star tech scraper, ryans price sync, bd retail sync
> **1-Line Summary:** Automated market price scraping from major Bangladeshi tech retailers (Star Tech, Ryans) and global trackers.
* **User Intention:** Automatically refresh used and retail GPU/RAM/SSD prices in BDT without manual entry.
* **Target Integration Point:** `src/` -> `price_scraper.py` feeding `data/hardware/hardware_specs.json`.

### [WISHLIST: Automated-Benchmark-Sync] | Aliases: github action benchmark sync, openrouter cron
> **1-Line Summary:** Scheduled GitHub Actions workflow to periodically query OpenRouter and models.dev APIs for newly released models.
* **User Intention:** Keep the AI model matrix continually updated with frontier releases without manual script execution.
* **Target Integration Point:** `.github/workflows/sync-benchmarks.yml` triggering `src/update_models.ps1`.

### [WISHLIST: DuckDB-In-Browser-WASM] | Aliases: duckdb wasm, browser sql, in-memory analytics
> **1-Line Summary:** Embed DuckDB-WASM in `web/index.html` for interactive SQL console querying directly within the browser dashboard.
* **User Intention:** Provide power users with direct SQL querying over SQLite/Parquet files without requiring Python backend running.
* **Target Integration Point:** `web/index.html` -> dedicated SQL Explorer tab.
