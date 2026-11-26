# Product Intent & Feature Map (`PRODUCT.md`)
> **1-Line Summary:** Unified benchmark, compatibility, catalog, personal library, and repository telemetry database manager across 7 grouped domains (`pc`, `games`, `ai`, `media`, `book`, `phone`, `github`).

## 1. Core Vision & User Experience Intent
* **What This App Does (Plain English):** Consolidates 7 cleanly scoped domains into one zero-dependency local hub (`127.0.0.1:8770`): unified PC hardware & build compatibility (`pc`), unified owned Steam library + strategy/RTS wishlist game benchmarks cross-linked directly with `pc` GPUs and storage (`games`), API pricing & model intelligence rankings (`ai`, decoupled from local VRAM), interconnected multi-format media & adaptations (`media`), personal book tracking (`book`, rename-ready for `learning`/`reading`), mobile specs & supported apps/games (`phone`), and GitHub repository/CI health telemetry (`github`).
* **How It Must Feel to Use:** Ultra-fast, zero-dependency, local-first dashboard with dark-mode GitHub styling, registry-driven grouped navigation that supports painless domain renames and aliases, instant client-side filtering, strictly table-isolated per-domain SQLite files, and dual terminal CLI/REST API interfaces.

## 2. Active Features (Do Not Break)

### [FEATURE: Unified-PC-Domain-And-Compatibility-Engine] | Aliases: pc domain, hardware, cpus, pc_components, psu guard, compatibility engine
> **1-Line Summary:** Consolidated PC catalog (`data/pc/pc.json`) unifying 82 parts across 12 categories (`cpus`, 15 `gpus` incl. Steam Ref GTX 1060 / RX 580 and RTX 2060 Super / 2070 / 2070 Super, `psus`, motherboards, RAM, storage incl. 2TB/4TB NVMe SSDs, displays, peripherals) with 550W PSU transient excursion checks and full-rig compatibility validation.
* **User Intention (Non-Negotiable):** Maintain one canonical `pc` source of truth for all desktop hardware, preventing socket/DDR mismatches, drawing tablet DP-Alt-Mode traps, SMR drive gaming stutters, and microsecond PSU Over-Current Protection (OCP) trips.
* **Visual / UI Behavior:** Unified dashboard in `web/pc/index.html` combining category browsing, 550W PSU transient spike gauges, multi-retailer BD pricing, and full-build validation via `/api/pc`, `/api/pc/gpus`, `/api/pc/cpus`, `/api/pc/check-build`, and `/api/cross/check-build`.
* **Code Anchors (Grep Targets):**
  * `data/pc/pc.json` -> `system_baseline`, `transient_rules`, `cpus`, `gpus`, `ssds`, `psus`
  * `src/compatibility_engine.py` -> `compute_transient_metrics`, `evaluate_build`, `evaluate_default_build`
  * `web/pc/index.html` -> safe-DOM PC catalog & PSU guard renderer

