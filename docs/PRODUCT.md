# Product Intent & Feature Map (`PRODUCT.md`)
> **1-Line Summary:** Unified benchmark, compatibility, catalog, personal library, and repository telemetry database manager across 7 grouped domains (`pc`, `games`, `ai`, `media`, `book`, `phone`, `github`).

## 1. Core Vision & User Experience Intent
* **What This App Does (Plain English):** Consolidates 7 cleanly scoped domains into one zero-dependency local hub (`127.0.0.1:8770`): unified PC hardware & build compatibility (`pc`), unified owned Steam library + strategy/RTS wishlist game benchmarks cross-linked directly with `pc` GPUs and storage (`games`), API pricing & model intelligence rankings (`ai`, decoupled from local VRAM), interconnected multi-format media & adaptations (`media`), personal book tracking (`book`, rename-ready for `learning`/`reading`), mobile specs & supported apps/games (`phone`), and GitHub repository/CI health telemetry (`github`).
* **How It Must Feel to Use:** Ultra-fast, zero-dependency, local-first dashboard with dark-mode GitHub styling, registry-driven grouped navigation that supports painless domain renames and aliases, instant client-side filtering, strictly table-isolated per-domain SQLite files, and dual terminal CLI/REST API interfaces.

## 2. Active Features (Do Not Break)

### [FEATURE: Unified-PC-Domain-And-Compatibility-Engine] | Aliases: pc domain, hardware, cpus, pc_components, psu guard, compatibility engine
> **1-Line Summary:** Consolidated PC catalog (`data/pc/pc.json`) unifying 79 parts across 12 categories (`cpus`, `gpus`, `psus`, motherboards, RAM, storage incl. 2TB/4TB NVMe SSDs, displays, peripherals) with 550W PSU transient excursion checks and full-rig compatibility validation.
* **User Intention (Non-Negotiable):** Maintain one canonical `pc` source of truth for all desktop hardware, preventing socket/DDR mismatches, drawing tablet DP-Alt-Mode traps, SMR drive gaming stutters, and microsecond PSU Over-Current Protection (OCP) trips.
* **Visual / UI Behavior:** Unified dashboard in `web/pc/index.html` combining category browsing, 550W PSU transient spike gauges, multi-retailer BD pricing, and full-build validation via `/api/pc`, `/api/pc/gpus`, `/api/pc/cpus`, `/api/pc/check-build`, and `/api/cross/check-build`.
* **Code Anchors (Grep Targets):**
  * `data/pc/pc.json` -> `system_baseline`, `transient_rules`, `cpus`, `gpus`, `ssds`, `psus`
  * `src/compatibility_engine.py` -> `compute_transient_metrics`, `evaluate_build`, `evaluate_default_build`
  * `web/pc/index.html` -> safe-DOM PC catalog & PSU guard renderer

### [FEATURE: GameRank-Compatibility-And-PC-Link] | Aliases: game rank, vega 7 rts, fps preset, upgrade simulator, game benchmarks, steam library
> **1-Line Summary:** Unified 153-title PC & strategy catalog (`105` owned Steam titles + `48` researched wishlist titles) across 12 genres evaluated against Ryzen 5 5600GT (Vega 7), 51 measured FPS benchmark runs (`benchmarks.csv`), live Disk Footprint & Storage Advisor, and canonical `pc` GPU/SSD cross-links.
* **User Intention (Non-Negotiable):** Keep owned Steam games and researched wishlist titles in one unified schema v4.0.0 structure (`ownership`, `steamAppId`, `companions`, `specs`, `hddSp`, `storageAdvice`), enriched via Steam Store/Player/SteamSpy APIs and cross-linked to `pc` GPUs and NVMe/HDD storage.
* **Visual / UI Behavior:** Lives in `web/games/index.html` with `All / Owned / Wishlist` filter, 12 genre filters across Steam PC and RTS categories, live Disk Footprint & SSD/HDD Advisor bar, canonical `pc`-keyed GPU simulator dropdown, companion/test-server modal badges, and card/table views.
* **Code Anchors (Grep Targets):**
  * `src/scrapers/multi_site_games.py` -> `normalize_game_record`, `fetch_steam_metadata`, `build_record_from_steam`, `apply_games_update`
  * `web/games/js/rank.js` -> `UPGRADE_GPUS`, `resolveUpgradeGpuKey`, `compatScoreFor`, `computeUpgradedCompat`
  * `web/games/js/app.js` -> `hydrateLivePcGpus`, `hydrateLivePcStorage`, `renderStorageAdvisor`
  * `src/db_hub.py` -> `query_games_by_gpu`, `query_game_benchmarks_with_pc`, `query_games_storage_summary`

