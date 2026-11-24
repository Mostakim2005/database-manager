# Database Manager (`Mostakim2005/database-manager`)

> **Unified benchmark, compatibility, catalog, and repository telemetry database manager across 7 registered domains.**

[![CI Status](https://github.com/Mostakim2005/database-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/Mostakim2005/database-manager/actions)
[![License: PolyForm Noncommercial](https://img.shields.io/badge/License-PolyForm%20NC-blue.svg)](LICENSE)

---

## 🌟 Overview

**Database Manager** consolidates **7 registered data domains** into a single zero-dependency local hub (`127.0.0.1:8770`):
1. **🤖 AI Models & Benchmarks:** 52 frontier & Chinese/OSS models benchmarked against Artificial Analysis Intelligence Indexes, Coding Arena ELOs, reasoning effort simulations, and token pricing telemetry.
2. **🎮 PC Games & Compatibility:** 53 researched strategy/RTS titles benchmarked against an **AMD Ryzen 5 5600GT (Vega 7 iGPU, 16GB RAM, HDD)** reference PC, complete with FPS presets, 1%/0.1% low telemetry, and upgrade simulators.
3. **⚡ PC Hardware & PSU Transient Guard:** GPU upgrade matrices with microsecond transient power excursion multipliers (1.35× to 2.0×), Over-Current Protection (OCP) trip calculators for 550W power supplies, and Bangladesh local (BDT) vs global (USD) market pricing.
4. **🧠 Desktop CPUs (`cpus`):** Socket AM4/AM5/LGA1700 upgrade paths and CPU+GPU platform wattage combos.
5. **🧩 Full PC & Peripherals (`pc_components`):** 69 components across 11 categories with multi-retailer BDT price reconciliation and full-rig compatibility validation.
6. **📚 Manga, Manhwa & Adaptations (`manga`):** 104-title catalog with canonical `comix.to` sitemap lookup, anime/live-action probes, link health audits, and Obsidian `Manhua Links.md` sync.
7. **🐙 GitHub Repositories & CI Health (`github`):** 37+ public repositories (plus local-only gitignored live cache for private repos) with 3-tier activity triage, CI build health, commit gaps, upstream fork drift tracking, and one-click Markdown audit export.

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
Open **[http://127.0.0.1:8770](http://127.0.0.1:8770)** in your browser to access the 5-tabbed portal:
* **Tab 1:** AI Model Matrix & Visual Explorer
* **Tab 2:** GameRank PC Compatibility & Strategy Simulator
* **Tab 3:** PC Hardware Upgrade & PSU Transient Guard
* **Tab 4:** Manga, Manhwa & Adaptations Hub
* **Tab 5:** GitHub Repositories & CI Health Dashboard

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
python src/manga/cli.py --doctor --json
python src/github/cli.py --verify --json
python src/github/cli.py --doctor --json
```

### 3. Compile Consolidated & Separated SQLite Databases
Ingest all JSON datasets into `data/database.sqlite` and isolated per-domain `.sqlite` databases:
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
│   ├── ai/                    # AI models catalogs & taxonomy
│   ├── games/                 # PC game compatibility, benchmarks & taxonomy
│   ├── hardware/              # GPU specifications & PSU transient rules
│   ├── cpus/                  # Desktop CPU catalog & schema
│   ├── pc_components/         # Full PC & peripherals catalog (69 items)
│   ├── manga/                 # Manga/Manhwa/Manhua catalog & gitignored sitemaps
│   ├── github/                # Sanitized repos_public.json & gitignored live_cache.json
│   ├── registry.json          # Central 7-domain registry & cross-domain views
│   └── database.sqlite        # Consolidated SQLite database (git-ignored)
├── web/                       # Multi-tabbed dark-mode web dashboards
│   ├── index.html             # Master 5-Tab Unified Portal
│   ├── ai/                    # AI Model Matrix and visualizer
│   ├── games/                 # GameRank cards, tables, and simulator
│   ├── hardware/              # PC Hardware & PSU Transient Guard calculator
│   ├── manga/                 # Manga & Adaptations catalog & doctor UI
│   └── github/                # GitHub Repositories, CI health & fork drift UI
├── src/                       # Backend and domain modules
│   ├── server.py              # Zero-dependency Python HTTP server (:8770) & CLI search
│   ├── db_export.py           # Consolidated & separated SQLite compilation pipeline
│   ├── db_hub.py              # In-memory SQLite ATTACH cross-domain federation
│   ├── db_verify.py           # Declarative schema & freshness verifier
│   ├── compatibility_engine.py# Full-rig mechanical, electrical & bus validator
│   ├── catalog_classifier.py  # Multi-axis classifiers (AI, Games, Manga, GitHub)
│   ├── manga/                 # Manga crawler, matcher, link health & Obsidian sync
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
