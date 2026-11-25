# System Architecture & Visual Flows (`ARCHITECTURE.md`)
> **1-Line Summary:** Single living visual map of how Database Manager operates, its tech stack rationale, Obsidian-compatible subsystem flowcharts, and extension recipes.

## 1. High-Level Visual System Map
* **Plain-English Overview:** Database Manager combines a zero-dependency Python backend with registry-driven, grouped web dashboards and isolated per-domain SQLite databases federated via `ATTACH DATABASE`. PC hardware is unified under `pc` (`79` parts across `12` categories) and deeply cross-linked with `games` (`153` unified owned Steam & wishlist titles across `12` genres), while `ai` remains strictly pricing/benchmark-focused (no local VRAM coupling), and `media`, `book`, `phone`, and `github` run cleanly in isolated tables.

```mermaid
flowchart TB
    %% Color Definitions (Obsidian & GitHub compatible)
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef outputNode fill:#6b21a8,stroke:#581c87,color:#ffffff

    User([User / Developer]):::startNode -->|HTTP / Port 8770| Portal[Dynamic Grouped Portal]:::outputNode
    User -->|Terminal Commands| CLI[CLI Search & Verify Tools]:::processNode

    subgraph Backend["Python Standard Library Services (src/)"]
        CLI -->|Serves Web & REST API| Server[server.py HTTP Server]:::processNode
        Compiler[db_export.py Compiler]:::processNode -->|Consolidated + Table-Isolated DBs| SQLite[(database.sqlite & data/*/*.sqlite)]:::dataNode
        Hub[db_hub.py Federated Hub]:::processNode -->|In-Memory ATTACH: games x pc| SQLite
        Scrapers[src/scrapers/ Engine]:::processNode -->|Multi-tier fetch & diff| DataPC
        Compat[src/compatibility_engine.py]:::processNode -->|Build & PSU Rules| Server
        Classifiers[src/catalog_classifier.py]:::processNode -->|AI, Games, Media, GitHub Taxonomies| Server
        MediaEngine[src/media/ Engine]:::processNode -->|Sitemaps, Doctor & Link Audit| DataMedia
        GitHubEngine[src/github/ Engine]:::processNode -->|gh api scan & triage| DataGitHub
    end

    subgraph DataLayer["7 Registered Grouped Datasets (data/)"]
        Registry[data/registry.json — Groups, Display Names & Aliases]:::dataNode
        DataPC[(data/pc/ — Unified CPUs, GPUs, PSUs & Peripherals)]:::dataNode
        DataGames[(data/games/ — RTS Games & benchmarks.csv)]:::dataNode
        DataAI[(data/ai/ — API Pricing, Intelligence & Tiers)]:::dataNode
        DataMedia[(data/media/ — Comics, Novels, Anime, Movies & Series)]:::dataNode
        DataBook[(data/book/ — Books & Reading Tracker)]:::dataNode
        DataPhone[(data/phone/ — Phone Specs, Supported Games & Apps)]:::dataNode
        DataGitHub[(data/github/ — Public Repos & Gitignored Cache)]:::dataNode
    end

    subgraph WebDashboards["Grouped Safe-DOM Web Views (web/)"]
        Portal -->|Group: PC & Gaming| PCView[PC & PSU Guard]:::outputNode
        Portal -->|Group: PC & Gaming| GameView[GameRank + PC GPU Link]:::outputNode
        Portal -->|Group: AI Models| AIView[AI Pricing & Matrix]:::outputNode
        Portal -->|Group: Media & Books| MediaView[Media & Adaptations]:::outputNode
        Portal -->|Group: Media & Books| BookView[Book Collection]:::outputNode
        Portal -->|Group: Mobile| PhoneView[Phone & Apps Matrix]:::outputNode
        Portal -->|Group: DevOps| GitHubView[GitHub Repos & CI]:::outputNode
    end

    Registry -->|Drives tabs, aliases & stats| Server
    DataPC <-->|GPU tiers & FPS benchmarks| DataGames
    DataPC --> Server
    DataGames --> Server
    DataAI --> Server
    DataMedia --> Server
    DataBook --> Server
    DataPhone --> Server
    DataGitHub --> Server

    DataPC --> Compiler
    DataGames --> Compiler
    DataAI --> Compiler
    DataMedia --> Compiler
    DataBook --> Compiler
    DataPhone --> Compiler
    DataGitHub --> Compiler

    Server -->|JSON REST Endpoints| Portal

    subgraph Legend["Legend (Color Guide)"]
        L1([Blue = User Entrypoint]):::startNode
        L2[Teal = Python Processing & Server Engine]:::processNode
        L3[(Green = Registry, Datasets & SQLite Storage)]:::dataNode
        L4[Purple = Registry-Driven Web Dashboards]:::outputNode
    end
```

