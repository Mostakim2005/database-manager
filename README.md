# Database Manager (`Mostakim2005/database-manager`)

> **Unified benchmark, compatibility, catalog, and repository telemetry database manager across 7 registered domains.**

[![CI Status](https://github.com/Mostakim2005/database-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/Mostakim2005/database-manager/actions)
[![License: PolyForm Noncommercial](https://img.shields.io/badge/License-PolyForm%20NC-blue.svg)](LICENSE)

---

## 🌟 Overview

**Database Manager** consolidates **7 registered, grouped data domains** (`display_name` & `aliases` configured in `data/registry.json`) into a single zero-dependency local hub (`127.0.0.1:8770`):
1. **⚡ PC & Hardware (`pc`, group `pc_gaming`):** 75 unified components across 12 categories (10 CPUs, 10 GPUs, 4 PSUs, motherboards, RAM, SSDs, HDDs, displays, peripherals) with microsecond PSU transient excursion safety calculators (1.35×–2.0×) and Bangladesh multi-retailer pricing (Star Tech, Ryans, UCC).
2. **🎮 PC Games (`games`, group `pc_gaming`):** 53 researched strategy/RTS titles benchmarked against an **AMD Ryzen 5 5600GT (Vega 7 iGPU)** baseline and cross-linked directly with `pc` GPU tiers and 51 real-world 1% / 0.1% Low FPS runs (`benchmarks.csv` ↔ `v_game_benchmarks_with_pc`).
3. **🤖 AI Models (`ai`, group `ai_models`):** 52 frontier, near-frontier, and specialized models scored across Artificial Analysis Intelligence Indexes, Coding Arena ELOs, reasoning effort simulations, and API token pricing (decoupled from local VRAM hardware).
4. **🎬 Media & Adaptations (`media`, group `media_knowledge`):** 110 interconnected entries across `comic`, `light_novel`, `anime`, `donghua`, `movie`, and `tv_series` subdomains linked via `franchise_id` and `relations`, with `comix.to` sitemap lookup and link health audits.
5. **📚 Book Collection (`book`, group `media_knowledge`, alias-ready for `learning`/`reading`):** Personal library tracking ownership (`owned`, `wishlist`, `borrowed`, `library`), reading status, format, ratings, and notes.
6. **📱 Phone & Mobile (`phone`, group `mobile`):** Device specs (SoC, GPU, RAM, display refresh rate, battery/charging, BDT/USD price) paired with verified `supported_games` and `supported_apps` matrices.
7. **🐙 GitHub Repositories (`github`, group `devops`):** 37+ public repositories (plus local-only gitignored live cache for private repos) with 3-tier activity triage, CI build health, commit gaps, upstream fork drift tracking, and Markdown export.

---

## 🚀 Quick Start

### 1. Launch Web Dashboard Portal
Start the built-in HTTP server on `http://127.0.0.1:8770`:
```cmd
start-server.bat
```
Or directly with Python (requires Python 3.10+, zero pip packages):
```bash
python src/server.py
```
Open **[http://127.0.0.1:8770](http://127.0.0.1:8770)** in your browser to access the registry-driven, group-clustered portal across **PC, Games, AI, Media, Book, Phone, and GitHub**.

### 2. Multi-Domain Terminal CLI
Query the database directly from PowerShell or Command Prompt:
```cmd
run-cli.bat
```
Search across all domains or run domain-specific CLIs:
```bash
python src/server.py --cli "claude"
python src/server.py --cli "starcraft"
python src/server.py --cli "rx 6600"
python src/media/cli.py --doctor --json
python src/github/cli.py --verify --json
python src/db_verify.py --domain learning
```

### 3. Compile Consolidated & Isolated SQLite Databases
Ingest all JSON/CSV datasets into `data/database.sqlite` and strictly isolated per-domain `.sqlite` databases (each containing only its own tables + `_meta`):
```bash
python src/db_export.py
```
Verify table schemas, record counts, and declarative `schema.json` contracts:
```bash
python src/db_export.py --verify
python src/db_verify.py
```

---

## 📁 Repository Directory Layout

```text
Database Manager/
├── .github/workflows/ci.yml   # GitHub Actions automated verification runner
├── data/                      # Master datasets across 7 registered domains
│   ├── pc/                    # Unified PC parts, CPUs, GPUs, PSUs & transient rules
│   ├── games/                 # PC game compatibility, benchmarks.csv & taxonomy
│   ├── ai/                    # AI models pricing, tiers & origin taxonomy
│   ├── media/                 # Media & Adaptations catalog & gitignored sitemaps
│   ├── book/                  # Book collection & reading tracker (alias-ready)
│   ├── phone/                 # Mobile device specs & supported games/apps catalog
│   ├── github/                # Sanitized repos_public.json & gitignored live_cache.json
│   ├── registry.json          # Groups, display_name, aliases & cross-domain views
│   └── database.sqlite        # Consolidated SQLite database (git-ignored)
├── web/                       # Dynamic portal & safe-DOM dark-mode dashboards
│   ├── index.html             # Registry-driven grouped multi-domain portal
│   ├── pc/                    # Unified PC Parts, CPUs, GPUs & PSU Guard calculator
│   ├── games/                 # GameRank cards, tables & live pc-GPU simulator
│   ├── ai/                    # AI Model Matrix and pricing visualizer
│   ├── media/                 # Media, Franchise Relations, Doctor & Link Audit UI
│   ├── book/                  # Book Collection & Reading tracker UI
│   ├── phone/                 # Phone Specs & Supported Games/Apps UI
│   └── github/                # GitHub Repositories, CI health & fork drift UI
├── src/                       # Backend and domain modules
│   ├── server.py              # Zero-dependency Python HTTP server (:8770) & CLI search
│   ├── db_export.py           # Consolidated & table-isolated SQLite compilation pipeline
│   ├── db_hub.py              # In-memory SQLite ATTACH federation (games <-> pc views)
│   ├── db_verify.py           # Declarative schema & alias verifier
│   ├── compatibility_engine.py# Full-rig mechanical, electrical & bus validator
│   ├── catalog_classifier.py  # Multi-axis classifiers (AI, Games, Media, GitHub)
│   ├── media/                 # Media crawler, matcher, adaptation refresh & link health
│   ├── github/                # GitHub gh api scanner, triage, exporter & CLI
│   ├── scrapers/              # Multi-tier hardware, games & LLM scrapers
│   ├── update_models.ps1      # Upstream AI models sync pipeline
│   └── hardware_planner_obsidian/ # Archived Obsidian plugin source
├── tests/                     # Unit & integration tests (unittest)
├── docs/                      # Core living documentation suite
│   ├── PRODUCT.md             # Product intent, active feature map & wishlist
│   ├── ARCHITECTURE.md        # Obsidian-compatible Mermaid architecture flows
│   └── DECISIONS_AND_TRAPS.md # Architectural pivots and critical engineering traps
├── local-ci.ps1               # Local verification runner emitting patch-ready reports
├── AGENTS.md                  # Project-specific AI agent operating guidelines
├── LICENSE                    # PolyForm Noncommercial 1.0.0
└── THIRD_PARTY_NOTICES.md     # Upstream open-source attribution table
```

---

## 🛠️ Verification & Testing

Run the local verification runner:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\local-ci.ps1
```
All checks (Python syntax, CLI smoke tests, SQLite integrity, and JSON schema validation) are mirrored in GitHub Actions (`.github/workflows/ci.yml`).

---

## ⚖️ License & Attribution

* Code and Documentation: Licensed under the **[PolyForm Noncommercial License 1.0.0](LICENSE)**.
* Third-Party Open Source Notices: See **[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)** for Chart.js, OpenRouter, and models.dev citations.
