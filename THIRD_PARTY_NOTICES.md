# Third-Party Notices (`THIRD_PARTY_NOTICES.md`)

This repository incorporates or references the following third-party libraries, datasets, and tooling. We gratefully acknowledge the authors and open-source communities.

## Ships inside the app

| Component / Library | Purpose & Usage | Upstream License | Upstream Source |
| :--- | :--- | :--- | :--- |
| **Chart.js** | Interactive Pareto frontier and performance charts in web dashboards | [MIT License](https://opensource.org/licenses/MIT) | [chartjs.org](https://www.chartjs.org/) |
| **OpenRouter Benchmark Data** | Public intelligence, coding ELO, and pricing metrics | Open Data / Public Attribution | [openrouter.ai](https://openrouter.ai/) |
| **Artificial Analysis (AA)** | Intelligence Index benchmarks and latency telemetry | Public Evaluation Citation | [artificialanalysis.ai](https://artificialanalysis.ai/) |
| **models.dev Catalog** | Model capabilities, pricing, and provider fact-checking | Public API Specification | [models.dev](https://models.dev/) |
| **PC Game Storefront Specs** | Verbatim minimum/recommended specifications and pricing (Steam, GOG, Epic) | Fair Use Research Citation | Valve Corporation, CD Projekt, Epic Games |
| **Obsidian API** | TypeScript typings for the archived Obsidian hardware planner plugin | [MIT License](https://opensource.org/licenses/MIT) | [github.com/obsidianmd/obsidian-api](https://github.com/obsidianmd/obsidian-api) |

## Build / test only — not shipped

| Component / Tool | Purpose & Usage | Upstream License | Upstream Source |
| :--- | :--- | :--- | :--- |
| **esbuild** | Fast bundler for Obsidian plugin packaging | [MIT License](https://opensource.org/licenses/MIT) | [github.com/evanw/esbuild](https://github.com/evanw/esbuild) |
| **TypeScript** | Static type checking for archived hardware plugin sources | [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) | [github.com/microsoft/TypeScript](https://github.com/microsoft/TypeScript) |
| **ESLint** | Code linting and style enforcement | [MIT License](https://opensource.org/licenses/MIT) | [eslint.org](https://eslint.org/) |
| **GitHub Actions** | Automated CI verification runner | Platform Provided | [github.com/features/actions](https://github.com/features/actions) |

## Optional Scraper & Database Exploration Stack (`requirements-scrapers.txt` — not required for core)

| Component / Library | Purpose & Usage | Upstream License | Upstream Source |
| :--- | :--- | :--- | :--- |
| **httpx** | Tier 1 async/HTTP client for static retail & API endpoints | BSD-3-Clause | [github.com/encode/httpx](https://github.com/encode/httpx) |
| **selectolax** | Tier 1 fast HTML5 CSS selector parser (Lexbor) | MIT License | [github.com/rushter/selectolax](https://github.com/rushter/selectolax) |
| **Scrapling** | Tier 2 adaptive stealth scraping & MCP server | BSD-3-Clause | [github.com/d4vinci/Scrapling](https://github.com/d4vinci/Scrapling) |
| **Playwright for Python** | Tier 3 headless browser automation for JS-heavy sites | Apache 2.0 | [github.com/microsoft/playwright-python](https://github.com/microsoft/playwright-python) |
| **Crawl4AI** | Tier 3 LLM-ready structured web crawler | Apache 2.0 | [github.com/unclecode/crawl4AI](https://github.com/unclecode/crawl4AI) |
| **yt-dlp** | Tier 4 YouTube benchmark metadata/transcript extractor | The Unlicense | [github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| **Pydantic** | Optional strict runtime schema coercion for scrapers | MIT License | [github.com/pydantic/pydantic](https://github.com/pydantic/pydantic) |
| **Datasette & sqlite-utils** | Optional local SQL explorer & CLI over separated `.sqlite` files | Apache 2.0 | [github.com/simonw/datasette](https://github.com/simonw/datasette) |
