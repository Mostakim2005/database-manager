# Database Manager (`Mostakim2005/database-manager`)

> **Unified benchmark, compatibility, and specifications database manager across AI models, PC games, and hardware upgrades.**

[![CI Status](https://github.com/Mostakim2005/database-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/Mostakim2005/database-manager/actions)
[![License: PolyForm Noncommercial](https://img.shields.io/badge/License-PolyForm%20NC-blue.svg)](LICENSE)

---

## 🌟 Overview

**Database Manager** consolidates three core research domains into a single zero-dependency local hub:
1. **🤖 AI Models & Benchmarks:** 26+ frontier models benchmarked against Artificial Analysis Intelligence Indexes, Coding Arena ELOs, reasoning effort simulations, and token pricing telemetry.
2. **🎮 PC Games & Compatibility:** 43 researched strategy/RTS titles benchmarked against an **AMD Ryzen 5 5600GT (Vega 7 iGPU, 16GB RAM, HDD)** reference PC, complete with FPS presets and upgrade simulators.
3. **⚡ PC Hardware & PSU Transient Guard:** GPU upgrade matrices with microsecond transient power excursion multipliers (1.35× to 2.0×), Over-Current Protection (OCP) trip calculators for 550W power supplies, and asymmetric local (BDT) vs global (USD) market pricing.

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
Open **[http://127.0.0.1:8770](http://127.0.0.1:8770)** in your browser to access the tabbed portal:
* **Tab 1:** AI Model Matrix & Visual Explorer
* **Tab 2:** GameRank PC Compatibility & Strategy Simulator
* **Tab 3:** PC Hardware Upgrade & PSU Transient Guard

### 2. Multi-Domain Terminal CLI
Query the database directly from PowerShell or Command Prompt:
```cmd
run-cli.bat
```
Search for any model, game, or hardware GPU:
```bash
python src/server.py --cli "claude"
python src/server.py --cli "starcraft"
python src/server.py --cli "rx 6600"
```

### 3. Compile Consolidated SQLite Database
Ingest all JSON datasets into `data/database.sqlite`:
```bash
python src/db_export.py
```
Verify table schemas and record counts:
```bash
python src/db_export.py --verify
```

---

## 📁 Repository Directory Layout

```text
Database Manager/
├── .github/workflows/ci.yml   # GitHub Actions automated verification runner
├── data/                      # Master datasets
│   ├── ai/                    # AI models catalogs (models_master.json, model-comparison.csv)
│   ├── games/                 # PC game compatibility data (games.js, games.json)
│   ├── hardware/              # Hardware specifications & PSU transient rules (hardware_specs.json)
│   └── database.sqlite        # Consolidated SQLite database (git-ignored)
├── web/                       # Multi-tabbed glassmorphic web dashboards
│   ├── index.html             # Master Unified Portal with tab switcher
│   ├── ai/                    # AI Model Matrix and visualizer
│   ├── games/                 # GameRank cards, tables, and simulator
│   └── hardware/              # PC Hardware & PSU Transient Guard calculator
├── src/                       # Backend and data tools
│   ├── server.py              # Zero-dependency Python HTTP server & CLI search tool
│   ├── db_export.py           # SQLite compilation and integrity pipeline
│   ├── update_models.ps1      # Upstream AI models sync pipeline
│   └── hardware_planner_obsidian/ # Archived Obsidian plugin source
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