### [FEATURE: AI-Model-Benchmark-And-Pricing-Matrix] | Aliases: ai matrix, frontier models, coding elo, token pricing, chinese oss
> **1-Line Summary:** Standalone 52-model AI pricing, benchmark, geopolitical origin, and tier matrix (`frontier`, `near_frontier`, `mid_tier`, `specialized`) completely decoupled from local GPU VRAM constraints.
* **User Intention (Non-Negotiable):** Evaluate API cost-to-intelligence tradeoffs across Western/Chinese and open/closed models for cloud usage without meaningless local-VRAM mapping rules.
* **Visual / UI Behavior:** Lives in `web/ai/index.html` featuring sortable columns, effort normalization, and multi-axis classification via `/api/ai` and `/api/ai/classified`.
* **Code Anchors (Grep Targets):**
  * `src/catalog_classifier.py` -> `classify_ai_model`, `classify_ai_catalog`
  * `data/ai/taxonomy.json` -> `model_tiers`
  * `data/ai/models_master.json` -> `models`

### [FEATURE: Media-Catalog-And-Adaptation-Hub] | Aliases: media domain, manga, manhua, light novel, anime, donghua, movie, tv_series
> **1-Line Summary:** Interconnected 117-entry media catalog uniting `comic`, `light_novel`, `anime`, `donghua`, `movie`, and `tv_series` via `franchise_id`/`relations` (including Steam-linked adaptations tagged `plan_to_watch` / `plan_to_read`), canonical `comix.to` sitemap lookup, adaptation probes, and link health audits without external Obsidian markdown sync.
* **User Intention (Non-Negotiable):** Model adaptation chains (e.g., light novel -> comic/anime/donghua -> movie/series) natively inside SQLite/JSON while preserving `Outlander` TV series tracking cleanly (excluding private MEGA URLs), marking game-linked additions unambiguously as `plan_to_watch` / `plan_to_read`, and discarding legacy Obsidian markdown write-back.
* **Visual / UI Behavior:** Dashboard `web/media/index.html` featuring subdomain filters, origin filters, `Plan to Watch / Read (Wishlist)` filter & badges, clickable franchise relation chips, Doctor diagnostics, and Link Audit panels backed by `/api/media`, `/api/media/doctor`, `/api/media/links`, and `/api/media/classified`.
* **Code Anchors (Grep Targets):**
  * `src/media/__init__.py` -> `load_catalog`
  * `src/media/adaptation_refresh.py` -> `inspect_catalog_doctor`, `propose_link_upgrades`
  * `src/media/link_health.py` -> `audit_catalog_links_offline`, `check_catalog_links_live`
  * `web/media/index.html` -> franchise relation chips, watchlist badges & safe-DOM table renderer