## 2. Tech Stack & Why We Chose It

| Layer | Tool / Library | Plain-English Reason Why |
| :--- | :--- | :--- |
| **Backend & CLI** | Python 3.10+ (Standard Library) | `http.server`, `sqlite3`, `csv`, and `json` require zero `pip install` steps, avoiding virtual environment bloat on the local PC. |
| **Relational Storage** | SQLite 3 (Isolated + Consolidated) | Each domain compiles to its own table-isolated `data/<domain>/<domain>.sqlite` plus consolidated `data/database.sqlite`, joined cross-domain in memory via `ATTACH DATABASE`. |
| **Web Interface** | Vanilla HTML5 / Modern CSS / ES6 | Zero-build safe-DOM (`createElement` / `textContent`) dashboards dynamically structured from `data/registry.json` groups, `display_name`, and `aliases`. |
| **Visual Charts** | Chart.js (CDN / Bundled) | Lightweight canvas-based charting for Pareto frontier curves and transient power excursion meters. |
| **Verification & CI** | PowerShell + GitHub Actions | Dual verification paths: fast local sanity checks via `local-ci.ps1` and authoritative cloud runs via `ci.yml`. |

## 3. Core Subsystems & Visual Feature Flows

### [SUBSYSTEM: AI-Model-Matrix-Pipeline] | Aliases: ai pipeline, models dev, openrouter sync
> **1-Line Summary:** Data ingestion and normalized scoring flow for 26+ frontier AI models.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff

    A1[Upstream APIs: models.dev & OpenRouter]:::startNode -->|update_models.ps1| A2[JSON Schema Normalizer]:::processNode
    A2 -->|Writes| A3[(data/ai/models_master.json)]:::dataNode
    A3 -->|Loads into| A4[web/ai/model_matrix/app.js]:::processNode
    A4 -->|Renders| A5[Interactive Filter & Matrix View]:::startNode

    subgraph Legend["Legend"]
        L1[Blue = External / UI]:::startNode
        L2[Teal = Processing Logic]:::processNode
        L3[(Green = Storage)]:::dataNode
    end
```

### [SUBSYSTEM: GameRank-Compatibility-Engine] | Aliases: vega 7 simulator, game benchmark flow
> **1-Line Summary:** Heuristic scoring, Steam enrichment, 8-GPU progressive benchmark table (`benchmarks.csv`), and storage footprint engine evaluating 195 owned/wishlist PC & RTS games against Ryzen 5 5600GT hardware and simulated GPU/SSD upgrades.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff

    S0[Steam Store + Player + SteamSpy APIs]:::startNode -->|multi_site_games.py normalize & enrich| G1[(data/games/games.json)]:::dataNode
    B0[(data/games/benchmarks.csv 8-GPU Ladder)]:::dataNode -->|GET /api/games/benchmarks| G5
    G1 -->|Loads 195 records: 105 owned + 90 wishlist| G2[js/rank.js & Disk Footprint Advisor]:::processNode
    G3[User filters Ownership / Genre / GPU / Preset]:::startNode -->|Inputs filter + GPU tier| G2
    G2 -->|Applies GPU margin + CPU/HDD penalties| G4[Calculates 0-100 Score & SSD Recommendation]:::processNode
    G4 -->|Assigns Great / OK / Struggle + Storage Match| G5[js/render.js Card, Table & Progressive GPU Modal]:::startNode

    subgraph Legend["Legend"]
        L1[(Green = Unified Game & Benchmark Data)]:::dataNode
        L2[Teal = Compatibility & Storage Heuristic]:::processNode
        L3[Blue = Steam API & User Interaction UI]:::startNode
    end
```

