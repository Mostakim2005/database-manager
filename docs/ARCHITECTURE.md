# System Architecture & Visual Flows (`ARCHITECTURE.md`)
> **1-Line Summary:** Single living visual map of how Database Manager operates, its tech stack rationale, Obsidian-compatible subsystem flowcharts, and extension recipes.

## 1. High-Level Visual System Map
* **Plain-English Overview:** Database Manager combines a zero-dependency Python backend with standalone client-side web dashboards and a relational SQLite database. Users can inspect benchmarks, simulate game frame rates, or evaluate GPU power draw via the Web Portal or the Terminal CLI.

```mermaid
flowchart TB
    %% Color Definitions (Obsidian & GitHub compatible)
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef outputNode fill:#6b21a8,stroke:#581c87,color:#ffffff

    User([User / Developer]):::startNode -->|Browser HTTP / Port 8770| Portal[Web Portal / Dashboard]:::outputNode
    User -->|Terminal Commands| CLI[CLI Search & Server Engine]:::processNode

    subgraph Backend["Python Standard Library Services (src/)"]
        CLI -->|Serves Web & REST API| Server[server.py HTTP Server]:::processNode
        Compiler[db_export.py Compiler]:::processNode -->|Compiles & Indexes| SQLite[(database.sqlite)]:::dataNode
        Hub[db_hub.py Multi-DB Hub]:::processNode -->|In-Memory ATTACH Federation| SQLite
        Scrapers[src/scrapers/ Engine]:::processNode -->|Multi-tier fetch & diff| DataHW
        Compat[src/compatibility_engine.py]:::processNode -->|Build Rule Checks| Server
        Classifiers[src/catalog_classifier.py]:::processNode -->|Multi-axis taxonomies| Server
    end

    subgraph DataLayer["Multi-Domain Datasets (data/)"]
        DataAI[(data/ai/ — Models & Taxonomy)]:::dataNode
        DataGames[(data/games/ — Games & Benchmarks)]:::dataNode
        DataHW[(data/hardware/ — GPU & PSU Specs)]:::dataNode
        DataCPUs[(data/cpus/ — Desktop CPUs)]:::dataNode
        DataComp[(data/pc_components/ — Components)]:::dataNode
        DataManga[(data/manga/ — Manga & Adaptations)]:::dataNode
        Registry[data/registry.json — Domain Hub]:::dataNode
    end

    subgraph WebDashboards["Client-Side Visualizers (web/)"]
        Portal -->|Tab 1| AIView[AI Model Matrix]:::outputNode
        Portal -->|Tab 2| GameView[GameRank FPS Simulator]:::outputNode
        Portal -->|Tab 3| HWView[PSU Transient Guard]:::outputNode
        Portal -->|Tab 4| MangaView[Manga & Adaptations]:::outputNode
    end

    DataAI -->|Loaded by| Server
    DataGames -->|Loaded by| Server
    DataHW -->|Loaded by| Server
    DataCPUs -->|Loaded by| Server
    DataComp -->|Loaded by| Server
    DataManga -->|Loaded by| Server

    DataAI -->|Ingested by| Compiler
    DataGames -->|Ingested by| Compiler
    DataHW -->|Ingested by| Compiler
    DataCPUs -->|Ingested by| Compiler
    DataComp -->|Ingested by| Compiler
    DataManga -->|Ingested by| Compiler

    Server -->|JSON REST Endpoints| Portal

    subgraph Legend["Legend (Color Guide)"]
        L1([Blue = User Entrypoint]):::startNode
        L2[Teal = Python Processing & Server Engine]:::processNode
        L3[(Green = Master Datasets & SQLite Storage)]:::dataNode
        L4[Purple = Interactive Web Dashboards]:::outputNode
    end
```

## 2. Tech Stack & Why We Chose It

| Layer | Tool / Library | Plain-English Reason Why |
| :--- | :--- | :--- |
| **Backend & CLI** | Python 3.10+ (Standard Library) | `http.server`, `sqlite3`, and `json` require zero `pip install` steps, avoiding virtual environment bloat on the local PC. |
| **Relational Storage** | SQLite 3 | Embedded single-file database (`data/database.sqlite`) offering instant local querying and portability across machines. |
| **Web Interface** | Vanilla HTML5 / Modern CSS / ES6 | Fast, zero-build dashboards with glassmorphic UI, responsive tables, and zero runtime overhead. |
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
> **1-Line Summary:** Heuristic scoring engine evaluating 43 RTS games against Ryzen 5 5600GT hardware parameters and simulated GPU upgrades.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff

    G1[(data/games/games.json)]:::dataNode -->|Loads 43 records| G2[js/rank.js Scoring Engine]:::processNode
    G3[User selects GPU preset: Vega 7 / RX 6600]:::startNode -->|Inputs tier| G2
    G2 -->|Applies GPU margin + CPU/HDD penalties| G4[Calculates 0-100 Compatibility Score]:::processNode
    G4 -->|Assigns Great / OK / Struggle verdict| G5[js/render.js Card & Table View]:::startNode

    subgraph Legend["Legend"]
        L1[(Green = Game Database)]:::dataNode
        L2[Teal = Compatibility Heuristic]:::processNode
        L3[Blue = User Interaction & Verdict UI]:::startNode
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
    S4 -->|--apply| S6[Write hardware_specs.json & recompile]:::dataNode

    subgraph Legend["Legend"]
        L1[Blue = Target GPU & CLI Output]:::startNode
        L2[Teal = Multi-Tier HTTP & Parsing]:::processNode
        L3[Amber = Non-Destructive Diff Computation]:::diffNode
        L4[(Green = Persistent Catalog Storage)]:::dataNode
    end
