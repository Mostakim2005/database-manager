# Product Intent & Feature Map (`PRODUCT.md`)
> **1-Line Summary:** Unified benchmark, compatibility, and specifications database manager across AI models, PC games, and hardware upgrades.

## 1. Core Vision & User Experience Intent
* **What This App Does (Plain English):** Consolidates multiple fragmented datasets into one unified database and web portal: tracking 52 frontier & Chinese/OSS AI models with intelligence and coding benchmarks, 53 researched PC strategy games with compatibility scores for a Ryzen 5 5600GT (Vega 7) setup, 51 real-world 1% and 0.1% Low benchmark runs, 69 PC components and peripherals with multi-retailer price reconciliation across Bangladesh retailers (Star Tech, Ryans, UCC), and hardware GPU upgrade forecasting with PSU transient spike safety analysis.
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
> **1-Line Summary:** Automated compilation script that maps AI, Game, Hardware, and CPU JSON catalogs into relational tables in `data/database.sqlite`.
* **User Intention (Non-Negotiable):** Enable standard SQL queries and analytical aggregation across all data domains.
* **Visual / UI Behavior:** CLI execution via `python src/db_export.py` reporting verified record counts and schema validation.
* **Code Anchors (Grep Targets):**
  * `src/db_export.py` -> `compile_database`, `verify_database`

### [FEATURE: Multi-Domain-SQLite-Hub-And-Federation] | Aliases: multidb hub, separated domain dbs, cross-domain views
> **1-Line Summary:** Separated domain SQLite architecture (`ai.sqlite`, `games.sqlite`, `hardware.sqlite`, `cpus.sqlite`) with in-memory ATTACH federation and cross-domain SQL views.
* **User Intention (Non-Negotiable):** Maintain clean domain boundaries with independent TTL freshness tracking while enabling zero-copy cross-domain queries.
* **Visual / UI Behavior:** Programmatic Python API `db_hub.py`, HTTP endpoints (`/api/domains`, `/api/cross/*`), and integrity verification via `db_verify.py`.
* **Code Anchors (Grep Targets):**
  * `src/db_hub.py` -> `open_federated_connection`, `query_domain_health`
  * `src/db_verify.py` -> `verify_all`
  * `data/registry.json` -> `domains`

### [FEATURE: BD-Retail-Hardware-Price-Sync] | Aliases: bd hardware scraper, star tech sync, ryans sync, ucc sync
> **1-Line Summary:** Multi-tier live web scraper targeting Star Tech, Ryans, and UCC to track GPU prices in BDT with non-destructive diff previews.
* **User Intention (Non-Negotiable):** Keep hardware upgrade pricing current with actual Bangladesh local retail stock without manual data entry.
* **Visual / UI Behavior:** CLI execution via `python src/scrapers/bd_hardware.py --dry-run` displaying tabular price deltas before optional `--apply` writing.
* **Code Anchors (Grep Targets):**
  * `src/scrapers/bd_hardware.py` -> `compute_live_price_sync`, `render_diff_table`
  * `src/scrapers/adapters.py` -> `parse_bd_retail_html`

### [FEATURE: Low-FPS-Benchmark-Telemetry] | Aliases: game benchmarks, 1% low fps, 0.1% low fps, 5600gt telemetry
> **1-Line Summary:** Real-world gaming telemetry recording Avg, 1% Low, and 0.1% Low FPS for Ryzen 5 5600GT across Vega 7, RX 6600, and RTX 4060 GPUs.
* **User Intention (Non-Negotiable):** Provide realistic frame-pacing and stutter assessments beyond deceptive average FPS numbers.
* **Visual / UI Behavior:** Ingestion CLI via `python src/scrapers/benchmark_ingest.py --verify` rendering stability indices and percentiles.
* **Code Anchors (Grep Targets):**
  * `src/scrapers/benchmark_ingest.py` -> `ingest_csv`, `print_stability_report`
  * `data/games/benchmarks.csv` -> benchmark dataset

### [FEATURE: Desktop-CPUs-Domain-And-Combo-Planner] | Aliases: cpus domain, cpu gpu combos, socket am4 am5 lga1700
> **1-Line Summary:** 4th registered domain database (`data/cpus/cpus.sqlite`) modeling desktop processors, socket architectures, and balanced CPU+GPU build combinations.
* **User Intention (Non-Negotiable):** Evaluate upgrade paths from Ryzen 5 5600GT (AM4) to 5700X3D or AM5/LGA1700 while checking combined power consumption against a 550W PSU.
* **Visual / UI Behavior:** REST API endpoint `/api/cpus` and `/api/cross/cpu-gpu-combos`, plus SQL view `v_cpu_gpu_combos`.
* **Code Anchors (Grep Targets):**
  * `data/cpus/schema.json` -> CPU schema definition
  * `data/cpus/cpus.json` -> 6 core processors catalog
  * `src/db_hub.py` -> `query_cpu_gpu_combos`

### [FEATURE: Full-PC-And-Peripherals-Compatibility-Engine] | Aliases: compatibility engine, socket am4, ddr4 ram, pen display, smr hdd, tv 60hz
> **1-Line Summary:** Evaluates complete PC rigs (motherboard, CPU, RAM, GPU, storage, PSU, monitors, drawing pen displays) for mechanical, electrical, and bus compatibility.
* **User Intention (Non-Negotiable):** Prevent costly hardware purchase mistakes (socket mismatch, DDR generation conflict, PCIe lane throttling, missing DP-Alt-Mode for pen displays, SMR drive game-load freezes).
* **Visual / UI Behavior:** CLI execution via `python src/compatibility_engine.py --demo` (or `--demo --json`) plus REST API endpoint `/api/cross/check-build` and component catalog `/api/components`.
* **Code Anchors (Grep Targets):**
  * `src/compatibility_engine.py` -> `evaluate_default_build`, `evaluate_build`
  * `src/server.py` -> `/api/cross/check-build`, `/api/components`
  * `data/pc_components/components.json` -> full component catalog
  * `data/pc_components/schema.json` -> component spec validation