### [SUBSYSTEM: PSU-Transient-Guard-Engine] | Aliases: psu excursion, spike calculator, ocp checker
> **1-Line Summary:** Physics-based electrical load and transient power spike calculator safeguarding 550W single-rail power supplies.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef passNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef failNode fill:#b91c1c,stroke:#7f1d1d,color:#ffffff

    H1[Candidate GPU Selected]:::startNode -->|Reads TDP| H2[Determine Excursion Multiplier: 1.35x / 1.65x / 2.0x]:::processNode
    H2 -->|Calculates| H3[Peak Spike = GPU TDP * Mult + 85W Base]:::processNode
    H3 -->|Compare against 550W PSU Limit| H4{Peak > 550W?}:::processNode
    H4 -->|No| H5[Status: Safe or Caution Badge]:::passNode
    H4 -->|Yes| H6[Status: OCP Trip Risk Warning]:::failNode

    subgraph Legend["Legend"]
        L1[Blue = Selection]:::startNode
        L2[Teal = Electrical Formula]:::processNode
        L3[Green = Headroom Safe]:::passNode
        L4[Red = Emergency Trip Risk]:::failNode
    end
```

### [SUBSYSTEM: Multi-Tier-Scraper-And-BD-Retail-Sync] | Aliases: scraper stack, bd retail sync, star tech scraper
> **1-Line Summary:** Multi-tier fallback architecture (Tier 1 httpx/selectolax -> Tier 0 urllib/regex) scraping retail pricing with non-destructive diff previews.

* **Plain-English Overview:** Fetches live product listings from local retailers (Star Tech, Ryans, UCC) for candidate GPUs, extracts prices with CSS selectors or regex, and computes changes against the catalog before writing.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef diffNode fill:#b45309,stroke:#78350f,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff

    S1[Target GPUs: RX 6600, RTX 4060, etc.]:::startNode -->|Fetch queries| S2[fetch_with_fallback]:::processNode
    S2 -->|Tier 1: httpx + selectolax| S3[Fast HTML Parsing]:::processNode
    S2 -->|Tier 0: urllib + regex fallback| S3
    S3 -->|Extracted Price BDT| S4[compute_record_diff]:::diffNode
    S4 -->|--dry-run| S5[Render Markdown Diff Table]:::startNode
    S4 -->|--apply| S6[Write data/pc/pc.json & recompile pc.sqlite]:::dataNode

    subgraph Legend["Legend"]
        L1[Blue = Target GPU & CLI Output]:::startNode
        L2[Teal = Multi-Tier HTTP & Parsing]:::processNode
        L3[Amber = Non-Destructive Diff Computation]:::diffNode
        L4[(Green = Persistent Catalog Storage)]:::dataNode
    end
```

### [SUBSYSTEM: Cross-Domain-Federated-Hub] | Aliases: db hub, in memory attach, cross domain views
> **1-Line Summary:** In-memory SQLite ATTACH federation joining isolated `pc.sqlite` and `games.sqlite` databases into `games` <-> `pc` views while keeping `ai` separate.

* **Plain-English Overview:** Opens an in-memory SQLite connection, dynamically attaches all compiled domain databases (`pc`, `games`, `ai`, `media`, `book`, `phone`, `github`), resolves aliases via `resolve_domain_key`, and creates strictly `games` <-> `pc` cross-domain views (`v_games_by_gpu`, `v_game_benchmarks_with_pc`, `v_cpu_gpu_combos`) without duplicating tables or coupling cloud AI models to local GPU VRAM.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff

    D1[data/registry.json]:::dataNode -->|Loads paths & aliases| F1[open_federated_connection]:::processNode
    F1 -->|ATTACH DATABASE| D2[(pc.sqlite & games.sqlite)]:::dataNode
    F1 -->|Installs| V1[Cross-Domain SQL Views]:::processNode
    V1 -->|v_games_by_gpu| Q1[Compatibility by GPU & 550W PSU]:::startNode
    V1 -->|v_game_benchmarks_with_pc| Q2[Measured FPS Benchmarks x GPU Specs]:::startNode
    V1 -->|v_cpu_gpu_combos| Q3[CPU+GPU Build Combos]:::startNode
    F1 -->|query_games_storage_summary| Q4[Owned/Wishlist GB vs PC SSDs & HDDs]:::startNode

    subgraph Legend["Legend"]
        L1[(Green = Isolated Domain DBs)]:::dataNode
        L2[Teal = SQLite In-Memory Engine]:::processNode
        L3[Blue = Cross-Domain Query Outputs]:::startNode
    end