```

### [SUBSYSTEM: Cross-Domain-Federated-Hub] | Aliases: db hub, in memory attach, cross domain views
> **1-Line Summary:** In-memory SQLite ATTACH federation combining domain databases into cross-domain analytical views.

* **Plain-English Overview:** Opens an in-memory SQLite connection, dynamically attaches all registered domain databases (`ai`, `games`, `hardware`, `cpus`), and creates cross-domain views (`v_games_by_gpu`, `v_local_ai_vram_fit`, `v_cpu_gpu_combos`) without duplicating tables.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff

    D1[data/registry.json]:::dataNode -->|Loads domain paths| F1[open_federated_connection]:::processNode
    F1 -->|ATTACH DATABASE| D2[(ai.sqlite, games.sqlite, hardware.sqlite, cpus.sqlite)]:::dataNode
    F1 -->|Installs| V1[Cross-Domain SQL Views]:::processNode
    V1 -->|v_games_by_gpu| Q1[Compatibility by GPU]:::startNode
    V1 -->|v_local_ai_vram_fit| Q2[VRAM Fit by GPU]:::startNode
    V1 -->|v_cpu_gpu_combos| Q3[CPU+GPU Build Combos]:::startNode

    subgraph Legend["Legend"]
        L1[(Green = Domain Database Files)]:::dataNode
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

### [SUBSYSTEM: Manga-Catalog-And-Adaptation-Pipeline] | Aliases: manga pipeline, comix sitemaps, link health, obsidian manhua sync
> **1-Line Summary:** Sitemap indexing, Chrome-impersonated adaptation probing, link-health verification, SQLite compilation, and non-destructive Obsidian vault synchronization for 104+ comic titles.

* **Plain-English Overview:** `src/manga/crawler.py` caches `comix.to` sitemaps locally (gitignored), `indexer.py` + `matcher.py` propose canonical series URLs, `adaptation_refresh.py` + `link_health.py` audit adaptations and URL health via `fetch_helper.py` (`curl_cffi` with `urllib` fallback), and `sync_vault.py` updates `Manhua Links.md` while keeping everything beneath `### Outlander` intact.

```mermaid
flowchart LR
    %% Color Definitions
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef dataNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef outNode fill:#6b21a8,stroke:#581c87,color:#ffffff

    M1[(data/manga/manga_catalog.json)]:::dataNode -->|Compiled by db_export.py| M2[(data/manga/manga.sqlite)]:::dataNode
    S1[comix.to Sitemaps & Public APIs]:::startNode -->|crawler.py & fetch_helper.py| P1[adaptation_refresh.py & link_health.py]:::processNode
    M1 -->|Read & Audited| P1
    P1 -->|Non-destructive Proposals| UI1[web/manga/index.html & /api/manga/*]:::outNode
    M1 -->|sync_vault.py preserving Outlander| OBS[Obsidian Manhua Links.md]:::outNode

    subgraph Legend["Legend"]
        L1[Blue = External Sitemaps & Sources]:::startNode
        L2[Teal = Fetch, Match & Health Pipeline]:::processNode
        L3[(Green = Catalog JSON & SQLite)]:::dataNode
        L4[Purple = Web Tab & Obsidian Sync]:::outNode
    end
```

## 4. Extension Recipes: Adding New Datasets

1. **Adding a New AI Model:**
   * Append model object to `data/ai/models_master.json` following the `scores` and `pricing` schema.
   * Run `python src/db_export.py` to refresh `data/database.sqlite`.

2. **Adding a New PC Game:**
   * Append game record to `data/games/games.json` (and mirror in `web/games/data/games.js`), then run `python src/db_export.py` to atomically rebuild `data/database.sqlite`.

3. **Adding a New GPU / Hardware Component:**
   * Add GPU entry to `data/hardware/hardware_specs.json` with TDP, tier, and local market prices.
   * Run `python src/db_export.py` to regenerate the relational table.

4. **Adding a New Domain Database (e.g. SSDs, Laptops, Monitors):**
   * Run `python src/db_export.py --init-domain <domain_name>` to scaffold `data/<domain_name>/`.
   * Define field rules in `data/<domain_name>/schema.json` and records in `data/<domain_name>/<domain_name>.json`.
   * Add export compiler function in `src/db_export.py` and run `python src/db_export.py` to compile `<domain_name>.sqlite`.
   * Run `python src/db_verify.py` to confirm zero errors and zero warnings across all domains.
