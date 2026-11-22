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
    end

    subgraph DataLayer["Unified Master Datasets (data/)"]
        DataAI[(data/ai/ — Models Master)]:::dataNode
        DataGames[(data/games/ — RTS Database)]:::dataNode
        DataHW[(data/hardware/ — GPU & PSU Specs)]:::dataNode
    end

    subgraph WebDashboards["Client-Side Visualizers (web/)"]
        Portal -->|Tab 1| AIView[AI Model Matrix]:::outputNode
        Portal -->|Tab 2| GameView[GameRank FPS Simulator]:::outputNode
        Portal -->|Tab 3| HWView[PSU Transient Guard]:::outputNode
    end

    DataAI -->|Loaded by| Server
    DataGames -->|Loaded by| Server
    DataHW -->|Loaded by| Server

    DataAI -->|Ingested by| Compiler
    DataGames -->|Ingested by| Compiler
    DataHW -->|Ingested by| Compiler

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

## 4. Extension Recipes: Adding New Datasets

1. **Adding a New AI Model:**
   * Append model object to `data/ai/models_master.json` following the `scores` and `pricing` schema.
   * Run `python src/db_export.py` to refresh `data/database.sqlite`.

2. **Adding a New PC Game:**
   * Append game record to `data/games/games.json` (and mirror in `web/games/data/games.js`), then run `python src/db_export.py` to atomically rebuild `data/database.sqlite`.

3. **Adding a New GPU / Hardware Component:**
   * Add GPU entry to `data/hardware/hardware_specs.json` with TDP, tier, and local market prices.
   * Run `python src/db_export.py` to regenerate the relational table.
