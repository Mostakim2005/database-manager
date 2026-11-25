# Project Operating Instructions (`AGENTS.md`)
> **Notice:** This project inherits user persona, confirmation gates, OS-default vs. Shared Libraries/Ecosystem Registry rules, GitHub-first CI/CD defaults, Top-Secret Local-Only rules, on-demand `AUDITS.md`/`UIUX.md` and Downloads-folder disposable report routing, pre-commit doc sync, visual standards, and documentation blueprints from the global master `AGENTS.md`. Do not duplicate those rules here.

## 1. Repository Classification & Tech Stack
* **Verification Mode:** `[GitHub-First (Remote Configured)]`
* **Remote Repository:** `https://github.com/Mostakim2005/database-manager`
* **Runtime / Language:** Python 3.10+ (Standard Library only), Node.js v20+ / ES6 (for web components & parsers)
* **Framework / Host:** Built-in `http.server` + Vanilla HTML5/CSS3/ES6 Dashboards + SQLite3
* **Target OS / Build Output:** Cross-platform local web portal (`http://127.0.0.1:8770`), Terminal CLI (`python src/server.py --cli`), and Windows launch scripts (`start-server.bat`, `run-cli.bat`)
* **Shared Libraries & Local Ports:** Local HTTP server port `8770`.

## 2. Verification & Build Commands (Mirrored in CI)
* **CLI Smoke Test:** `python src/server.py --cli` (or `--cli "claude" --json`)
* **Unit & Regression Tests:** `python -m unittest discover -s tests -v`
* **SQLite Compilation & Verification:** `python src/db_export.py --verify` & `python src/db_verify.py` (supports aliases, e.g. `--domain learning`)
* **Domain Scaffold & Scraper Stack Probe:** `python src/db_export.py --init-domain <name>` & `python src/scrapers/test_stack.py`
* **Live Scraper Probing & BD Retail Sync:** `python src/scrapers/test_stack.py --live --dry-run` & `python src/scrapers/bd_hardware.py --dry-run`
* **Game Benchmark Ingest:** `python src/scrapers/benchmark_ingest.py --verify`
* **Compatibility Engine & Catalog Classifiers:** `python src/compatibility_engine.py --demo` & `python src/catalog_classifier.py --ai --chinese-oss` & `python src/catalog_classifier.py --media` & `python src/catalog_classifier.py --github`
* **Media Catalog, Refresh & Link Health CLI:** `python src/media/cli.py --verify --json`, `python src/media/cli.py --doctor --json`, `python src/media/cli.py --check-links`
* **GitHub Repositories & CI Health CLI:** `python src/github/cli.py --verify --json`, `python src/github/cli.py --doctor --json`, `python src/github/cli.py --check-local --json`, `python src/github/cli.py --export`
* **Python Syntax Check:** `python -m py_compile src/server.py src/agent_proxy.py src/db_export.py src/db_hub.py src/db_verify.py src/scrapers/base.py src/scrapers/adapters.py src/scrapers/test_stack.py src/scrapers/bd_hardware.py src/scrapers/benchmark_ingest.py src/scrapers/multi_site_components.py src/scrapers/multi_site_games.py src/scrapers/multi_site_ai.py src/compatibility_engine.py src/catalog_classifier.py src/media/__init__.py src/media/fetch_helper.py src/media/crawler.py src/media/indexer.py src/media/matcher.py src/media/adaptation_refresh.py src/media/link_health.py src/media/cli.py src/github/__init__.py src/github/local_sync.py src/github/scanner.py src/github/exporter.py src/github/cli.py`
* **JSON Schema Verification:** `python -c "import json; json.load(open('data/registry.json', encoding='utf-8')); json.load(open('data/pc/pc.json', encoding='utf-8')); json.load(open('data/games/games.json', encoding='utf-8')); json.load(open('data/ai/models_master.json', encoding='utf-8')); json.load(open('data/media/media_catalog.json', encoding='utf-8')); json.load(open('data/book/books.json', encoding='utf-8')); json.load(open('data/phone/phones.json', encoding='utf-8')); json.load(open('data/github/repos_public.json', encoding='utf-8')); json.load(open('data/ai/taxonomy.json', encoding='utf-8')); json.load(open('data/games/taxonomy.json', encoding='utf-8'))"`
* **Local Verification Runner:** `powershell -NoProfile -ExecutionPolicy Bypass -File .\local-ci.ps1`

