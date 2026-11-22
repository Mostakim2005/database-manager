# Product Intent & Feature Map (`PRODUCT.md`)
> **1-Line Summary:** Mathematical PC hardware comparison and upgrade forecasting plugin for Obsidian tailored to asymmetric market pricing, local currency benchmarks, and power safety.

## 1. Core Vision & User Experience Intent
* **What This App Does (Plain English):** Evaluates GPU and CPU upgrade paths by cross-referencing real-world frame rates across 160+ games, 30+ software apps, power supply limits (e.g. 550W Bronze PSU), and local market pricing (Dhaka/Bangladesh used & retail alongside global USD).
* **How It Must Feel to Use:** Fast, offline-first, high-density glassmorphic dashboard with interactive Pareto frontier curves and zero layout shifting.

## 2. Active Features (Do Not Break)

### [FEATURE: Hardware-Comparison-Engine] | Aliases: gpu compare, price performance, upgrade matrix
> **1-Line Summary:** Interactive Pareto value analysis charting FPS-per-taka and FPS-per-dollar across 36+ modern GPUs.
* **User Intention (Non-Negotiable):** Provide objective mathematical comparison to prevent overspending on diminishing-return hardware.
* **Visual / UI Behavior:** Opens in a dedicated Obsidian workspace view via ribbon icon or command palette with interactive Chart.js graphs.
* **Code Anchors (Grep Targets):**
  * `src/main.ts` -> `renderComparisonView`, `calculateParetoFrontier`

### [FEATURE: PSU-Transient-Spike-Guard] | Aliases: psu check, power limit, 550w cx550 calculator
> **1-Line Summary:** Evaluates system power draw and transient spikes against specific PSU thresholds (e.g. 550W 43A rail).
* **User Intention (Non-Negotiable):** Warn the user before they purchase a GPU whose microsecond power spikes trip single +12V rail overcurrent protection.
* **Visual / UI Behavior:** Displays color-coded safety badges (Green: Safe, Amber: Caution, Red: Critical Trip Risk).
* **Code Anchors (Grep Targets):**
  * `src/psu.ts` -> `calculatePsuSafetyMargin`, `evaluateTransientHeadroom`

### [FEATURE: Game-Benchmark-Forecaster] | Aliases: fps estimator, 1080p gaming, bottleneck check
> **1-Line Summary:** Predicts average 1080p and 1440p frame rates factoring in CPU bottlenecks (e.g. Ryzen 5 5600GT 16MB L3 cache).
* **User Intention (Non-Negotiable):** Show real-world playable performance rather than synthetic raw compute teraflops.
* **Code Anchors (Grep Targets):**
  * `src/main.ts` -> `estimateFpsForTitle`, `applyCpuCachePenalty`

## 3. Planned Features & App-Merge Wishlist

### [WISHLIST: Live-Price-Scraper-Integration] | Aliases: startech scraper, ryans price sync, bd retail sync
> **1-Line Summary:** On-demand local market pricing sync from major regional electronics retailers.
* **User Intention:** Eliminate manual price entry for Bangladeshi Taka (BDT) used and new market listings.
* **Target Integration Point:** `src/settings.ts` -> `PriceSyncHandler`

### [FEATURE: UI-UX-Parity-And-Accessibility] | Aliases: hardware planner view, confirm modal, psu status bar, settings tab
> **1-Line Summary:** Introduces full Workspace ItemView, ConfirmModal guardrail, dedicated SettingsTab, clickable PSU calculator Status Bar pill, and WCAG accessibility styles.
* **User Intention (Non-Negotiable):** Provide desktop and mobile users with a persistent hardware planning view, safe modal confirmation for destructive resets, and real-time PSU power metrics in the status bar.
* **Visual / UI Behavior:** Dedicated workspace leaf with ribbon launcher, status bar showing total estimated wattage, and accessible focus states across all interactive elements.
* **Code Anchors (Grep Targets):** `src/view.ts`, `src/confirm-modal.ts`, `src/settings-tab.ts`, `src/main.ts`, `styles.css`