```

### [SUBSYSTEM: Full-Rig-Compatibility-Validator] | Aliases: compatibility validator, pc build checker, peripheral guard
> **1-Line Summary:** Rule-based validation engine checking physical socket, RAM generation, PCIe bandwidth, PSU headroom, and peripheral cable constraints.

* **Plain-English Overview:** Validates complete PC component selections against physical, electrical, and bus constraints, warning about CPU-motherboard socket mismatches, DDR generation incompatibilities, drawing tablet display connections, and SMR storage lag.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef passNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef warnNode fill:#b45309,stroke:#78350f,color:#ffffff

    B1[Component Manifest: CPU, MB, RAM, GPU, PSU, Display]:::startNode -->|validate_pc_build| C1[Compatibility Engine]:::processNode
    C1 -->|Check Socket & RAM Gen| S1{Socket & DDR Match?}:::processNode
    C1 -->|Check TDP + Transients| P1{Peak Spike <= PSU?}:::processNode
    C1 -->|Check Peripheral Ports| D1{DP-Alt-Mode / Cable?}:::processNode
    S1 -->|Valid| R1[PASS: Mechanically Sound]:::passNode
    P1 -->|Within Limit| R1
    D1 -->|Port Note / Advice| R2[NOTE: Cable Guidance Emitted]:::warnNode

    subgraph Legend["Legend"]
        L1[Blue = Build Input]:::startNode
        L2[Teal = Validation Rules]:::processNode
        L3[Green = Verified Compatible]:::passNode
        L4[Amber = Advisory Warning]:::warnNode
    end
```

### [SUBSYSTEM: Multi-Axis-Catalog-Taxonomy-Engine] | Aliases: catalog taxonomy, llm classifier, rts taxonomy
> **1-Line Summary:** Multi-axis taxonomy classifier categorizing AI models by geopolitical origin/capability and games by tactical pacing.