### [FEATURE: Book-Collection-And-Reading-Tracker] | Aliases: book domain, books, learning, reading
> **1-Line Summary:** Personal library catalog (`books.json` / `book.sqlite`) tracking 9 books (4 owned/core + 5 Steam-franchise source novels tagged `wishlist` / `queued` / unread) with title, author, subject, format, ownership, reading status, ratings, and notes with alias readiness (`learning`, `reading`).
* **User Intention (Non-Negotiable):** Track owned vs wishlist vs active reading books (explicitly marking unread game-source books as `wishlist` + `queued`) while keeping labels and aliases in `data/registry.json` flexible enough to rename the domain (e.g. `Book` -> `Learning`) without code rewrites.
* **Visual / UI Behavior:** Safe-DOM card view in `web/book/index.html` with KPI summary strip, ownership/reading/format filters, live alias chips, and `/api/book` + `/api/domain/learning` alias routing.
* **Code Anchors (Grep Targets):**
  * `data/book/schema.json` -> book field contracts and enums
  * `src/db_export.py` -> `create_book_schema`, `export_books`
  * `web/book/index.html` -> `applyFilters`, `renderKPIs`

### [FEATURE: Phone-Specs-And-App-Support-Catalog] | Aliases: phone domain, phones, mobile, smartphones
> **1-Line Summary:** Mobile device specifications catalog (`phones.json` / `phone.sqlite`) tracking SoC, GPU, RAM, display refresh rate, battery/charging, BD/USD pricing, and verified `supported_games` (including mobile editions of Steam titles) / `supported_apps` compatibility lists.
* **User Intention (Non-Negotiable):** Compare smartphones both on hardware capability (Snapdragon/Exynos SoC, RAM, LTPO/AMOLED display, charging wattage) and on real-world app/game compatibility profiles.
* **Visual / UI Behavior:** Safe-DOM dashboard in `web/phone/index.html` with SoC/RAM/brand filters, dual supported games & supported apps badges (`locked`, `smooth`, `playable`, `supported`), and `/api/phone`.
* **Code Anchors (Grep Targets):**
  * `data/phone/schema.json` -> device spec ranges and required fields
  * `src/db_export.py` -> `create_phone_schema`, `export_phones`
  * `web/phone/index.html` -> `applyFilters`, `makeSupportBlock`

### [FEATURE: GitHub-Repositories-And-CI-Hub] | Aliases: github manager, repo triage, ci health, upstream fork drift
> **1-Line Summary:** DevOps domain (`github`) tracking repository activity timelines (0–4d, 4–8d, dormant), GitHub Actions CI health, unbuilt/unreleased commit gaps, upstream fork drift, and Markdown audit exports.
* **User Intention (Non-Negotiable):** Track all repositories on port `8770`, redact private repo metadata from committed `data/github/repos_public.json` into gitignored `live_cache.json`, render strictly with safe DOM, and guard `POST` mutations with loopback `Origin`/`Host` CSRF validation.
* **Visual / UI Behavior:** Grouped `DevOps` tab in `web/index.html` loading `web/github/index.html`, backed by `/api/github`, `/api/github/triage`, `/api/github/doctor`, `/api/github/classified`, and `POST /api/github/{refresh,export}`.
* **Code Anchors (Grep Targets):**
  * `src/github/scanner.py` -> `scan_all_repositories`, `triage_repositories`, `redact_public_repos`
  * `src/github/exporter.py` -> `export_markdown_report`
  * `web/github/index.html` -> `renderTable`, `inspectRepo`, `loadTriage`

### [FEATURE: Registry-Driven-Dynamic-Portal-And-Isolated-SQLite] | Aliases: master dashboard, web portal, db hub, db export, table isolation, aliases
> **1-Line Summary:** Dynamic grouped web portal (`web/index.html`), alias-aware domain resolver (`resolve_domain_key`), strictly table-isolated per-domain SQLite builds (`compile_separated_domains`), and cross-domain `games` <-> `pc` federation (`db_hub.py`).
* **User Intention (Non-Negotiable):** Enable painless domain renames (`display_name`, `short_label`, `aliases`, `group` in `data/registry.json`), guarantee every `data/<domain>/<domain>.sqlite` holds strictly its own tables + `_meta`, and retire pre-reorg legacy routes cleanly (`404`).
* **Visual / UI Behavior:** Top header renders group-clustered tabs, quick-links, and live domain stats straight from `/api/status`; `#<alias>` URL hashes and `/api/domain/<alias>` resolve aliases automatically.
* **Code Anchors (Grep Targets):**
  * `data/registry.json` -> `groups`, `domains`, `cross_domain_views`
  * `src/db_export.py` -> `SCHEMA_CREATORS`, `compile_separated_domains`, `compile_database`
  * `src/db_hub.py` -> `open_federated_connection`, `query_domain_health`, `resolve_domain_key`
  * `src/server.py` -> `DatabaseHandler.do_GET`, `search_databases`
  * `web/index.html` -> `buildPortalChrome`, `resolveTargetTab`