## 3. Repository Directory Structure & Conventions
* `data/` - Normalized master datasets across 7 registered domains (`groups`, `display_name`, `aliases` defined in `registry.json`):
  * `data/pc/` - Unified PC hardware catalog (82 parts across 12 categories: CPUs, 15 GPUs incl. Steam Ref GTX 1060 / RX 580 + RTX 2060 Super / 2070 / 2070 Super, motherboards, RAM, SSDs incl. 2TB/4TB NVMe, HDDs, PSUs, displays, peripherals) + `psu` transient excursion rules (`pc.json`, `schema.json`).
  * `data/games/` - Unified PC & strategy games database (`163` titles: `105` owned Steam + `58` wishlist), `155` measured/projected benchmark rows across the canonical 8-GPU progressive ladder (`benchmarks.csv`), GPU/storage compatibility links, and taxonomy (`games.json`, `games.js`, `taxonomy.json`, `schema.json`).
    * **Mandatory Game Benchmark Update Rule:** Whenever adding new games or updating game benchmarks in the future, always populate/update benchmark telemetry for the user's PC (`AMD Ryzen 5 5600GT` + `vega-7-igpu`) AND all 7 progressive upgrade GPUs (`rx-580-8gb`, `gtx-1660-super`, `rtx-2060-super`, `rx-6600`, `rtx-2070`, `rtx-3060`, `rtx-2070-super`) defined in `data/games/taxonomy.json -> benchmark_gpu_ladder`.
  * `data/ai/` - AI model pricing, benchmarks, tiers, and origin taxonomy (`models_master.*`, `taxonomy.json`, `raw_api_dumps/`). Decoupled from local VRAM hardware.
  * `data/media/` - Interconnected Media & Adaptations catalog (`media_catalog.json`, `schema.json`, gitignored `sitemaps/*.xml`) covering comics, light novels, anime, donghua, movies, and TV series.
  * `data/book/` - Book collection & reading tracker (`books.json`, `schema.json`), rename-ready with `learning`/`reading` aliases.
  * `data/phone/` - Mobile phone specifications & supported games/apps matrix (`phones.json`, `schema.json`).
  * `data/github/` - Sanitized public GitHub repository snapshot (`repos_public.json`, `schema.json`, gitignored `live_cache.json`, `sync_state.json`, `local_roots.json`).
  * `data/registry.json` - Central registry with domain groups (`pc_gaming`, `ai_models`, `media_knowledge`, `mobile`, `devops`), `display_name`, `short_label`, `aliases`, and cross-domain views (`games` <-> `pc`).
* `web/` - Registry-driven dynamic portal and safe-DOM domain dashboards:
  * `web/index.html` - Dynamic grouped Portal + `#home` Main Overview Hub with Cross-Domain AI Ask Bar reading `/api/status` & `/api/domains`.
  * `web/shared/nav.js` - Safe-DOM sticky global domain switcher bar injected on standalone domain pages (hidden inside portal iframes).
  * `web/pc/` - Unified PC Parts, CPUs, GPUs & PSU Transient Guard + compatibility build checker.
  * `web/games/` - GameRank cards & table simulator using canonical `pc` GPU keys.
  * `web/ai/` - Interactive AI Model Matrix visualizer (pricing, intelligence, coding ELO).
  * `web/media/` - Media & Adaptations explorer, franchise relation chips, doctor, and link audit view.
  * `web/book/` - Book & Reading tracker UI (safe DOM only).
  * `web/phone/` - Phone Specs & Supported Games/Apps UI (safe DOM only).
  * `web/github/` - GitHub Repositories, CI health, upstream drift, and report export view (safe DOM only).
* `src/` - Server, CLI, and data processing utilities:
  * `src/server.py` - Standard library HTTP web server on port `8770`, async refresh/local-sync endpoints, CLIProxyAPI proxy routes, and multi-domain CLI search engine.
  * `src/agent_proxy.py` - CLIProxyAPI (`127.0.0.1:8317/v1`) and Google/Antigravity account status discovery, auto-launcher, and AI report/summary/Q&A client.
  * `src/db_export.py` - Consolidated (`data/database.sqlite`) and strictly table-isolated per-domain (`data/<domain>/<domain>.sqlite`) SQLite compilation pipeline.
  * `src/db_hub.py` - In-memory SQLite ATTACH federation (`games` <-> `pc` views) and alias resolution (`resolve_domain_key`).
  * `src/db_verify.py` - Domain schema integrity (`required_by_category`, types, enums, `[min, max]` ranges) and alias resolver.
  * `src/compatibility_engine.py` - Full PC component and peripheral compatibility validator reading `data/pc/pc.json`.
  * `src/catalog_classifier.py` - Multi-axis taxonomy classifiers for AI models, PC games, media entries, and GitHub repos.
  * `src/media/` - Media sitemap crawler, matcher, adaptation refresher, link health checker (`cli.py`, `fetch_helper.py`, `crawler.py`, `indexer.py`, `matcher.py`, `adaptation_refresh.py`, `link_health.py`).
  * `src/github/` - GitHub `gh api` scanner with live progress/cancel/single-repo refresh, local-vs-web git reconciliation (`local_sync.py`), activity/CI/fork triage, Markdown report exporter, and CLI (`scanner.py`, `local_sync.py`, `exporter.py`, `cli.py`).
  * `src/scrapers/` - Multi-tier scraping stack (`base.py`, `adapters.py`, `test_stack.py`, `bd_hardware.py`, `benchmark_ingest.py`, `multi_site_*`).
  * `src/update_models.ps1` - Upstream AI benchmark data fetcher and normalizer.
  * `src/hardware_planner_obsidian/` - Complete archived Obsidian plugin source for PC hardware planning.