* **Plain-English Overview:** Analyzes catalog entries against structured taxonomies (`data/ai/taxonomy.json`, `data/games/taxonomy.json`) to tag AI models into Chinese OSS vs Western Frontier tiers and classify strategy titles into micro, macro, and 4X subgenres.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef outNode fill:#6b21a8,stroke:#581c87,color:#ffffff

    M1[(data/ai/models_master.json)]:::dataNode -->|classify_ai_models| T1[src/catalog_classifier.py]:::processNode
    G1[(data/games/games.json)]:::dataNode -->|classify_games| T1
    X1[(data/*/taxonomy.json)]:::dataNode -->|Taxonomy Rules| T1
    T1 -->|--ai --chinese-oss| O1[Chinese OSS Tiers: DeepSeek, Qwen, GLM, Yi]:::outNode
    T1 -->|--games| O2[RTS Subgenres: Micro RTS, Macro RTS, 4X]:::outNode

    subgraph Legend["Legend"]
        L1[(Green = Catalog & Taxonomy Files)]:::dataNode
        L2[Teal = Classifier Engine]:::processNode
        L3[Purple = Classified Tiers & Subgenres]:::outNode
    end
```

### [SUBSYSTEM: Multi-Site-Scraping-Pipeline] | Aliases: multi site scrapers, retail reconciliation, fallback tiers
> **1-Line Summary:** Multi-tier scraper architecture reconciling live pricing, hardware specifications, and LLM telemetry across 3+ independent sources per domain.

* **Plain-English Overview:** Fetches live pricing and specs across Star Tech, Ryans, UCC BD, Steam Store API, PCGamingWiki, OpenRouter API, and Models.dev. Automatically falls back from Tier 0 (stdlib) to Tier 1 (httpx + selectolax lexbor) and Tier 2 (Scrapling stealth). Computes price spread deltas and prompts confirmation before persisting via `--apply`.

```mermaid
flowchart TD
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef alertNode fill:#b91c1c,stroke:#7f1d1d,color:#ffffff

    S1[External Sources: BD Retailers / Steam / OpenRouter]:::startNode -->|Tier 0 / Tier 1 / Tier 2 Probe| F1[src/scrapers/base.py]:::processNode
    F1 -->|Parse HTML / JSON API| M1[src/scrapers/multi_site_*.py]:::processNode
    M1 -->|Cross-Source Reconciliation| R1{Price Spread >20%?}:::processNode
    R1 -->|Yes: SKU Mismatch Risk| A1[Flag spread_alert & Log Review]:::alertNode
    R1 -->|No: Concordant| D1[Compute Best Retailer & Lowest BDT]:::processNode
    A1 --> V1[--dry-run Diff Preview]:::processNode
    D1 --> V1
    V1 -->|Validate schema.json| P1[--apply Write Gate]:::processNode
    P1 -->|Compile Atomically| DB[(data/*.sqlite Databases)]:::dataNode

    subgraph Legend["Legend"]
        L1[Blue = External Web & API Targets]:::startNode
        L2[Teal = Scraping & Normalization Pipeline]:::processNode
        L3[Red = Cross-Site Spread Alert]:::alertNode
        L4[(Green = Compiled SQLite Databases)]:::dataNode
    end
```

### [SUBSYSTEM: Media-Catalog-And-Adaptation-Pipeline] | Aliases: media pipeline, manga, manhua, light_novel, anime, donghua, movie, tv_series, comix sitemaps
> **1-Line Summary:** Sitemap indexing, Chrome-impersonated adaptation probing, link-health verification, and interconnected franchise graph compilation (`media.sqlite`) without external Obsidian markdown sync.

* **Plain-English Overview:** `src/media/crawler.py` caches `comix.to` sitemaps locally (gitignored), `indexer.py` + `matcher.py` propose canonical series URLs, and `adaptation_refresh.py` + `link_health.py` audit adaptations and URL health via `fetch_helper.py` (`curl_cffi` with `urllib` fallback). Interconnected subdomains (`comic`, `light_novel`, `anime`, `donghua`, `movie`, `tv_series`) share `franchise_id` and `relations` links inside `data/media/media_catalog.json` (including public `Outlander` TV series tracking without private MEGA URLs), replacing the retired Obsidian markdown sync.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef outNode fill:#6b21a8,stroke:#581c87,color:#ffffff

    M1[(data/media/media_catalog.json)]:::dataNode -->|Compiled by db_export.py| M2[(data/media/media.sqlite)]:::dataNode
    S1[comix.to Sitemaps & Public APIs]:::startNode -->|crawler.py & fetch_helper.py| P1[adaptation_refresh.py & link_health.py]:::processNode
    M1 -->|Read & Audited| P1
    P1 -->|Franchise Relations & Proposals| UI1[web/media/index.html & /api/media/*]:::outNode

    subgraph Legend["Legend"]
        L1[Blue = External Sitemaps & Sources]:::startNode
        L2[Teal = Fetch, Match & Health Pipeline]:::processNode
        L3[(Green = Unified Media JSON & SQLite)]:::dataNode
        L4[Purple = Franchise Explorer & API]:::outNode
    end
```

### [SUBSYSTEM: Book-And-Phone-Catalog-Domains] | Aliases: book domain, phone domain, learning alias, mobile games matrix
> **1-Line Summary:** Table-isolated storage, schema contracts, REST APIs, and safe-DOM UIs for personal book tracking (`book`) and smartphone specs/supported apps (`phone`).

* **Plain-English Overview:** `db_export.py` compiles `data/book/books.json` into isolated `data/book/book.sqlite` (`books` + `_meta`) and `data/phone/phones.json` into `data/phone/phone.sqlite` (`phones` + `_meta`). Both domains support alias lookup via `/api/domain/<alias>` (e.g. `learning` -> `book`) and render via safe-DOM dashboards in `web/book/index.html` and `web/phone/index.html`.

```mermaid
flowchart LR
    %% Color Definitions
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef outNode fill:#6b21a8,stroke:#581c87,color:#ffffff

    B1[(data/book/books.json)]:::dataNode -->|export_books| B2[(data/book/book.sqlite)]:::dataNode
    P1[(data/phone/phones.json)]:::dataNode -->|export_phones| P2[(data/phone/phone.sqlite)]:::dataNode
    B2 -->|GET /api/book or /api/domain/learning| BUI[web/book/index.html]:::outNode
    P2 -->|GET /api/phone| PUI[web/phone/index.html]:::outNode

    subgraph Legend["Legend"]
        L1[(Green = JSON Catalog & Isolated SQLite)]:::dataNode
        L2[Purple = Safe-DOM Dashboards]:::outNode
        L3[Teal = Schema Exporter]:::processNode
    end
```

### [SUBSYSTEM: GitHub-Repo-Triage-And-CI-Hub] | Aliases: github manager, repo triage, ci health, fork drift, local sync, cliproxyapi
> **1-Line Summary:** Async `gh api` scanner with live progress/cancel/single-repo refresh, local-vs-web git drift reconciliation (`local_sync.py`), backend CLIProxyAPI (`127.0.0.1:8317/v1`) AI assistant (`agent_proxy.py`), privacy redaction, safe DOM DevOps UI, and SQLite export.

* **Plain-English Overview:** `src/github/scanner.py` runs async or blocking `gh api` scans with 15-second timeouts, real-time per-repo progress polling (`/api/github/refresh/status`), cancellation, and single-repo quick refresh. `src/github/local_sync.py` scans local Git roots (`GIT_TERMINAL_PROMPT=0`) to flag local-only, web-only, dirty, ahead/behind, and newly deleted repos, persisting private/local telemetry strictly in gitignored `data/github/live_cache.json` and `sync_state.json`. `src/agent_proxy.py` connects securely on loopback to CLIProxyAPI (`ecosystem-registry.json -> 127.0.0.1:8317/v1`) and authenticated Google/Antigravity accounts (`~/.cli-proxy-api/`) to generate AI executive reports and cross-domain Q&A, while `web/shared/nav.js` and `web/index.html` (`#home` Overview Hub) provide one-click navigation across all 7 domains.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef outNode fill:#6b21a8,stroke:#581c87,color:#ffffff

    GHCLI[GitHub API via gh CLI]:::startNode -->|Async + Progress Lock| SCAN[src/github/scanner.py]:::processNode
    LOC[Local Git Roots] -->|local_sync.py| SYNC[Local vs Web Diff Engine]:::processNode
    SCAN -->|Full local incl. private| LIVE[(data/github/live_cache.json + sync_state.json gitignored)]:::dataNode
    SYNC --> LIVE
    PUB[(data/github/repos_public.json)]:::dataNode -->|Compiled by db_export.py| SQL[(data/github/github.sqlite)]:::dataNode
    LIVE -->|Fallback to repos_public.json| TRI[triage_repositories & doctor]:::processNode
    PUB --> TRI
    PROXY[CLIProxyAPI :8317 + Google OAuth]:::startNode -->|agent_proxy.py| TRI
    TRI -->|GET + CSRF-guarded POST| UI[web/github/index.html + shared/nav.js]:::outNode
    TRI -->|exporter.py + AI Report| RPT[Downloads Markdown Audit Reports]:::outNode

    subgraph Legend["Legend"]
        L1[Blue = GitHub API, Local Git & CLIProxyAPI]:::startNode
        L2[Teal = Scanner, Local Diff & Triage Engine]:::processNode
        L3[(Green = Public JSON, Gitignored State & SQLite)]:::dataNode
        L4[Purple = Safe DOM Dashboard & Downloads Report]:::outNode
    end
```

## 4. Extension Recipes: Adding or Renaming Datasets

1. **Adding a New AI Model:**
   * Append model object to `data/ai/models_master.json` following the `scores`, `pricing`, and `classification` schema.
   * Run `python src/db_export.py` to refresh `data/database.sqlite` and `data/ai/ai.sqlite`.

2. **Adding a New PC Game or Benchmark Run:**
   * Append game record to `data/games/games.json` (and mirror in `web/games/data/games.js` & `data/games/games.js`), and always populate `data/games/benchmarks.csv` for all 8 canonical GPUs in `data/games/taxonomy.json -> benchmark_gpu_ladder` (`vega-7-igpu`, `rx-580-8gb`, `gtx-1660-super`, `rtx-2060-super`, `rx-6600`, `rtx-2070`, `rtx-3060`, `rtx-2070-super`) paired with `AMD Ryzen 5 5600GT`.
   * Run `python src/db_export.py` to rebuild `games.sqlite` and `v_game_benchmarks_with_pc`.

3. **Adding a New PC Part / GPU / CPU / PSU:**
   * Add entry into the appropriate category array inside `data/pc/pc.json` and run `python src/db_export.py` + `python src/db_verify.py --domain pc`.

4. **Renaming a Domain Display Label or Adding Aliases (`Book` -> `Learning`):**
   * Edit `display_name`, `short_label`, `unit_label`, `aliases`, or `group` in `data/registry.json` — the dynamic web portal (`web/index.html`), `/api/domains`, `/api/status`, `/api/domain/<alias>`, and `db_verify.py` pick up the new label with zero source-code edits.

5. **Adding a New Domain Database (e.g. SSDs, Laptops, Courses):**
   * Run `python src/db_export.py --init-domain <domain_name>` to scaffold `data/<domain_name>/`.
   * Define field rules in `data/<domain_name>/schema.json` (using `[min, max]` arrays for `ranges`) and records in `data/<domain_name>/<domain_name>.json`.
   * Register an isolated schema creator and exporter in `src/db_export.py` (`SCHEMA_CREATORS`) and run `python src/db_export.py` + `python src/db_verify.py`.
