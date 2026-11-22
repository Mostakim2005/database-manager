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
* **SQLite Compilation & Verification:** `python src/db_export.py --verify` & `python src/db_verify.py`
* **Domain Scaffold & Scraper Stack Probe:** `python src/db_export.py --init-domain <name>` & `python src/scrapers/test_stack.py`
* **Live Scraper Probing & BD Retail Sync:** `python src/scrapers/test_stack.py --live --dry-run` & `python src/scrapers/bd_hardware.py --dry-run`
* **Game Benchmark Ingest:** `python src/scrapers/benchmark_ingest.py --verify`
* **Compatibility Engine & Catalog Classifiers:** `python src/compatibility_engine.py --demo` & `python src/catalog_classifier.py --ai --chinese-oss`
* **Python Syntax Check:** `python -m py_compile src/server.py src/db_export.py src/db_hub.py src/db_verify.py src/scrapers/base.py src/scrapers/adapters.py src/scrapers/test_stack.py src/scrapers/bd_hardware.py src/scrapers/benchmark_ingest.py src/scrapers/multi_site_components.py src/scrapers/multi_site_games.py src/scrapers/multi_site_ai.py src/compatibility_engine.py src/catalog_classifier.py`
* **JSON Schema Verification:** `python -c "import json; json.load(open('data/hardware/hardware_specs.json', encoding='utf-8')); json.load(open('data/games/games.json', encoding='utf-8')); json.load(open('data/ai/models_master.json', encoding='utf-8')); json.load(open('data/cpus/cpus.json', encoding='utf-8')); json.load(open('data/pc_components/components.json', encoding='utf-8')); json.load(open('data/ai/taxonomy.json', encoding='utf-8')); json.load(open('data/games/taxonomy.json', encoding='utf-8'))"`
* **Local Verification Runner:** `powershell -NoProfile -ExecutionPolicy Bypass -File .\local-ci.ps1`

## 3. Repository Directory Structure & Conventions
* `data/` - Normalized master datasets across registered domains:
  * `data/ai/` - AI model benchmark catalogs and taxonomy (`models_master.*`, `taxonomy.json`, `raw_api_dumps/`).
  * `data/games/` - PC strategy/RTS benchmark database and taxonomy (`games.js`, `games.json`, `taxonomy.json`, `benchmarks.csv`).
  * `data/hardware/` - PC hardware specs, GPU upgrade tiers, and PSU transient excursion tables (`hardware_specs.*`).
  * `data/cpus/` - Desktop processor specifications and socket architectures (`cpus.json`, `schema.json`).
  * `data/pc_components/` - Full PC rigs and peripherals catalog (`components.json`, `schema.json`).
  * `data/registry.json` - Domain registry and health monitoring ledger.
* `web/` - Multi-tabbed dashboard interface:
  * `web/index.html` - Unified Portal integrating AI, Game, and Hardware views.
  * `web/ai/` - Interactive AI Model Matrix visualizer and visual explorer.
  * `web/games/` - GameRank cards & table simulator.
  * `web/hardware/` - PC Hardware & PSU Transient Guard calculator.
* `src/` - Server, CLI, and data processing utilities:
  * `src/server.py` - Standard library HTTP web server on port `8770` and multi-domain CLI search engine.
  * `src/db_export.py` - Consolidated and multi-domain SQLite compilation pipeline.
  * `src/db_hub.py` - In-memory SQLite ATTACH federation and cross-domain analytical query views.
  * `src/db_verify.py` - Domain schema integrity, constraint, and foreign key verifier.
  * `src/compatibility_engine.py` - Full PC component and peripheral compatibility validator.
  * `src/catalog_classifier.py` - Multi-axis taxonomy classifiers for AI models and PC games.
  * `src/scrapers/` - Multi-tier scraping stack (`base.py`, `adapters.py`, `test_stack.py`, `bd_hardware.py`, `benchmark_ingest.py`).
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