* `docs/` - Core Markdown documentation suite (`PRODUCT.md`, `ARCHITECTURE.md`, `DECISIONS_AND_TRAPS.md`). Scan with `grep -A 1 "^### \[" docs/`.
* `local-ci.ps1` - Local verification runner emitting patch-ready failure reports directly to `%USERPROFILE%\Downloads\`.

## 4. Critical Trap Pointers (1-Line Warnings Only)
* **TRAP 1:** Never parse context tokens with naive `int()` without handling '1M' or '200k' suffix strings — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: String-Suffix-Context-Window-Parsing]`.
* **TRAP 2:** High-TDP GPUs (>= 250W) cause 2.0x microsecond transient excursions that trip 550W PSU OCP — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: High-TDP-Transient-Power-Spikes]`.
* **TRAP 3:** Never redirect binary streams in PowerShell when updating models — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Binary-Redirection-Encoding-In-Powershell]`.
* **TRAP 4:** Effort simulation deltas must normalize `ultra` vs `ultra_high` schema keys to prevent NaN scores — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Effort-Simulation-Key-Mismatch]`.
* **TRAP 5:** In selectolax 1.0+, use `selectolax.lexbor.LexborHTMLParser` to avoid deprecated Modest backend — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Selectolax-Lexbor-Deprecation-In-Python-3-13-Plus]`.
* **TRAP 6:** Star Tech price spans concatenate `.price-new` and `.price-old` into merged numbers unless targeting `.price-new` first — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Star-Tech-Price-Span-Concatenation]`.
* **TRAP 7:** SQLite parameter binding rejects Python dictionaries; serialize objects with `json.dumps()` — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: SQLite-Dict-Parameter-Binding-Error]`.
* **TRAP 8:** Budget motherboards lack USB-C DP-Alt-Mode; route drawing pen displays via 3-in-1 HDMI + USB to GPU — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Motherboard-USB-C-DP-Alt-Mode-Absence]`.
* **TRAP 9:** SMR hard drives cause severe IO-wait stutter and game freezes; keep games on NVMe SSD or CMR drives — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: SMR-HDD-Gaming-IOWait-Freezes]`.
* **TRAP 10:** Sanitize JSON lowercase booleans to Python `True`/`False` to prevent `NameError: name 'true' is not defined` — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: JavaScript-Booleans-In-Python-Dictionaries]`.
* **TRAP 11:** Flag price spreads >20% across retailers as `spread_alert` for SKU mismatch check — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Multi-Site-Retailer-Price-Spread-SKU-Mismatch]`.
* **TRAP 12:** Filter YouTube description regex to benchmark keywords to prevent refresh rates from corrupting FPS — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: YouTube-Description-FPS-Regex-Noise]`.
* **TRAP 13:** Never call `.is_integer()` directly on `int` types in Python 3.11 CI — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Int-Object-Has-No-Attribute-Is-Integer-Python-3-11]`.
* **TRAP 14:** `api.jikan.moe` times out from this host and Viki/iQIYI return JS-rendered HTTP 200 shells — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Manga-Jikan-And-JS-Rendered-Search-Pages]`.
* **TRAP 15:** Obsidian markdown sync was retired; keep private MEGA links out of public `data/media/media_catalog.json` — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Obsidian-Manhua-Vault-Outlander-Preservation]`.
* **TRAP 16:** Never commit `data/github/live_cache.json` or raw private repo metadata into public `repos_public.json` — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: GitHub-Live-Cache-Private-Repo-Leak]`.
* **TRAP 17:** Guard `latest_run` and `conclusion` against `None` in GitHub exporters/triage — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: GitHub-Latest-Run-And-Conclusion-None]`.
* **TRAP 18:** Compare `recent_commits` HEAD date against `pushed_at` to avoid false-active triage on metadata bumps like `dataview-fork` — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Dataview-Fork-Push-Timestamp-Anomaly]`.
* **TRAP 19:** `db_verify.py` unpacks `ranges` entries as `[min, max]` arrays rather than `{min, max}` objects — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Schema-Json-Range-Bounds-Must-Be-Arrays]`.
* **TRAP 20:** Steam `storesearch` ranks sequels ahead of exact matches and delisted/bundled apps omit `price_overview` — see `docs/DECISIONS_AND_TRAPS.md` -> `[TRAP: Steam-Storesearch-Sequel-Ranking-And-Bundle-Prices]`.
