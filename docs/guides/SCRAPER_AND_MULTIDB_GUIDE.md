# Database Manager - Scraper & Multi-DB Guide (`SCRAPER_AND_MULTIDB_GUIDE.md`)
> **1-Line Summary:** Agent-ready instruction set and technical blueprint for the multi-tier scraping stack, separated per-domain SQLite databases (`data/registry.json`), SQLite `ATTACH` cross-domain hub, hybrid verification engine, and domain scaffolding CLI.

### [GUIDE: Scraper-And-Multi-DB-Guide] | Aliases: scraper stack, multi db, db hub, registry, dry run, bd retail
> **1-Line Summary:** Technical blueprint for the multi-tier scraping stack (Tier 0 to Tier 4), separated per-domain SQLite databases (`data/registry.json`), SQLite `ATTACH` cross-domain hub, and dry-run diff engine.

---

## 1. Multi-Tier Scraping Strategy (Never One-Size-Fits-All)

Instead of forcing every website through one heavy browser scraper, `src/scrapers/base.py` routes each target through the lightest tier that succeeds and automatically falls back to the next tier only when blocked (HTTP 403/429, JS challenge, or empty DOM):

| Tier | Stack & License | When to Use | Fallback Trigger |
| :--- | :--- | :--- | :--- |
| **Tier 0 — Official JSON API** | Python stdlib `urllib.request` (Zero deps) | Direct JSON endpoints (OpenRouter, Models.dev, Steam Store API, PCGamingWiki Cargo API, Hugging Face Hub). | Rate-limit or endpoint removed. |
| **Tier 1 — Fast Static HTML** | [httpx](https://github.com/encode/httpx) (BSD-3) + [selectolax](https://github.com/rushter/selectolax) (MIT) | Server-rendered retail & spec pages (Star Tech, Ryans, UCC, TechPowerUp, Notebookcheck). 10–50× faster than headless browsers. | Cloudflare challenge, 403, or JS-rendered price container. |
| **Tier 2 — Adaptive Stealth Fetcher** | [Scrapling](https://github.com/d4vinci/Scrapling) (BSD-3-Clause) | Sites with anti-bot protection, rotating DOM classes, or Cloudflare Turnstile (Bikroy.com, PCPartPicker, Artificial Analysis, eBay Sold). Includes built-in MCP server for AI agents. | Complex multi-step interactive filters or SPA state. |
| **Tier 3 — Full Browser / LLM Crawler** | [Playwright for Python](https://github.com/microsoft/playwright-python) (Apache 2.0) / [Crawl4AI](https://github.com/unclecode/crawl4AI) (Apache 2.0) | Heavy SPAs, infinite-scroll leaderboards, or unstructured benchmark writeups needing clean Markdown/JSON extraction. | Login wall / anti-automation ToS. |
| **Tier 4 — Media & Human-Assisted Import** | [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense) + Offline Paste Parser (`parse_facebook_group_posts`) | YouTube FPS benchmark videos (1% / 0.1% lows + Ryzen 5 5600GT + GPU pairings) and **Facebook Groups / Marketplace** secondhand BD listings (never automate logged-in Facebook accounts). | Manual review / dry-run diff. |

---

## 2. Domain-by-Domain Website Source Matrix

### Domain A — PC Games (Min/Rec Specs + Avg / 1% Low / 0.1% Low FPS)

| Data Type | Recommended Sources | Primary Tier | Fallback Tier | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Min / Rec Specs & USD Store Price | Steam Store API (`store.steampowered.com/api/appdetails?appids=<id>`) | **Tier 0** | Tier 1 | Zero-dependency JSON; parse `pc_requirements.minimum` / `recommended` HTML snippets cleanly. |
| Engine, DRM, Streaming & Fixes | [PCGamingWiki Cargo API](https://github.com/PCGamingWiki/api) (`pcgamingwiki.com/w/api.php`) | **Tier 0** | Tier 1 | Polite rate limit (5 req/s, custom `User-Agent`); provides engine & HDD streaming metadata. |
| Structured GPU/CPU FPS Tables | Notebookcheck Game Benchmarks, TechPowerUp Game Benchmarks | **Tier 1** | Tier 2 (`Scrapling`) | Extract Low/Med/High/Ultra 1080p/1440p averages into `game_benchmarks`. |
| Exact `Ryzen 5 5600GT` + GPU 1% / 0.1% Low FPS | YouTube benchmark channels (Hardware Unboxed, Gamers Nexus, zWORMz Gaming, Testing Games) via [yt-dlp](https://github.com/yt-dlp/yt-dlp) | **Tier 4** (`yt-dlp --write-auto-sub --skip-download`) | Manual entry | Extract descriptions, chapters, and auto-captions for exact Avg / 1% Low / 0.1% Low rows without downloading video files. |

### Domain B — PC Hardware & Asymmetric Local (BDT) + US (USD) Pricing

| Data Type | Recommended Sources | Primary Tier | Fallback Tier | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Bangladesh Retail BDT Prices | [Star Tech](https://www.startech.com.bd/), [Ryans Computers](https://www.ryans.com/), [UCC BD](https://www.ucc.com.bd/) | **Tier 1** (`httpx` + `selectolax`) | Tier 2 (`Scrapling`) | Server-rendered HTML product cards; `parse_bd_retail_html()` extracts price (`৳` / `Tk`) and stock status. |
| Bangladesh Secondhand BDT Prices | [Bikroy.com](https://bikroy.com/) | **Tier 2** (`Scrapling`) | Tier 3 (`Playwright`) | Dynamic listing pages; filter by category + GPU model keyword. |
| Bangladesh Facebook Groups (Used GPUs) | PC Builders BD / Used GPU Marketplace Groups | **Tier 4** (Human-Assisted Paste) | — | **HARD RULE:** Never run automated headless browsers on logged-in Facebook accounts. Copy/export posts to a text file and pass to `parse_facebook_group_posts()` with `--dry-run`. |
| US New & Used USD Prices | PCPartPicker (new), eBay Completed/Sold Listings (used) | **Tier 2** (`Scrapling`) | Tier 3 (`Playwright`) | Track `price_usd_new` and `price_usd_used` in `hardware_prices` alongside BDT prices. |
| GPU Specs, TDP & Transient Rules | TechPowerUp GPU Database | **Tier 1** (`httpx` + `selectolax`) | Tier 2 (`Scrapling`) | Authoritative TDP, VRAM, bus width, and release date. |

### Domain C — AI Models & Frontier / Open-Source Benchmarks

| Data Type | Recommended Sources | Primary Tier | Fallback Tier | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Live Model Catalog & Token Pricing | OpenRouter API (`openrouter.ai/api/v1/models`), Models.dev (`models.dev/catalog.json?type=all`) | **Tier 0** | — | Dual-source pricing & context concordance. |
| General Intelligence & Speed Index | [Artificial Analysis Leaderboard](https://artificialanalysis.ai/leaderboards/models) | **Tier 2** (`Scrapling`) | Tier 3 (`Crawl4AI`) | Next.js / hydrated tables; extract AA Intelligence Index, Coding, and STEM scores. |
| Human-Voted ELO Rankings | [Arena Leaderboard](https://arena.ai/leaderboard) / [lmarena-ai Hugging Face Space](https://huggingface.co/spaces/lmarena-ai/arena-leaderboard) | **Tier 0** (HF dataset/API) | Tier 3 (`Playwright`) | Pull underlying JSON/CSV from the Hugging Face Space before falling back to DOM scraping. |
| Open-Weights Parameter & Quantization Info | Hugging Face Hub API (`huggingface.co/api/models`) | **Tier 0** | — | Powers the `v_local_ai_vram_fit` cross-domain join against `hardware.hardware_gpus`. |

---

## 3. Separated Multi-Database Architecture (`data/registry.json` + SQLite `ATTACH`)

Every domain lives in its own isolated folder and standalone `.sqlite` file, while `src/db_hub.py` attaches them together dynamically at query time:

```text
data/
├── registry.json               # Central domain registry (schemas, freshness TTL, cross-domain joins)
├── database.sqlite             # Backward-compatible consolidated SQLite (optional)
├── ai/
│   ├── models_master.json      # Source JSON
│   ├── schema.json             # Declarative domain schema contract
│   └── ai.sqlite               # Isolated SQLite (ai_models + _meta)
├── games/
│   ├── games.json              # Source JSON
│   ├── schema.json             # Declarative domain schema contract
│   └── games.sqlite            # Isolated SQLite (pc_games + game_benchmarks + _meta)
└── hardware/
    ├── hardware_specs.json     # Source JSON
    ├── schema.json             # Declarative domain schema contract
    └── hardware.sqlite         # Isolated SQLite (hardware_gpus + hardware_prices + _meta)
```

### Logical Cross-Domain Views (`src/db_hub.py`)
1. **`v_games_by_gpu`** — Joins `games.pc_games` × `hardware.hardware_gpus` to show which games meet min/recommended tiers on a given GPU, paired with 550W PSU safety verdict and BDT/USD upgrade price.
2. **`v_local_ai_vram_fit`** — Joins open-weights `ai.ai_models` × `hardware.hardware_gpus` to estimate Q4/Q8 local VRAM fit.
3. **`v_domain_health`** — Unions `_meta` across every registered domain DB (record count, schema version, SHA-256 content hash, last updated timestamp, and `is_stale` flag when older than `max_age_days`).

### Optional OSS Power-User Bridges
Because every domain is a standard SQLite file, you can also inspect or query all of them simultaneously with zero code changes:
* **[Datasette](https://github.com/simonw/datasette) (Apache 2.0):** `datasette data/ai/ai.sqlite data/games/games.sqlite data/hardware/hardware.sqlite`
* **[sqlite-utils](https://github.com/simonw/sqlite-utils) (Apache 2.0):** `sqlite-utils tables data/games/games.sqlite --counts`
* **[DuckDB](https://duckdb.org/) (MIT):** `ATTACH 'data/games/games.sqlite' AS games (TYPE SQLITE); ATTACH 'data/hardware/hardware.sqlite' AS hw (TYPE SQLITE);`

---

## 4. Agent Execution Instructions (Testing Scrapers & Adding Domains)

### Step 1 — Install Optional Scraper Stack (Isolated from Core)
Core `server.py`, `db_export.py`, `db_hub.py`, and `db_verify.py` require **zero pip packages**. To test Tier 1–3 scrapers locally, install only the tiers you need:
```bash
pip install -r requirements-scrapers.txt
# Optional for Tier 3 browser scraping:
playwright install chromium
```

### Step 2 — Probe Which Scraper Tiers Work on Your Machine
```bash
# Offline diagnostic probe (runs built-in parser fixtures + reports installed tiers):
python src/scrapers/test_stack.py

# Live network probe across Tier 0 -> Tier 1 -> Tier 2 -> Tier 3:
python src/scrapers/test_stack.py --live --dry-run
```

### Step 3 — Run Scrapers Safely with `--dry-run` Diff Preview
Always preview changes (`+ added`, `~ changed`, `- removed`) before committing scraped data:
```bash
python src/scrapers/test_stack.py --live --dry-run --domain ai
```
For Facebook Group secondhand GPU posts, paste copied posts into a local text file (e.g., `fb_posts.txt`) and parse offline:
```bash
python src/scrapers/test_stack.py --fb-file fb_posts.txt --dry-run
```

### Step 4 — Compile Separated Databases & Run Hybrid Verification
```bash
# Compile per-domain SQLite files + consolidated database.sqlite atomically:
python src/db_export.py

# Run hybrid schema, range, freshness, and cross-domain integrity checks:
python src/db_verify.py

# Query cross-domain views via REST API (when server.py is running):
#   GET /api/domains
#   GET /api/cross/games-by-gpu?gpu=rx-6600&psu=550
#   GET /api/cross/ai-vram-fit?gpu=rx-6600
```

### Step 5 — Scaffold a Brand-New Domain Database (`--init-domain`)
```bash
python src/db_export.py --init-domain laptops
```
This creates `data/laptops/laptops.json`, `data/laptops/schema.json`, and registers `laptops` in `data/registry.json`. Next:
1. Customize `data/laptops/schema.json` with required fields and numeric ranges.
2. Add records (or a scraper adapter in `src/scrapers/`) and run `python src/db_verify.py --domain laptops`.
3. Run `python src/db_export.py` to compile `data/laptops/laptops.sqlite` with its `_meta` table automatically.