### [FEATURE: Multi-Site-Catalog-Expansion-And-Scrapers] | Aliases: multi site scrapers, retail reconciliation, steam api, openrouter sync, bd retail
> **1-Line Summary:** Multi-tier scraping and consensus pricing engine across PC hardware (Star Tech, Ryans, UCC -> `data/pc/pc.json`), Games (benchmarks CSV & yt-dlp), and AI catalogs with `--dry-run` diff safety.
* **User Intention (Non-Negotiable):** Prevent single-retailer bias and destructive overwrites through multi-source consensus, BDT spread alerts (>20%), and offline CI compatibility (`Tier 0` stdlib fallback).
* **Visual / UI Behavior:** CLI execution via `--dry-run` diff tables prior to opt-in `--apply` persistence.
* **Code Anchors (Grep Targets):**
  * `src/scrapers/bd_hardware.py` -> `compute_live_price_sync`
  * `src/scrapers/multi_site_components.py` -> `sync_multi_site_components`
  * `src/scrapers/benchmark_ingest.py` -> `ingest_csv`, `verify_benchmarks`

## 3. Planned Features & App-Merge Wishlist

### [WISHLIST: One-Click-Fork-Sync-Button] | Aliases: remote sync, sync fork from UI, gh repo sync
> **1-Line Summary:** Add an opt-in UI action to fast-forward behind-upstream forks via `gh repo sync` directly from the GitHub Repos tab.
* **User Intention:** Allow zero-conflict upstream forks flagged in the drift column to be synchronized without leaving the dashboard, gated behind loopback CSRF checks and fast-forward validation.
* **Target Integration Point:** `web/github/index.html` table actions + CSRF-protected `POST /api/github/sync` in `src/server.py`.

### [WISHLIST: Automated-Benchmark-Sync] | Aliases: github action benchmark sync, openrouter cron
> **1-Line Summary:** Scheduled GitHub Actions workflow to periodically query OpenRouter and models.dev APIs for newly released models.
* **User Intention:** Keep the AI model matrix continually updated with frontier releases without manual script execution.
* **Target Integration Point:** `.github/workflows/sync-benchmarks.yml` triggering `src/update_models.ps1`.

### [WISHLIST: DuckDB-In-Browser-WASM] | Aliases: duckdb wasm, browser sql, in-memory analytics
> **1-Line Summary:** Embed DuckDB-WASM in `web/index.html` for interactive SQL console querying directly within the browser dashboard.
* **User Intention:** Provide power users with direct SQL querying over SQLite/Parquet files without requiring Python backend running.
* **Target Integration Point:** `web/index.html` -> dedicated SQL Explorer tab.

### [WISHLIST: CSV-And-Playnite-Library-Export] | Aliases: playnite export, csv game export, steam library sync
> **1-Line Summary:** Export filtered GameRank lists and PC compatibility verdicts as CSV or Playnite-compatible JSON directly from the dashboard.
* **User Intention:** Allow filtered Owned/Wishlist game tables and Vega 7 / RX 6600 compatibility scores to be exported for spreadsheets or external PC launcher catalogs.
* **Target Integration Point:** `web/games/index.html` toolbar + `src/scrapers/multi_site_games.py` export helper.