### [FEATURE: Games-And-AI-Taxonomy-Classifiers] | Aliases: catalog classifier, chinese oss tiers, game taxonomy, strategy subgenres
> **1-Line Summary:** Multi-axis taxonomy classifiers partitioning AI models (Chinese OSS vs Western OSS vs Closed Frontier) and RTS/Grand Strategy games into discoverable tactical subgenres.
* **User Intention (Non-Negotiable):** Enable nuanced categorization for open-source AI models (DeepSeek, Qwen, GLM, Yi vs Llama, Mistral) and classify PC games by real-time micro vs macro tactical focus.
* **Visual / UI Behavior:** CLI execution via `python src/catalog_classifier.py --ai --chinese-oss` or `python src/catalog_classifier.py --games`, plus REST API endpoints `/api/ai/classified` and `/api/games/classified`.
* **Code Anchors (Grep Targets):**
  * `src/catalog_classifier.py` -> `classify_ai_catalog`, `classify_games_catalog`
  * `src/server.py` -> `/api/ai/classified`, `/api/games/classified`
  * `data/ai/taxonomy.json` -> AI geopolitical and capability taxonomy
  * `data/games/taxonomy.json` -> Games subgenre and pacing taxonomy

### [FEATURE: Multi-Site-Catalog-Expansion] | Aliases: multi site scrapers, retail reconciliation, steam api, openrouter sync
> **1-Line Summary:** Multi-source scraping, price reconciliation, and catalog expansion engine across PC Components (Star Tech, Ryans, UCC), Games (Steam, PCGamingWiki, BAR), and LLMs (OpenRouter, Models.dev, Arena).
* **User Intention (Non-Negotiable):** Eliminate manual data curation and single-retailer bias through multi-source consensus, tracking BDT price spreads, SKU divergence alerts, and dual-source capability concordance.
* **Visual / UI Behavior:** Modular scrapers `src/scrapers/multi_site_components.py`, `src/scrapers/multi_site_games.py`, and `src/scrapers/multi_site_ai.py` supporting `--dry-run` and `--apply`.
* **Code Anchors (Grep Targets):**
  * `src/scrapers/multi_site_components.py` -> `sync_multi_site_components`
  * `src/scrapers/multi_site_games.py` -> `sync_multi_site_games`
  * `src/scrapers/multi_site_ai.py` -> `sync_multi_site_ai`
  * `data/pc_components/components.json` -> 69 verified components across 11 categories
  * `data/games/games.json` -> 53 verified strategy games
  * `data/ai/models_master.json` -> 52 verified LLM models

### [FEATURE: Manga-Catalog-And-Adaptation-Hub] | Aliases: manga manager, manhua links, comix sitemaps, adaptation refresh, link health
> **1-Line Summary:** Unified 104-title manga, manhwa, manhua, and web-novel catalog with canonical `comix.to` sitemap lookup, adaptation research probes, streaming link health checks, Obsidian `Manhua Links.md` sync, and a dedicated Web Portal tab.
* **User Intention (Non-Negotiable):** Consolidate `Manga Manager` into `Database Manager` as the 6th registered domain (`data/manga/manga.sqlite`), keeping `data/manga/sitemaps/*.xml` gitignored, preserving `### Outlander` on Obsidian sync, and exposing non-destructive `--doctor` / `--propose` / `--check-links` workflows.
* **Visual / UI Behavior:** Tab 4 (`Manga & Adaptations`, shortcut `4`) in `web/index.html` rendering `web/manga/index.html` with origin/adaptation filters and inline Doctor & Link Audit panels, plus `/api/manga`, `/api/manga/doctor`, `/api/manga/links`, and `/api/manga/classified`.
* **Code Anchors (Grep Targets):**
  * `src/manga/cli.py` -> `main`
  * `src/manga/adaptation_refresh.py` -> `inspect_catalog_doctor`, `propose_link_upgrades`, `probe_public_adaptation_sources`, `run_adaptation_refresh`
  * `src/manga/link_health.py` -> `audit_catalog_links_offline`, `check_catalog_links_live`
  * `src/manga/sync_vault.py` -> `sync_to_obsidian`
  * `web/manga/index.html` -> `renderTable`, `loadCatalog`

## 3. Planned Features & App-Merge Wishlist

### [WISHLIST: Automated-Benchmark-Sync] | Aliases: github action benchmark sync, openrouter cron
> **1-Line Summary:** Scheduled GitHub Actions workflow to periodically query OpenRouter and models.dev APIs for newly released models.
* **User Intention:** Keep the AI model matrix continually updated with frontier releases without manual script execution.
* **Target Integration Point:** `.github/workflows/sync-benchmarks.yml` triggering `src/update_models.ps1`.

### [WISHLIST: DuckDB-In-Browser-WASM] | Aliases: duckdb wasm, browser sql, in-memory analytics
> **1-Line Summary:** Embed DuckDB-WASM in `web/index.html` for interactive SQL console querying directly within the browser dashboard.
* **User Intention:** Provide power users with direct SQL querying over SQLite/Parquet files without requiring Python backend running.
* **Target Integration Point:** `web/index.html` -> dedicated SQL Explorer tab.
