/**
 * AI Frontier & Budget Matrix — Application Orchestrator (v1.3.0)
 * Coordinates dynamic column visibility, global & per-model reasoning effort simulation,
 * dual-source Models.dev fact-checking, provider/tier filtering, logic advisor, and 30 real-world tasks.
 */

window.MatrixApp = {
  catalog: [],
  selectedModelIds: new Set(),
  currentQuickFilter: 'all',
  currentFamilyFilter: 'all',
  currentTierFilter: 'all',
  searchQuery: '',
  modalSearchQuery: '',
  modalFamilyFilter: 'all',
  modalTierFilter: 'all',

  // Reasoning Effort Simulation State
  globalEffort: 'medium', // 'low', 'medium', 'high', 'ultra_high'
  modelEffortOverrides: {}, // { modelId: 'ultra_high' }

  // 30 Real-World Tasks Dataset
  tasks: [
    // Tier 1: Simple / Routine Tasks (1-10)
    { id: 1, tier: 'Simple', name: 'Regex Pattern Generator', desc: 'Generate and validate complex email, phone, and slug regex patterns with unit tests.', promptTok: 1500, complTok: 400, cachedTok: 1000, recModel: 'Meta Muse Spark 1.3', freeModel: 'Meta Muse Spark 1.3' },
    { id: 2, tier: 'Simple', name: 'Python Docstrings & Type Annotations', desc: 'Add PEP 257 docstrings and PEP 484 static typing to an undocumented utility module.', promptTok: 2000, complTok: 600, cachedTok: 1500, recModel: 'GLM 5.3 Flash', freeModel: 'GLM 5.3 Flash' },
    { id: 3, tier: 'Simple', name: 'Git Commit & Release Note Synthesizer', desc: 'Summarize git diff into conventional commit messages and clean changelog bullets.', promptTok: 3000, complTok: 500, cachedTok: 2500, recModel: 'DeepSeek 4.1 Flash (1017)', freeModel: 'DeepSeek 4.1 Flash (1017)' },
    { id: 4, tier: 'Simple', name: 'JSON Schema Validator & Fixtures', desc: 'Derive JSON Schema from payload examples and output 10 diverse mock fixtures.', promptTok: 2500, complTok: 800, cachedTok: 2000, recModel: 'Claude Haiku 5.5', freeModel: 'GLM 5.3 Flash' },
    { id: 5, tier: 'Simple', name: 'Tailwind CSS Layout Formatter', desc: 'Refactor raw CSS into responsive Tailwind flexbox, grid, and dark-mode utility classes.', promptTok: 2000, complTok: 700, cachedTok: 1500, recModel: 'GPT-5.6 Terra', freeModel: 'Qwen 2.5 Coder 32B' },
    { id: 6, tier: 'Simple', name: 'REST API Mock Fixture Generator', desc: 'Synthesize mock JSON data matching complex nested relations (Users, Orders, Items).', promptTok: 1800, complTok: 900, cachedTok: 1200, recModel: 'Z.ai GLM 5.3', freeModel: 'DeepSeek 4.1 Flash (1017)' },
    { id: 7, tier: 'Simple', name: 'Code Linter & Typo Remediation', desc: 'Identify syntax issues, variable name typos, and unused dependencies in scripts.', promptTok: 3500, complTok: 500, cachedTok: 3000, recModel: 'Meta Muse Spark 1.3', freeModel: 'Meta Muse Spark 1.3' },
    { id: 8, tier: 'Simple', name: 'Markdown Technical Readme', desc: 'Generate an executive summary, installation guide, and quickstart documentation.', promptTok: 4000, complTok: 1200, cachedTok: 3500, recModel: 'Gemini 3.8 Flash', freeModel: 'Gemini 3.8 Flash' },
    { id: 9, tier: 'Simple', name: 'SQL Query Builder & Aggregator', desc: 'Write SQL queries using window functions, CTEs, and index-optimized joins.', promptTok: 2200, complTok: 600, cachedTok: 1800, recModel: 'Meta Muse Spark 1.3', freeModel: 'Meta Muse Spark 1.3' },
    { id: 10, tier: 'Simple', name: 'PowerShell / Shell Automation Script', desc: 'Build an idempotent Windows maintenance or file backup automation utility script.', promptTok: 2000, complTok: 800, cachedTok: 1500, recModel: 'Claude Haiku 5.5', freeModel: 'GLM 5.3 Flash' },

    // Tier 2: Medium / Fullstack Tasks (11-20)
    { id: 11, tier: 'Medium', name: 'Full CRUD REST API with JWT Auth', desc: 'Build production-ready Express/FastAPI route with bcrypt, JWT auth, and middleware.', promptTok: 12000, complTok: 2500, cachedTok: 10000, recModel: 'Claude Sonnet 5.5', freeModel: 'Meta Muse Spark 1.3' },
    { id: 12, tier: 'Medium', name: 'React 19 Data Grid with Virtualization', desc: 'Develop responsive React component with virtualization, multi-column sort, and custom hooks.', promptTok: 15000, complTok: 3200, cachedTok: 12000, recModel: 'Claude Sonnet 5.5', freeModel: 'Meta Muse Spark 1.3' },
    { id: 13, tier: 'Medium', name: 'Database Migration & Zero-Downtime Rollback', desc: 'Create schema migration with foreign keys, index additions, and rollback verification.', promptTok: 18000, complTok: 2800, cachedTok: 15000, recModel: 'GPT-6 Sol', freeModel: 'Xiaomi MiMo V2.6 Pro' },
    { id: 14, tier: 'Medium', name: 'Resilient Multi-Step Web Scraper', desc: 'Implement headless browser scraper with rate-limiting, CAPTCHA bypass, and retry logic.', promptTok: 14000, complTok: 3500, cachedTok: 11000, recModel: 'Meta Muse Spark 1.3', freeModel: 'Meta Muse Spark 1.3' },
    { id: 15, tier: 'Medium', name: 'Audio FFT Spectrogram Processor', desc: 'Design Web Audio API pipeline calculating real-time FFT frequency bins and decibels.', promptTok: 22000, complTok: 4200, cachedTok: 18000, recModel: 'Gemini 4 Argon', freeModel: 'Gemini 3.8 Flash' },
    { id: 16, tier: 'Medium', name: 'WebSocket Real-Time Sync Server', desc: 'Build Node.js WebSocket engine with room pub/sub, heartbeat pings, and reconnect queues.', promptTok: 16000, complTok: 3000, cachedTok: 13000, recModel: 'Claude Sonnet 5.5', freeModel: 'Meta Muse Spark 1.3' },
    { id: 17, tier: 'Medium', name: 'PDF Spatial Text Parser & OCR Pipeline', desc: 'Extract bounding box text coords and align two-column academic paper sections.', promptTok: 25000, complTok: 4500, cachedTok: 20000, recModel: 'Claude Sonnet 5.5', freeModel: 'Gemini 3.8 Flash' },
    { id: 18, tier: 'Medium', name: 'Docker Compose Multi-Service Stack', desc: 'Configure Dockerized web app, PostgreSQL with volume, Redis cache, and Traefik SSL.', promptTok: 10000, complTok: 2400, cachedTok: 8000, recModel: 'GPT-5.6 Terra', freeModel: 'GLM 5.3 Flash' },
    { id: 19, tier: 'Medium', name: 'High-Throughput Algorithm Optimizer', desc: 'Optimize matrix multiplication or graph traversal with cache-friendly contiguous layout.', promptTok: 20000, complTok: 3800, cachedTok: 16000, recModel: 'Gemini 4 Argon', freeModel: 'Meta Muse Spark 1.3' },
    { id: 20, tier: 'Medium', name: 'Electron IPC & Native Win32 Interop', desc: 'Write typed IPC bridge between renderer and preload script handling system events.', promptTok: 28000, complTok: 4800, cachedTok: 24000, recModel: 'Claude Sonnet 5.5', freeModel: 'Meta Muse Spark 1.3' },

    // Tier 3: Exclusive / Frontier Hard Tasks (21-30)
    { id: 21, tier: 'Exclusive', name: 'Compiler AST Pass & SSA Optimizer', desc: 'Design custom compiler backend lowering AST to SSA intermediate representation with DCE.', promptTok: 75000, complTok: 6500, cachedTok: 65000, recModel: 'Claude Opus 5.5', freeModel: 'Meta Muse Spark 1.3' },
    { id: 22, tier: 'Exclusive', name: 'Formal Proof in Lean / Coq', desc: 'Synthesize machine-checked mathematical proof for non-trivial algebraic geometry lemma.', promptTok: 60000, complTok: 7500, cachedTok: 50000, recModel: 'Claude Opus 5.5', freeModel: 'Gemini 4 Argon' },
    { id: 23, tier: 'Exclusive', name: 'Lock-Free Ring Buffer in C++20', desc: 'Implement high-concurrency wait-free queue with atomic memory orders and cacheline alignment.', promptTok: 65000, complTok: 5500, cachedTok: 55000, recModel: 'GPT-6 Astra', freeModel: 'Meta Muse Spark 1.3' },
    { id: 24, tier: 'Exclusive', name: 'Autonomous Multi-Agent Orchestrator', desc: 'Build hierarchical multi-agent state machine with vector memory, reflection, and rollback.', promptTok: 90000, complTok: 8000, cachedTok: 80000, recModel: 'Claude Opus 5.5', freeModel: 'Meta Muse Spark 1.3' },
    { id: 25, tier: 'Exclusive', name: 'Binary Protocol Reverse Engineering', desc: 'Disassemble proprietary binary TCP stream, reconstruct frame spec and Wireshark dissector.', promptTok: 80000, complTok: 6000, cachedTok: 70000, recModel: 'Claude Opus 5.5', freeModel: 'Xiaomi MiMo V2.6 Pro' },
    { id: 26, tier: 'Exclusive', name: '100k-Line Legacy Codebase Refactor', desc: 'Execute architectural transformation across entire repository using semantic AST diffs.', promptTok: 140000, complTok: 9500, cachedTok: 125000, recModel: 'Claude Sonnet 5.5', freeModel: 'Meta Muse Spark 1.3' },
    { id: 27, tier: 'Exclusive', name: 'Relativistic N-Body Physics Simulator', desc: 'Simulate Kerr black hole gravitational lensing raytracing using Runge-Kutta 4th order.', promptTok: 70000, complTok: 7000, cachedTok: 60000, recModel: 'Gemini 4 Argon', freeModel: 'Gemini 3.8 Flash' },
    { id: 28, tier: 'Exclusive', name: 'Distributed Event-Sourcing & CQRS Migration', desc: 'Design zero-downtime event store migration with Kafka, event replay, and snapshotting.', promptTok: 85000, complTok: 8500, cachedTok: 75000, recModel: 'Claude Opus 5.5', freeModel: 'Meta Muse Spark 1.3' },
    { id: 29, tier: 'Exclusive', name: 'Win32 Virtual Key & DIB Memory Interop', desc: 'Low-level C++/Node-API addon injecting simulated keystrokes and converting DIB bitmaps.', promptTok: 95000, complTok: 7200, cachedTok: 85000, recModel: 'Claude Sonnet 5.5', freeModel: 'Meta Muse Spark 1.3' },
    { id: 30, tier: 'Exclusive', name: 'Zero-Day Vulnerability & Taint Audit', desc: 'Perform static control-flow analysis and taint propagation tracking memory corruptions.', promptTok: 110000, complTok: 8000, cachedTok: 95000, recModel: 'Claude Opus 5.5', freeModel: 'Meta Muse Spark 1.3' }
  ],

  init() {
    if (window.MASTER_CATALOG && Array.isArray(window.MASTER_CATALOG)) {
      this.catalog = [...window.MASTER_CATALOG];
    } else {
      console.warn('MASTER_CATALOG not detected on window. Initializing with empty state.');
      this.catalog = [];
    }

    this.selectedModelIds = new Set(this.catalog.map(m => m.id));
    this.recalculateEffortScores();
    this.updateEffortAdvisory();

    window.MatrixTable.renderHeaders();
    this.renderColManagerMenu();
    this.renderModalChecklist();
    this.applyFiltersAndRender();
    this.bindEvents();
    this.runAdvisor();
    this.renderTasksTable();
  },

  bindEvents() {
    // Search input listener
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        this.searchQuery = searchInput.value.toLowerCase().trim();
        this.applyFiltersAndRender();
      });
    }

    // Modal search listener
    const modalSearch = document.getElementById('modalSearchInput');
    if (modalSearch) {
      modalSearch.addEventListener('input', () => {
        this.modalSearchQuery = modalSearch.value.toLowerCase().trim();
        this.renderModalChecklist();
      });
    }

    // Chart height selector listener
    const heightSelect = document.getElementById('chartHeightSelect');
    if (heightSelect) {
      heightSelect.addEventListener('change', (e) => {
        window.MatrixCharts.setHeight(e.target.value);
      });
    }

    // Close column dropdown when clicking outside
    document.addEventListener('click', (e) => {
      const dropdown = document.querySelector('.col-manager-dropdown');
      const menu = document.getElementById('colManagerMenu');
      if (dropdown && menu && !dropdown.contains(e.target)) {
        menu.style.display = 'none';
      }
    });
  },

  // ----------------------------------------------------
  // Reasoning Effort Simulation Subsystem
  // ----------------------------------------------------
  /**
   * Normalizes an effort level to the storage key used in effort_simulation.multipliers.
   * data.js (authored by update_models.ps1) uses 'low' | 'medium' | 'high' | 'ultra'.
   * The UI exposes 'ultra_high' — mapped here so lookups never silently fail.
   */
  normalizeEffortKey(level) {
    return level === 'ultra_high' ? 'ultra' : level;
  },

  /**
   * Normalizes a multiplier spec into the internal shape:
   * { intelDelta, eloDelta, stemDelta, tokenMult }.
   * Supports BOTH the data.js schema (intel_delta/code_delta/token_multiplier)
   * and the richer app schema (coding_elo_delta/stem_delta/token_cost_multiplier),
   * so future data regenerations can't silently produce NaN again.
   */
  normalizeMultiplier(mult) {
    if (!mult || typeof mult !== 'object') return { intelDelta: 0, eloDelta: 0, stemDelta: 0, tokenMult: 1 };
    return {
      intelDelta: Number(mult.intel_delta) || 0,
      // code_delta (data.js schema) and coding_elo_delta (legacy) carry the same semantic
      eloDelta: (mult.coding_elo_delta !== undefined) ? (Number(mult.coding_elo_delta) || 0) : (Number(mult.code_delta) || 0),
      // No explicit stem delta in data.js schema — approximate with the code delta (effort scales
      // hard coding and Olympiad math together, per docs/layers/02). Legacy stem_delta wins if present.
      stemDelta: (mult.stem_delta !== undefined) ? (Number(mult.stem_delta) || 0) : ((Number(mult.code_delta) || 0)),
      tokenMult: (mult.token_cost_multiplier !== undefined) ? (Number(mult.token_cost_multiplier) || 1) : (Number(mult.token_multiplier) || 1)
    };
  },

  recalculateEffortScores() {
    this.catalog.forEach(m => {
      const activeEffort = this.modelEffortOverrides[m.id] || this.globalEffort;
      const sim = m.effort_simulation;
      const rawMult = (sim && sim.multipliers && sim.multipliers[this.normalizeEffortKey(activeEffort)]) ? sim.multipliers[this.normalizeEffortKey(activeEffort)] : null;
      const mult = this.normalizeMultiplier(rawMult);

      const baseIntel = m.scores ? m.scores.intelligence_index : 30;
      const basePower = m.scores ? m.scores.coding_power : 50;
      const baseElo = m.scores ? m.scores.code_arena_elo : 1200;
      const baseStem = m.scores ? m.scores.stem_accuracy_pct : 50;

      m.effective_scores = {
        intelligence_index: Math.max(10, Math.min(62, Number((baseIntel + mult.intelDelta).toFixed(1)))),
        coding_power: Math.max(20, Math.min(100, Math.round(basePower + (mult.eloDelta / 4)))),
        code_arena_elo: Math.max(1000, Math.min(1500, baseElo + mult.eloDelta)),
        stem_accuracy_pct: Math.max(30, Math.min(100, Number((baseStem + mult.stemDelta).toFixed(1))))
      };

      const baseCompl = m.pricing ? m.pricing.completion_per_m : 0;
      m.effective_pricing = {
        completion_per_m: Number((baseCompl * mult.tokenMult).toFixed(4))
      };
    });
  },

  setGlobalEffort(level) {
    this.globalEffort = level;
    this.modelEffortOverrides = {}; // Reset per-model overrides to align with global preset
    this.recalculateEffortScores();
    this.updateEffortAdvisory();
    this.applyFiltersAndRender();
    this.showToast(`Global reasoning effort set to ${level.toUpperCase()}!`);
  },

  setModelEffort(modelId, level) {
    this.modelEffortOverrides[modelId] = level;
    this.recalculateEffortScores();
    this.updateEffortAdvisory();
    this.applyFiltersAndRender();
    const model = this.catalog.find(m => m.id === modelId);
    this.showToast(`Effort for ${model ? model.name : modelId} set to ${level.toUpperCase()}!`);
  },

  updateEffortAdvisory() {
    const textEl = document.getElementById('effortAdvisoryText');
    if (!textEl) return;

    const isHigh = (effort) => (effort === 'high' || effort === 'ultra_high');

    // Models flagged with high overthinking-regression risk by the sync pipeline
    const riskyModels = this.catalog.filter(m => m.effort_simulation && m.effort_simulation.overthinking_risk &&
      /high/i.test(String(m.effort_simulation.overthinking_risk).slice(0, 30)));
    const riskyNames = riskyModels.slice(0, 4).map(m => m.name).join(', ');
    const riskySuffix = riskyModels.length > 4 ? ` (+${riskyModels.length - 4} more)` : '';

    // Only show the warning when at least one *visible* model is under high/ultra effort
    const highEffortRisky = this.getFilteredModels().filter(m => isHigh(this.modelEffortOverrides[m.id] || this.globalEffort));

    if (highEffortRisky.length > 0 && riskyModels.length > 0) {
      textEl.innerHTML = `⚠️ <strong>Overthinking Advisory Active:</strong> ${riskyNames}${riskySuffix} experience loop penalties and regression (-15 to -25 ELO) under High/Ultra reasoning effort. High/Ultra effort is recommended only for Frontier reasoning architectures (Opus 5.5, Sonnet 5.5, GPT-6 Astra, Argon). ${highEffortRisky.length} active model(s) currently under High/Ultra effort.`;
      textEl.parentElement.style.borderColor = '#ef4444';
      textEl.parentElement.style.background = 'rgba(239, 68, 68, 0.12)';
    } else {
      textEl.innerHTML = `💡 <strong>Reasoning Effort Simulation:</strong> Test-time compute multipliers adjust benchmarks dynamically. Higher effort scales Frontier reasoning architectures by +5 to +8 points on Olympiad math and hard coding, but increases completion token usage up to 3.2x.`;
      textEl.parentElement.style.borderColor = 'rgba(245, 158, 11, 0.35)';
      textEl.parentElement.style.background = 'rgba(245, 158, 11, 0.1)';
    }
  },

  // ----------------------------------------------------
  // Dynamic Column Manager Subsystem
  // ----------------------------------------------------
  toggleColManager() {
    const menu = document.getElementById('colManagerMenu');
    if (menu) {
      menu.style.display = (menu.style.display === 'flex' ? 'none' : 'flex');
    }
  },

  renderColManagerMenu() {
    const list = document.getElementById('colManagerList');
    if (!list) return;

    list.innerHTML = window.MatrixTable.columns.map(col => {
      const isChecked = window.MatrixTable.visibleColumns.has(col.key);
      return `
        <label class="col-manager-item">
          <input type="checkbox" value="${col.key}" ${isChecked ? 'checked' : ''} onchange="window.MatrixApp.toggleColumn('${col.key}')">
          <span>${col.label}</span>
        </label>
      `;
    }).join('');
  },

  toggleColumn(colKey) {
    window.MatrixTable.toggleColumn(colKey);
    this.renderColManagerMenu();
  },

  applyColPreset(presetName) {
    window.MatrixTable.applyPreset(presetName);
    this.renderColManagerMenu();
    this.showToast(`Applied "${presetName.toUpperCase()}" column preset!`);
  },

  toggleInlineDelta(checkbox) {
    window.MatrixTable.showInlineDelta = checkbox ? checkbox.checked : !window.MatrixTable.showInlineDelta;
    this.applyFiltersAndRender();
  },

  // ----------------------------------------------------
  // Filtering & Model Selection Engine
  // ----------------------------------------------------
  getFilteredModels() {
    return this.catalog.filter(m => {
      if (!this.selectedModelIds.has(m.id)) return false;

      // Quick filter
      if (this.currentQuickFilter === 'frontier' && m.classification !== 'Frontier') return false;
      if (this.currentQuickFilter === 'oss' && m.classification !== 'Open-Source') return false;
      if (this.currentQuickFilter === 'free' && (!m.pricing || !m.pricing.is_free)) return false;
      if (this.currentQuickFilter === 'budget' && (!m.pricing || m.pricing.prompt_per_m > 1)) return false;

      // Family Filter
      if (this.currentFamilyFilter !== 'all') {
        if (m.provider_family !== this.currentFamilyFilter) return false;
      }

      // 5% Frontier Tier Filter
      if (this.currentTierFilter !== 'all') {
        if (this.currentTierFilter === 'tier1' && !m.frontier_tier.includes('Tier 1')) return false;
        if (this.currentTierFilter === 'tier2' && !m.frontier_tier.includes('Tier 2')) return false;
        if (this.currentTierFilter === 'tier3' && !m.frontier_tier.includes('Tier 3')) return false;
        if (this.currentTierFilter === 'tier4' && !m.frontier_tier.includes('Tier 4')) return false;
        if (this.currentTierFilter === 'tier5' && !m.frontier_tier.includes('Tier 5')) return false;
      }

      // Search Query
      if (this.searchQuery) {
        const matchName = (m.name || '').toLowerCase().includes(this.searchQuery);
        const matchProvider = (m.provider || '').toLowerCase().includes(this.searchQuery);
        const matchFamily = (m.provider_family || '').toLowerCase().includes(this.searchQuery);
        const matchAccess = (m.quota_and_access || '').toLowerCase().includes(this.searchQuery);
        if (!matchName && !matchProvider && !matchFamily && !matchAccess) return false;
      }

      return true;
    });
  },

  applyFiltersAndRender() {
    const models = this.getFilteredModels();

    // Render Table & Chart modules
    window.MatrixTable.render(models);
    window.MatrixCharts.render(models);

    // Update stats bar
    const statTotal = document.getElementById('statTotalCount');
    if (statTotal) statTotal.innerText = models.length;

    const countBadge = document.getElementById('selectedCountBadge');
    if (countBadge) countBadge.innerText = this.selectedModelIds.size;
  },

  setQuickFilter(type, element) {
    this.currentQuickFilter = type;
    document.querySelectorAll('.filter-pill-quick').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    this.applyFiltersAndRender();
  },

  setFamilyFilter(family, element) {
    this.currentFamilyFilter = family;
    document.querySelectorAll('.filter-pill-family').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    this.applyFiltersAndRender();
  },

  setTierFilter(tier, element) {
    this.currentTierFilter = tier;
    document.querySelectorAll('.filter-pill-tier').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    this.applyFiltersAndRender();
  },

  // Modal Checklist Drawer
  renderModalChecklist() {
    const container = document.getElementById('modalModelList');
    if (!container) return;

    const filteredForModal = this.catalog.filter(m => {
      if (this.modalFamilyFilter !== 'all' && m.provider_family !== this.modalFamilyFilter) return false;
      if (this.modalTierFilter !== 'all') {
        if (this.modalTierFilter === 'tier1' && !m.frontier_tier.includes('Tier 1')) return false;
        if (this.modalTierFilter === 'tier2' && !m.frontier_tier.includes('Tier 2')) return false;
        if (this.modalTierFilter === 'tier3' && !m.frontier_tier.includes('Tier 3')) return false;
        if (this.modalTierFilter === 'tier4' && !m.frontier_tier.includes('Tier 4')) return false;
        if (this.modalTierFilter === 'tier5' && !m.frontier_tier.includes('Tier 5')) return false;
      }
      if (this.modalSearchQuery) {
        const match = (m.name + ' ' + m.provider_family + ' ' + m.classification).toLowerCase();
        if (!match.includes(this.modalSearchQuery)) return false;
      }
      return true;
    });

    container.innerHTML = filteredForModal.map(m => {
      const tierBadgeClass = m.frontier_tier.includes('Tier 1') ? 'badge-tier1' :
                             m.frontier_tier.includes('Tier 2') ? 'badge-tier2' :
                             m.frontier_tier.includes('Tier 3') ? 'badge-tier3' :
                             m.frontier_tier.includes('Tier 4') ? 'badge-tier4' : 'badge-tier5';

      return `
        <label class="model-check-item">
          <div class="model-check-item-header">
            <input type="checkbox" value="${m.id}" ${this.selectedModelIds.has(m.id) ? 'checked' : ''} onchange="window.MatrixApp.toggleModel('${m.id}', this.checked)">
            <span style="font-weight: 600; color: #f8fafc;">${m.name}</span>
          </div>
          <div class="model-check-item-badges">
            <span class="badge ${tierBadgeClass}">${m.frontier_tier.split(' ')[0]} (${m.frontier_delta_pct}%)</span>
            <span class="badge" style="background: rgba(255,255,255,0.06); color: #94a3b8;">${m.provider_family}</span>
            ${m.pricing && m.pricing.is_free ? '<span class="badge badge-free">FREE</span>' : '<span style="font-size:0.75rem; color:#f59e0b; margin-left:auto;">$' + m.pricing.prompt_per_m + '/M</span>'}
          </div>
        </label>
      `;
    }).join('');

    this.updateModalCounts();
  },

  setModalFamilyFilter(fam, element) {
    this.modalFamilyFilter = fam;
    document.querySelectorAll('.modal-family-pill').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    this.renderModalChecklist();
  },

  setModalTierFilter(tier, element) {
    this.modalTierFilter = tier;
    document.querySelectorAll('.modal-tier-pill').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    this.renderModalChecklist();
  },

  updateModalCounts() {
    const modalCount = document.getElementById('modalSelectedCount');
    if (modalCount) modalCount.innerText = this.selectedModelIds.size;
    const badge = document.getElementById('selectedCountBadge');
    if (badge) badge.innerText = this.selectedModelIds.size;
  },

  toggleModel(id, checked) {
    if (checked) {
      this.selectedModelIds.add(id);
    } else {
      this.selectedModelIds.delete(id);
    }
    this.updateModalCounts();
    this.applyFiltersAndRender();
  },

  toggleAllModels(select) {
    if (select) {
      this.catalog.forEach(m => this.selectedModelIds.add(m.id));
    } else {
      this.selectedModelIds.clear();
    }
    this.renderModalChecklist();
    this.applyFiltersAndRender();
  },

  selectOnlyFilteredInModal() {
    const filtered = this.catalog.filter(m => {
      if (this.modalFamilyFilter !== 'all' && m.provider_family !== this.modalFamilyFilter) return false;
      if (this.modalTierFilter !== 'all') {
        if (this.modalTierFilter === 'tier1' && !m.frontier_tier.includes('Tier 1')) return false;
        if (this.modalTierFilter === 'tier2' && !m.frontier_tier.includes('Tier 2')) return false;
        if (this.modalTierFilter === 'tier3' && !m.frontier_tier.includes('Tier 3')) return false;
        if (this.modalTierFilter === 'tier4' && !m.frontier_tier.includes('Tier 4')) return false;
        if (this.modalTierFilter === 'tier5' && !m.frontier_tier.includes('Tier 5')) return false;
      }
      return true;
    });

    filtered.forEach(m => this.selectedModelIds.add(m.id));
    this.renderModalChecklist();
    this.applyFiltersAndRender();
    this.showToast(`Selected ${filtered.length} filtered models!`);
  },

  openModelDrawer() {
    const modal = document.getElementById('modelModal');
    if (modal) modal.style.display = 'flex';
  },

  closeModelDrawer(e) {
    if (e && e.target !== e.currentTarget && e.target.tagName !== 'BUTTON') return;
    const modal = document.getElementById('modelModal');
    if (modal) modal.style.display = 'none';
  },

  // Logic Recommender Engine
  runAdvisor() {
    const complexity = document.getElementById('advisorComplexity') ? document.getElementById('advisorComplexity').value : 'medium';
    const budget = document.getElementById('advisorBudget') ? document.getElementById('advisorBudget').value : 'balanced';
    const priority = document.getElementById('advisorPriority') ? document.getElementById('advisorPriority').value : 'coding';

    let primaryPick = null;
    let freePick = null;
    let reason = '';

    if (complexity === 'frontier') {
      if (budget === 'free') {
        primaryPick = this.catalog.find(m => m.id === 'meta/muse-spark-1.3') || this.catalog[0];
        freePick = primaryPick;
        reason = 'Meta Muse Spark 1.3 is the closest free model to the frontier (Code Arena ELO: 1354, #3 Global).';
      } else if (budget === 'unlimited') {
        // No budget ceiling: absolute quality wins — Opus 5.5 dominates every pillar
        primaryPick = priority === 'stem'
          ? (this.catalog.find(m => m.id === 'anthropic/claude-opus-5.5') || this.catalog.find(m => m.id === 'google/gemini-4-argon') || this.catalog[0])
          : (this.catalog.find(m => m.id === 'anthropic/claude-opus-5.5') || this.catalog[0]);
        freePick = this.catalog.find(m => m.id === 'meta/muse-spark-1.3') || this.catalog[0];
        reason = primaryPick.name + ' is the absolute frontier leader (' + primaryPick.scores.intelligence_index + ' AA Index, ELO ' + primaryPick.scores.code_arena_elo + ') with 90% prompt caching.';
      } else {
        primaryPick = priority === 'stem' ?
                      (this.catalog.find(m => m.id === 'anthropic/claude-opus-5.5') || this.catalog[0]) :
                      (this.catalog.find(m => m.id === 'anthropic/claude-sonnet-5.5') || this.catalog[0]);
        freePick = this.catalog.find(m => m.id === 'meta/muse-spark-1.3') || this.catalog[0];
        reason = primaryPick.name + ' offers frontier reasoning (' + primaryPick.scores.intelligence_index + ' AA Index) at the best quality-per-dollar with 90% prompt caching.';
      }
    } else if (complexity === 'medium') {
      if (budget === 'free') {
        primaryPick = this.catalog.find(m => m.id === 'meta/muse-spark-1.3') || this.catalog[0];
        freePick = primaryPick;
        reason = '100% Free in Open Code with frontier-grade code comprehension and 1M context.';
      } else if (budget === 'budget') {
        primaryPick = this.catalog.find(m => m.id === 'z-ai/glm-5.3') || this.catalog.find(m => m.id === 'anthropic/claude-haiku-5.5') || this.catalog[0];
        freePick = this.catalog.find(m => m.id === 'z-ai/glm-5.3-flash') || this.catalog[0];
        reason = primaryPick.name + ' provides near-frontier performance at an ultra-low rate of $' + primaryPick.pricing.prompt_per_m + '/M.';
      } else {
        primaryPick = this.catalog.find(m => m.id === 'anthropic/claude-sonnet-5.5') || this.catalog[0];
        freePick = this.catalog.find(m => m.id === 'meta/muse-spark-1.3') || this.catalog[0];
        reason = 'Claude Sonnet 5.5 is the global engineering gold standard with 91 Coding Power.';
      }
    } else { // routine
      if (budget === 'free') {
        primaryPick = this.catalog.find(m => m.id === 'z-ai/glm-5.3-flash') || this.catalog.find(m => m.id === 'deepseek/deepseek-v4.1-flash-1017') || this.catalog[0];
        freePick = primaryPick;
        reason = 'Zero-latency formatting and linting completely free in Open Code.';
      } else {
        primaryPick = this.catalog.find(m => m.id === 'anthropic/claude-haiku-5.5') || this.catalog.find(m => m.id === 'openai/gpt-5.6-terra') || this.catalog[0];
        freePick = this.catalog.find(m => m.id === 'z-ai/glm-5.3-flash') || this.catalog[0];
        reason = primaryPick.name + ' runs at micro-tier pricing ($' + (primaryPick.pricing ? primaryPick.pricing.prompt_per_m : 0.15) + '/M) with rapid sub-second responses.';
      }
    }

    const titleEl = document.getElementById('advisorPickTitle');
    const reasonEl = document.getElementById('advisorPickReason');
    const freeEl = document.getElementById('advisorFreeTitle');

    if (titleEl) titleEl.innerText = primaryPick ? primaryPick.name : 'Claude Sonnet 5.5';
    if (reasonEl) reasonEl.innerText = reason;
    if (freeEl) freeEl.innerText = freePick ? freePick.name : 'Meta Muse Spark 1.3';

    this.currentAdvisorRecommendation = { primary: primaryPick, free: freePick };
  },

  applyAdvisorPicks() {
    if (!this.currentAdvisorRecommendation) this.runAdvisor();
    const { primary, free } = this.currentAdvisorRecommendation;

    this.selectedModelIds.clear();
    if (primary) this.selectedModelIds.add(primary.id);
    if (free) this.selectedModelIds.add(free.id);

    // Also add top 3 comparison models for context
    const opus = this.catalog.find(m => m.id === 'anthropic/claude-opus-5.5');
    if (opus) this.selectedModelIds.add(opus.id);

    this.renderModalChecklist();
    this.applyFiltersAndRender();

    // Switch to Radar Chart
    const radarTab = document.querySelector('button[onclick*="radar"]');
    if (radarTab) window.MatrixCharts.switchTab('radar', this.getFilteredModels(), radarTab);

    this.showToast(`Filtered to Advisor picks: ${primary.name} & ${free.name}!`);
  },

  // 30 Real-World Tasks Table
  renderTasksTable() {
    const tbody = document.getElementById('tasksTableBody');
    if (!tbody) return;

    // Derive real pricing from the Sonnet 5.5 catalog entry (fallback to the documented $2/$10 rates)
    const sonnet = this.catalog.find(m => m.id === 'anthropic/claude-sonnet-5.5');
    const sp = sonnet && sonnet.pricing ? sonnet.pricing : { prompt_per_m: 2, completion_per_m: 10, cache_read_per_m: 0.1 };
    const pRate = sp.prompt_per_m / 1e6;       // uncached prompt rate
    const cRate = sp.completion_per_m / 1e6;   // completion rate
    const crRate = (sp.cache_read_per_m || sp.prompt_per_m * 0.1) / 1e6; // cached prompt rate

    tbody.innerHTML = this.tasks.map(t => {
      const tierBadge = t.tier === 'Simple' ? 'task-tier-simple' :
                        t.tier === 'Medium' ? 'task-tier-medium' : 'task-tier-exclusive';

      // Cost comparison: Free Model ($0), Budget Model ($0.10/M prompt, $0.50/M completion), Frontier Sonnet with/out caching
      const budgetCost = ((t.promptTok * 0.0000001) + (t.complTok * 0.0000005)).toFixed(4);
      const frontierBaseCost = ((t.promptTok * pRate) + (t.complTok * cRate)).toFixed(3);
      const frontierCachedCost = (((t.promptTok - t.cachedTok) * pRate) + (t.cachedTok * crRate) + (t.complTok * cRate)).toFixed(3);

      return `
        <tr>
          <td><span class="task-tier-badge ${tierBadge}">${t.tier}</span></td>
          <td>
            <div style="font-weight:600; color:#f8fafc;">#${t.id}: ${t.name}</div>
            <div style="font-size:0.75rem; color:var(--text-muted);">${t.desc}</div>
          </td>
          <td style="font-family:monospace; color:#93c5fd;">${(t.promptTok).toLocaleString()}</td>
          <td style="font-family:monospace; color:#c084fc;">${(t.complTok).toLocaleString()}</td>
          <td style="font-family:monospace; color:#34d399;">${(t.cachedTok).toLocaleString()}</td>
          <td style="font-weight:700; color:#10b981;">$0.00 <span style="font-size:0.7rem; color:var(--text-muted);">(${t.freeModel})</span></td>
          <td style="font-family:monospace; color:#38bdf8;">$${budgetCost}</td>
          <td style="font-family:monospace; color:#fbbf24;">$${frontierCachedCost} <span style="font-size:0.7rem; color:#94a3b8; text-decoration:line-through;">$${frontierBaseCost}</span></td>
          <td><span class="badge" style="background:rgba(99,102,241,0.2); color:#a5b4fc; border:1px solid #6366f1;">${t.recModel}</span></td>
        </tr>
      `;
    }).join('');
  },

  // Toast
  showToast(msg) {
    const toast = document.getElementById('toastMessage');
    if (!toast) return;
    toast.innerText = msg;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 2800);
  },

  // Export Tools
  copyObsidianMarkdown() {
    const models = this.getFilteredModels();
    let md = `| Model Name | Family | Class | Frontier Tier | Delta % | Dec Top % | Dual Fact-Check | Context | Intel (AA) | Coding Power | Code ELO | STEM % | Prompt/M | Compl/M | Cache Read/M | Free? | Quota / Access Point |\n`;
    md += `| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |\n`;

    // Baseline is the catalog ELO peak (Opus 5.5 = 0.0% by invariant); falls back dynamically if data changes
    const topElo = Math.max(...models.map(m => (m.effective_scores || m.scores).code_arena_elo), 1391);
    models.forEach(m => {
      const scores = m.effective_scores || m.scores;
      const isFree = (m.pricing && m.pricing.is_free) ? '**FREE**' : 'Paid';
      const promptP = m.pricing ? m.pricing.prompt_per_m : 0;
      const complP = m.effective_pricing ? m.effective_pricing.completion_per_m : (m.pricing ? m.pricing.completion_per_m : 0);
      const cacheP = m.pricing ? m.pricing.cache_read_per_m : 0;
      const decTop = (((scores.code_arena_elo - topElo) / topElo) * 100).toFixed(1) + '%';
      const fc = (m.fact_check && m.fact_check.is_verified) ? '✓ Concordant (OR+Dev)' : '✓ OR Verified';
      md += `| **${m.name}** | ${m.provider_family || m.provider} | ${m.classification} | ${m.frontier_tier} | ${m.frontier_delta_pct}% | ${decTop} | ${fc} | ${m.context_window} | **${scores.intelligence_index}** | **${scores.coding_power}** | **${scores.code_arena_elo}** | **${scores.stem_accuracy_pct}%** | $${promptP} | $${complP} | $${cacheP} | ${isFree} | ${m.quota_and_access || 'N/A'} |\n`;
    });

    navigator.clipboard.writeText(md).then(() => {
      this.showToast(`Copied ${models.length} models as Obsidian Markdown Table!`);
    }).catch(() => {
      this.showToast('Failed to copy. Please check clipboard permissions.');
    });
  },

  downloadCSV() {
    const models = this.getFilteredModels();
    const headers = ["ID","Name","Provider","Provider_Family","Classification","Frontier_Tier","Frontier_Delta_Pct","Context","Context_Tokens","Intel_Index","Coding_Power","Code_Arena_ELO","STEM_Pct","Prompt_Per_M","Completion_Per_M","Cache_Read_Per_M","Batch_Prompt_Per_M","Is_Free","Dual_Fact_Check","Pricing_Concordance","Quota_Access"];
    const rows = models.map(m => {
      const scores = m.effective_scores || m.scores;
      const complPrice = m.effective_pricing ? m.effective_pricing.completion_per_m : (m.pricing ? m.pricing.completion_per_m : 0);
      const factStatus = m.fact_check ? m.fact_check.status : "Verified via OpenRouter API";
      const pricingConcordance = (m.fact_check && m.fact_check.pricing_concordance) ? m.fact_check.pricing_concordance : "N/A";
      // Excel-safe quoting: escape embedded double quotes per RFC 4180
      const q = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
      return [
        q(m.id), q(m.name), q(m.provider), q(m.provider_family), q(m.classification),
        q(m.frontier_tier), m.frontier_delta_pct, q(m.context_window), m.context_tokens,
        scores.intelligence_index, scores.coding_power, scores.code_arena_elo, scores.stem_accuracy_pct,
        m.pricing ? m.pricing.prompt_per_m : 0, complPrice,
        m.pricing ? m.pricing.cache_read_per_m : 0, m.pricing ? m.pricing.batch_prompt_per_m : 0,
        m.pricing ? m.pricing.is_free : false, q(factStatus), q(pricingConcordance), q(m.quota_and_access || '')
      ];
    });

    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai_models_matrix_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    this.showToast('Exported CSV file successfully!');
  },

  downloadJSON() {
    const models = this.getFilteredModels();
    const jsonContent = JSON.stringify({
      metadata: {
        exported_at: new Date().toISOString(),
        version: "1.3.1",
        count: models.length,
        sources: ["OpenRouter API", "Models.dev API", "Artificial Analysis"],
        capability_cutoff: "Gemini 3.5 Pro/Flash Baseline (Code Arena ELO >= 1279)",
        global_effort: this.globalEffort
      },
      models: models
    }, null, 2);

    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai_models_matrix_${new Date().toISOString().slice(0,10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    this.showToast('Exported JSON file successfully!');
  },

  handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        if (data && data.models && Array.isArray(data.models)) {
          this.catalog = data.models;
          this.selectedModelIds = new Set(this.catalog.map(m => m.id));
          this.recalculateEffortScores();
          this.renderModalChecklist();
          this.applyFiltersAndRender();
          this.runAdvisor();
          this.showToast(`Loaded ${this.catalog.length} models from ${file.name}!`);
        } else {
          alert('Invalid catalog JSON format. Expected { models: [...] } structure.');
        }
      } catch (err) {
        alert('Error parsing JSON file: ' + err.message);
      }
    };
    reader.readAsText(file);
  }
};

// Auto-boot on DOM Ready
window.addEventListener('DOMContentLoaded', () => {
  window.MatrixApp.init();
});