### [FEATURE: GameRank-Compatibility-And-PC-Link] | Aliases: game rank, vega 7 rts, fps preset, upgrade simulator, game benchmarks, steam library
> **1-Line Summary:** Unified 195-title PC & strategy catalog (`105` owned Steam titles + `90` researched wishlist titles) across 12 genres evaluated against Ryzen 5 5600GT (Vega 7), 488 FPS benchmark rows (`benchmarks.csv`) across the canonical 8-GPU progressive ladder, live Disk Footprint & Storage Advisor, and canonical `pc` GPU/SSD cross-links.
* **User Intention (Non-Negotiable):** Keep owned Steam games and researched wishlist titles in one unified schema v4.0.0 structure (`ownership`, `steamAppId`, `companions`, `specs`, `hddSp`, `storageAdvice`), automatically populating progressive benchmarks across the user's Ryzen 5 5600GT + 8-GPU ladder (`vega-7-igpu`, `rx-580-8gb`, `gtx-1660-super`, `rtx-2060-super`, `rx-6600`, `rtx-2070`, `rtx-3060`, `rtx-2070-super`) on every new game addition or benchmark update.
* **Visual / UI Behavior:** Lives in `web/games/index.html` with `All / Owned / Wishlist` filter, 12 genre filters across Steam PC and RTS categories, live Disk Footprint & SSD/HDD Advisor bar, canonical `pc`-keyed GPU simulator dropdown, `460:215` Steam CDN cover thumbnails with genre-themed SVG fallbacks, compact 2×2 telemetry cards surfacing active-GPU FPS + install GB prominently, direct 1-click Store CTAs (`Open Steam` or the game's default store/launcher) in both Card and Table views, live **Progressive GPU FPS Scaling Table** inside the detail modal, and companion/test-server modal badges.
* **Code Anchors (Grep Targets):**
  * `src/scrapers/multi_site_games.py` -> `BENCHMARK_GPU_LADDER`, `normalize_game_record`, `fetch_steam_metadata`, `build_record_from_steam`, `apply_games_update`
  * `data/games/taxonomy.json` -> `benchmark_gpu_ladder`
  * `web/games/js/rank.js` -> `UPGRADE_GPUS`, `resolveUpgradeGpuKey`, `compatScoreFor`, `computeUpgradedCompat`
  * `web/games/js/app.js` -> `hydrateLivePcGpus`, `hydrateLivePcStorage`, `hydrateLiveBenchmarks`, `renderStorageAdvisor`
  * `web/games/js/render.js` -> `getGameCoverUrl`, `resolveGameStores`, `compactFpsSummary`, `renderCards`, `renderTable`, `showDetail`
  * `src/db_hub.py` -> `query_games_by_gpu`, `query_game_benchmarks_with_pc`, `query_games_storage_summary`

### [FEATURE: AI-Model-Benchmark-And-Pricing-Matrix] | Aliases: ai matrix, frontier models, coding elo, token pricing, chinese oss
> **1-Line Summary:** Live tri-source verified 48-model strict current-gen AI pricing, Artificial Analysis v5 intelligence/speed/ELO, and origin tier matrix (`frontier`, `near_frontier`, `mid_tier`, `specialized`) decoupled from local VRAM.
* **User Intention (Non-Negotiable):** Track active 2026 frontier and top free/open-weights models directly from live **OpenRouter API**, **Models.dev**, and **Artificial Analysis** (pruning legacy 2024/early-2025 clutter and duplicate `model_matrix/` UI bundles), with dense multi-row readability, provider color-coding + zero-network geometric SVG logos, toggleable **Group by Provider**, collapsible Matrix/Task headings, non-overlapping provider-colored Pareto chart labels, and zero UTF-8 mojibake.
* **Visual / UI Behavior:** Labeled **`LLM`** in portal nav/status (`data/registry.json`), lives in `web/ai/index.html` fetching live `/api/ai`, supporting async **Refresh Live AI** (`POST /api/ai/refresh?async=true`) with progress bar/cancel, dense Multi-Row & Wide Single-Row table toggle across both benchmark and 30-Task tables, **Group by Provider** toggle (`MatrixTable.groupByProvider`), collapsible `<details>` accordions on Charts, Multi-Tier Matrix, and 30 Real-World Tasks, clickable chart provider legend, and Smart/All/Hover Pareto scatter labels (`aiScatterLabelsPlugin`).
* **Code Anchors (Grep Targets):**
  * `src/scrapers/multi_site_ai.py` -> `sync_multi_site_ai`, `parse_aa_leaderboard`, `start_background_ai_refresh`
  * `src/server.py` -> `/api/ai`, `/api/ai/refresh`, `/api/ai/refresh/status`
  * `src/catalog_classifier.py` -> `classify_ai_model`, `classify_ai_catalog`
  * `data/ai/models_master.json` -> `models`
  * `web/ai/index.html` -> `PROVIDER_THEMES`, `renderProviderIcon`, `aiScatterLabelsPlugin`, `MatrixTable`, `MatrixApp`

### [FEATURE: Media-Catalog-And-Adaptation-Hub] | Aliases: media domain, manga, manhua, light novel, anime, donghua, movie, tv_series
> **1-Line Summary:** Multi-tiered 147-franchise (381 sub-entry) media catalog uniting `light_novel`, `comic`, `anime`, `donghua`, `movie`, and `tv_series` via `franchise_id`/`parent_id`/`relations`, per-tier local poster caching, IMDb/AniList/MangaUpdates synopses, official/unofficial link pills, and toggleable 18+ NSFW filtering without external Obsidian markdown sync.
* **User Intention (Non-Negotiable):** Model full adaptation chains (Text Source -> Visual Comic -> Motion/Live-Action sub-entries, with distinct cards when multiple seasons/films/series exist) inside SQLite/JSON while preserving `Outlander` safely without private MEGA links, keeping 18+ NSFW entries toggleable (hidden by default), and caching downloaded posters locally inside gitignored storage.
* **Visual / UI Behavior:** Dashboard [web/media/index.html](file:///c:/Users/kazir/Documents/Agentic%20Harness/Database%20Manager/web/media/index.html) featuring a uniform-baseline 3-tier Franchise Matrix (`Tier 1: Text Source`, `Tier 2: Visual / Comic`, `Tier 3: Motion & Screen`) with prominent franchise/tier borders, chronological & per-subdomain latest sorting (`release_year`, `added_at`, `updated_at`), a Reddit-style collapsible nested thread tree (`Compact Reddit Tree` mode), per-card collapsible details (`hidden="until-found"`), native `<dialog>` poster & details lightbox, smooth per-entry Watch/Read status selector (`POST /api/media/status`), per-entry/franchise live link probing (`Check Links` / `Probe Links`), `Show NSFW / 18+` native switch, universal Collapse/Expand QoL controls, and async background `Refresh & Cache Posters` progress bar (`/api/media/refresh`).
* **Links:** `[SUBSYSTEM: Media-Catalog-And-Adaptation-Pipeline]`, `[DECISION: Multi-Tier-Media-Franchise-Graph-And-Local-Poster-Cache]`, `[TRAP: Manga-Jikan-And-JS-Rendered-Search-Pages]`
* **Verified By:** `tests/test_multidb_and_scrapers.py :: TestMediaDomainIntegration.test_media_multi_tier_nsfw_and_local_poster_cache` & `python src/media/cli.py --doctor --json`

### [FEATURE: Book-Collection-And-Reading-Tracker] | Aliases: book domain, books, learning, reading
> **1-Line Summary:** Personal library catalog (`books.json` / `book.sqlite`) tracking 3,618 books (13 curated books with Open Library covers + 3,605 sanitized `E:\Books` Alexandria Library volumes across 26 subjects, paired with gitignored `local_library.json` for EPUB cover extraction and direct file launching).
* **User Intention (Non-Negotiable):** Track owned vs wishlist vs active reading books alongside the entire 3,605-volume `E:\Books` Alexandria catalog without committing local machine paths or utility shortcuts to GitHub, while keeping labels and aliases in `data/registry.json` flexible enough to rename the domain (e.g. `Book` -> `Learning`) without code rewrites.
* **Visual / UI Behavior:** Safe-DOM paginated card view (`zero innerHTML`) in `web/book/index.html` with 2:3 book covers (extracted EPUB cover artwork via `/api/book/cover?id=...`, Open Library ISBN/cover ID art, and subject-colored hardcover SVG fallbacks), KPI summary strip, subject/source/ownership/reading/format filters, **Sync E:\Books Library** trigger, detail modal with **Open Local File**, and `/api/book` + `/api/domain/learning` alias routing.
* **Code Anchors (Grep Targets):**
  * `data/book/schema.json` -> book field contracts, cover/ISBN fields, and enums
  * `src/book_sync.py` -> `sync_alexandria_library`, `load_merged_book_payload`, `get_book_cover_bytes`, `open_local_book_file`
  * `src/db_export.py` -> `create_book_schema`, `export_books`
  * `web/book/index.html` -> `createCoverElement`, `openBookModal`, `renderCurrentPage`, `applyFilters`

### [FEATURE: Phone-Specs-And-App-Support-Catalog] | Aliases: phone domain, phones, mobile, smartphones
> **1-Line Summary:** Mobile device specifications catalog (`phones.json` / `phone.sqlite`) tracking SoC, GPU, RAM, display refresh rate, battery/charging, BD/USD pricing, device thumbnails, and verified `supported_games` (including mobile editions of Steam titles) / `supported_apps` compatibility lists.
* **User Intention (Non-Negotiable):** Compare smartphones visually and technically on hardware capability (Snapdragon/Exynos SoC, RAM, LTPO/AMOLED display, charging wattage) and real-world app/game compatibility profiles.
* **Visual / UI Behavior:** Safe-DOM dashboard (`zero innerHTML`) in `web/phone/index.html` with verified device hardware thumbnails + bespoke vector silhouette fallbacks, SoC/RAM/brand filters, dual supported games & supported apps badges (`locked`, `smooth`, `playable`, `supported`), and `/api/phone`.
* **Code Anchors (Grep Targets):**
  * `data/phone/schema.json` -> device spec ranges, `image_url`, and required fields
  * `src/db_export.py` -> `create_phone_schema`, `export_phones`
  * `web/phone/index.html` -> `createPhoneCoverBox`, `applyFilters`, `makeSupportBlock`

### [FEATURE: GitHub-Repositories-And-CI-Hub] | Aliases: github manager, repo triage, ci health, upstream fork drift, local sync, cliproxyapi
> **1-Line Summary:** DevOps domain (`github`) tracking repository activity timelines (0–4d, 4–8d, dormant), live async refresh progress bar + cancel + single-repo refresh, local-vs-web git drift/deletion reconciliation, CLIProxyAPI AI assistant with authenticated Google accounts, and Markdown audit exports.
* **User Intention (Non-Negotiable):** Track all repositories on port `8770`, redact private repo metadata and local workspace paths from committed `data/github/repos_public.json` into gitignored `live_cache.json`/`sync_state.json`, show immediate visual progress during live scans (plus detect outdated `server.py` processes on port `8770`), reconcile local folders against GitHub web for deletions/dirty state, connect securely via backend to local CLIProxyAPI (`127.0.0.1:8317/v1`), render strictly with safe DOM (`zero innerHTML`) in a GitHub Primer Dark layout, and guard all `POST` mutations with loopback `Origin`/`Host` CSRF checks.
* **Visual / UI Behavior:** Grouped `DevOps` tab or standalone `web/github/index.html` styled with GitHub.com Primer Dark tokens (`#0d1117`), Primer Repository List rows (language color dot, stars/forks, visibility & CI status pills, inline **Quick Resync** button) + Compact Table toggle, immediate `#refresh-progress-card` animation + cancel + stale-server warning flash banner, `Local Sync` tab with configurable roots, CLIProxyAPI status/account/model selector + AI Executive Report & Refresh Summary buttons, single-repo Inspect modal refresh, and Repo Doctor.
* **Code Anchors (Grep Targets):**
  * `src/github/scanner.py` -> `start_background_refresh`, `get_refresh_status`, `cancel_background_refresh`, `refresh_single_repository`, `run_local_sync_check`, `triage_repositories`
  * `src/github/local_sync.py` -> `scan_local_git_repos`, `reconcile_local_with_web`, `discover_default_roots`
  * `src/github/exporter.py` -> `export_markdown_report`
  * `src/agent_proxy.py` -> `discover_cliproxy_config`, `get_proxy_status`, `start_cliproxy_service`, `generate_github_ai_report`, `summarize_github_refresh`
  * `web/github/index.html` -> `renderPrimerList`, `handleQuickResync`, `renderRefreshProgress`, `startPollingRefreshStatus`, `checkServerCapabilities`

### [FEATURE: Registry-Driven-Dynamic-Portal-And-Isolated-SQLite] | Aliases: master dashboard, web portal, db hub, db export, table isolation, aliases, cross domain nav
> **1-Line Summary:** Dynamic grouped web portal (`web/index.html`) with `#home` Main Overview Hub + cross-domain AI ask bar, shared safe-DOM domain switcher bar (`web/shared/nav.js`), alias-aware domain resolver (`resolve_domain_key`), strictly table-isolated per-domain SQLite builds (`compile_separated_domains`), and cross-domain `games` <-> `pc` federation (`db_hub.py`).
* **User Intention (Non-Negotiable):** Let users move smoothly from the Main Overview Hub (`#home`) to any domain and directly between standalone domain pages without browser Back buttons, support painless domain renames (`display_name`, `short_label`, `aliases`, `group` in `data/registry.json`), guarantee every `data/<domain>/<domain>.sqlite` holds strictly its own tables + `_meta`, and retire pre-reorg legacy routes cleanly (`404`).
* **Visual / UI Behavior:** Default `#home` Overview Hub renders domain health cards + Global Cross-Domain AI Assistant (`POST /api/agent/ask`), top header renders group-clustered tabs + `0`–`7` keyboard shortcuts, and `web/shared/nav.js` injects a sticky cross-domain bar whenever a domain page is viewed standalone (hiding automatically inside iframes).
* **Code Anchors (Grep Targets):**
  * `data/registry.json` -> `groups`, `domains`, `cross_domain_views`
  * `src/db_export.py` -> `SCHEMA_CREATORS`, `compile_separated_domains`, `compile_database`
  * `src/db_hub.py` -> `open_federated_connection`, `query_domain_health`, `resolve_domain_key`
  * `src/agent_proxy.py` -> `ask_cross_domain_agent`
  * `src/server.py` -> `DatabaseHandler.do_GET`, `DatabaseHandler.do_POST`, `search_databases`
  * `web/index.html` -> `buildPortalChrome`, `renderOverviewHub`, `resolveTargetTab`
  * `web/shared/nav.js` -> `buildNav`, `initSharedNav`

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
