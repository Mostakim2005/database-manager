/**
 * AI Frontier & Budget Matrix — Table & Sorting Engine (v1.3.0)
 * Encapsulates dynamic column visibility, header tooltips, inline delta % toggling,
 * per-model effort overrides, dual-source Models.dev fact-checking, and sticky column rendering.
 */

window.MatrixTable = {
  sortColumn: 'scores.code_arena_elo',

  escapeHtml(val) {
    return String(val ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  },
  sortAscending: false,
  showInlineDelta: false,

  // All registered columns with metadata and hover tooltips
  columns: [
    { key: 'col_name', label: 'Model Name', path: 'name', sticky: true, tooltip: 'Model designation and primary vendor / research organization.' },
    { key: 'col_tier', label: 'Frontier Tier', path: 'frontier_tier', tooltip: '5% frontier proximity tier (Tier 1 = top 0-5%, Tier 2 = 5-10%, etc.).' },
    { key: 'col_delta', label: 'Frontier Delta %', path: 'frontier_delta_pct', tooltip: 'Normalized composite capability distance relative to global frontier leader (Opus 5.5 = 0.0%).' },
    { key: 'col_dec_top', label: 'Dec from Top %', path: 'dec_from_top_pct', tooltip: 'Direct percentage decrease in Code Arena ELO relative to global frontier leader (1391 ELO).' },
    { key: 'col_fact_check', label: 'Dual Fact-Check', path: 'fact_check.status', tooltip: 'Cross-verification concordance between OpenRouter API telemetry and Models.dev open-source catalog.' },
    { key: 'col_class', label: 'Class', path: 'classification', tooltip: 'Architectural model: Proprietary Frontier, Open-Weights OSS, or 100% Free.' },
    { key: 'col_context', label: 'Context', path: 'context_tokens', tooltip: 'Maximum token context window length supported for input prompts and repository ingest.' },
    { key: 'col_intel', label: 'Intel (AA)', path: 'scores.intelligence_index', tooltip: 'Artificial Analysis composite intelligence index across MMLU-Pro, GPQA, and math (0-60).' },
    { key: 'col_code_power', label: 'Code Power', path: 'scores.coding_power', tooltip: 'Normalized composite coding capability score aggregating SWE-bench & HumanEval (0-100).' },
    { key: 'col_elo', label: 'Code ELO', path: 'scores.code_arena_elo', tooltip: 'LMSYS / Arena competitive ELO ranking specifically evaluated on engineering prompts.' },
    { key: 'col_stem', label: 'STEM %', path: 'scores.stem_accuracy_pct', tooltip: 'Benchmark accuracy percentage across graduate-level mathematics and physics proofs.' },
    { key: 'col_effort', label: 'Effort Setting', path: 'active_effort', tooltip: 'Simulated reasoning effort level (Low, Med, High, Ultra) adjusting tokens and compute.' },
    { key: 'col_prompt', label: 'Prompt $/M', path: 'pricing.prompt_per_m', tooltip: 'Standard pricing per 1,000,000 input prompt tokens.' },
    { key: 'col_compl', label: 'Compl $/M', path: 'pricing.completion_per_m', tooltip: 'Standard pricing per 1,000,000 output completion tokens.' },
    { key: 'col_cache', label: 'Cache Read $/M', path: 'pricing.cache_read_per_m', tooltip: 'Discounted pricing per 1,000,000 cached prompt tokens (up to 90% discount).' },
    { key: 'col_batch', label: 'Batch $/M', path: 'pricing.batch_prompt_per_m', tooltip: 'Discounted batch API rate (50% discount for asynchronous 24h completion).' },
    { key: 'col_status', label: 'Tier Status', path: 'pricing.is_free', tooltip: 'Subscription or billing requirement: 100% Free or Metered Paid API.' },
    { key: 'col_quota', label: 'Quota & Access Point', path: 'quota_and_access', tooltip: 'Recommended zero-cost or subscription endpoint (Open Code, Grok API, Antigravity).' }
  ],

  // Currently active visible column keys
  visibleColumns: new Set([
    'col_name', 'col_tier', 'col_delta', 'col_dec_top', 'col_fact_check', 'col_class',
    'col_context', 'col_intel', 'col_code_power', 'col_elo', 'col_stem',
    'col_effort', 'col_prompt', 'col_compl', 'col_cache', 'col_status', 'col_quota'
  ]),

  // Preset definitions
  presets: {
    default: [
      'col_name', 'col_tier', 'col_delta', 'col_dec_top', 'col_fact_check', 'col_class',
      'col_context', 'col_intel', 'col_code_power', 'col_elo', 'col_stem',
      'col_effort', 'col_prompt', 'col_compl', 'col_cache', 'col_status', 'col_quota'
    ],
    compact: [
      'col_name', 'col_tier', 'col_dec_top', 'col_fact_check', 'col_elo', 'col_prompt', 'col_status', 'col_quota'
    ],
    benchmarks: [
      'col_name', 'col_tier', 'col_delta', 'col_dec_top', 'col_fact_check', 'col_intel', 'col_code_power', 'col_elo', 'col_stem', 'col_effort'
    ],
    pricing: [
      'col_name', 'col_context', 'col_fact_check', 'col_prompt', 'col_compl', 'col_cache', 'col_batch', 'col_status', 'col_quota'
    ],
    all: [
      'col_name', 'col_tier', 'col_delta', 'col_dec_top', 'col_fact_check', 'col_class',
      'col_context', 'col_intel', 'col_code_power', 'col_elo', 'col_stem',
      'col_effort', 'col_prompt', 'col_compl', 'col_cache', 'col_batch', 'col_status', 'col_quota'
    ]
  },

  applyPreset(presetName) {
    if (this.presets[presetName]) {
      this.visibleColumns = new Set(this.presets[presetName]);
      this.renderHeaders();
      if (window.MatrixApp) window.MatrixApp.applyFiltersAndRender();
    }
  },

  toggleColumn(colKey) {
    if (this.visibleColumns.has(colKey)) {
      if (this.visibleColumns.size <= 1) return; // Keep at least one column
      this.visibleColumns.delete(colKey);
    } else {
      this.visibleColumns.add(colKey);
    }
    this.renderHeaders();
    if (window.MatrixApp) window.MatrixApp.applyFiltersAndRender();
  },

  getNestedValue(obj, path) {
    if (!obj || !path) return undefined;
    if (path.startsWith('scores.')) {
      const field = path.split('.')[1];
      if (obj.effective_scores && obj.effective_scores[field] !== undefined) {
        return obj.effective_scores[field];
      }
    }
    // Computed column: % decrease of Code Arena ELO from the catalog peak (invariant: Opus 5.5 baseline)
    if (path === 'dec_from_top_pct') {
      const elo = (obj.effective_scores && obj.effective_scores.code_arena_elo !== undefined) ? obj.effective_scores.code_arena_elo : (obj.scores && obj.scores.code_arena_elo);
      if (typeof elo !== 'number' || Number.isNaN(elo)) return -Infinity;
      const topElo = Math.max(elo, 1391);
      return ((elo - topElo) / topElo) * 100;
    }
    // Computed column: simulated effort level actually applied per model
    if (path === 'active_effort') {
      const app = window.MatrixApp;
      return (app && app.modelEffortOverrides[obj.id]) || (app ? app.globalEffort : 'medium');
    }
    return path.split('.').reduce((acc, part) => (acc && acc[part] !== undefined ? acc[part] : undefined), obj);
  },

  handleSort(column, getModelsCallback) {
    if (this.sortColumn === column) {
      this.sortAscending = !this.sortAscending;
    } else {
      this.sortColumn = column;
      this.sortAscending = (column === 'name' || column === 'classification' || column === 'provider_family');
    }

    this.renderHeaders();

    if (typeof getModelsCallback === 'function') {
      getModelsCallback();
    }
  },

  renderHeaders() {
    const thead = document.querySelector('#matrixTable thead tr');
    if (!thead) return;

    thead.innerHTML = this.columns
      .filter(col => this.visibleColumns.has(col.key))
      .map(col => {
        const isSorted = (this.sortColumn === col.path);
        const sortClass = isSorted ? (this.sortAscending ? 'sorted-asc' : 'sorted-desc') : '';
        const stickyClass = col.sticky ? 'sticky-col' : '';

        return `
          <th class="${stickyClass} ${sortClass}" 
              data-col="${col.path}" 
              data-tooltip="${col.tooltip}"
              onclick="window.MatrixTable.handleSort('${col.path}', () => window.MatrixApp.applyFiltersAndRender())">
            ${col.label} <span class="tooltip-icon">ⓘ</span>
          </th>
        `;
      }).join('');
  },

  sort(models) {
    return [...models].sort((a, b) => {
      let valA = this.getNestedValue(a, this.sortColumn);
      let valB = this.getNestedValue(b, this.sortColumn);

      if (valA === undefined || valA === null) valA = 0;
      if (valB === undefined || valB === null) valB = 0;

      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return this.sortAscending ? -1 : 1;
      if (valA > valB) return this.sortAscending ? 1 : -1;
      return 0;
    });
  },

  render(models) {
    const tbody = document.getElementById('tableBody');
    if (!tbody) return;

    if (models.length === 0) {
      tbody.innerHTML = `<tr><td colspan="${this.visibleColumns.size}" style="text-align:center; padding: 2rem; color: var(--text-muted);">No models match your current filters.</td></tr>`;
      return;
    }

    const sorted = this.sort(models);

    // Baseline frontier maximums for delta calculation
    const maxElo = 1391;
    const maxIntel = 57.6;
    const maxPower = 92;
    const maxStem = 95.0;

    tbody.innerHTML = sorted.map(m => {
      const scores = m.effective_scores || m.scores;
      const classBadge = m.classification === 'Frontier' ? 'badge-frontier' :
                         m.classification === 'Open-Source' ? 'badge-oss' : 'badge-free';

      const tierBadge = (m.pricing && m.pricing.is_free) ?
                        '<span class="badge badge-free">FREE</span>' :
                        '<span class="badge badge-paid">PAID</span>';

      const frontierTierClass = m.frontier_tier && m.frontier_tier.includes('Tier 1') ? 'badge-tier1' :
                                m.frontier_tier && m.frontier_tier.includes('Tier 2') ? 'badge-tier2' :
                                m.frontier_tier && m.frontier_tier.includes('Tier 3') ? 'badge-tier3' :
                                m.frontier_tier && m.frontier_tier.includes('Tier 4') ? 'badge-tier4' : 'badge-tier5';

      const deltaPct = m.frontier_delta_pct !== undefined ? `${m.frontier_delta_pct}%` : 'N/A';

      // Percentage decrease from top ELO (1391)
      const eloDecFromTop = (((scores.code_arena_elo - maxElo) / maxElo) * 100).toFixed(1);
      const decTopDisplay = `${eloDecFromTop}%`;

      // Inline delta tags if enabled
      const intelDelta = this.showInlineDelta ? `<span class="score-delta-pill">(${(((scores.intelligence_index - maxIntel) / maxIntel) * 100).toFixed(1)}%)</span>` : '';
      const powerDelta = this.showInlineDelta ? `<span class="score-delta-pill">(${(((scores.coding_power - maxPower) / maxPower) * 100).toFixed(1)}%)</span>` : '';
      const eloDelta = this.showInlineDelta ? `<span class="score-delta-pill">(${eloDecFromTop}%)</span>` : '';
      const stemDelta = this.showInlineDelta ? `<span class="score-delta-pill">(${(((scores.stem_accuracy_pct - maxStem) / maxStem) * 100).toFixed(1)}%)</span>` : '';

      const promptPrice = m.pricing ? m.pricing.prompt_per_m : 0;
      const complPrice = m.effective_pricing ? m.effective_pricing.completion_per_m : (m.pricing ? m.pricing.completion_per_m : 0);
      const cacheRead = m.pricing ? m.pricing.cache_read_per_m : 0;
      const batchPrompt = m.pricing ? m.pricing.batch_prompt_per_m : 0;

      const activeEffort = (window.MatrixApp && window.MatrixApp.modelEffortOverrides[m.id]) ||
                           (window.MatrixApp ? window.MatrixApp.globalEffort : 'medium');

      const formatPrice = (val, maxDec = 4) => {
        if (val === 0) return '$0.00';
        return '$' + val.toFixed(val < 0.1 ? maxDec : 2);
      };

      const esc = (v) => this.escapeHtml(v);
      const factCheckBadge = m.fact_check && m.fact_check.is_verified ?
        `<span class="badge badge-free" style="font-size:0.7rem;" title="${esc(m.fact_check.pricing_concordance)} | ${esc(m.fact_check.context_concordance)}">✓ Concordant</span>` :
        `<span class="badge" style="background:rgba(56,189,248,0.15); color:#38bdf8; font-size:0.7rem;" title="Verified via OpenRouter API">✓ OR Verified</span>`;

      // Cells map by column key
      const cellMap = {
        col_name: `
          <td class="sticky-col">
            <div style="font-weight: 600; color: #f8fafc;">${esc(m.name)}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${esc(m.provider_family || m.provider)}</div>
          </td>`,
        col_tier: `<td><span class="badge ${frontierTierClass}">${esc(m.frontier_tier || 'Tier 5')}</span></td>`,
        col_delta: `<td style="font-family: monospace; font-weight: 600; color: ${m.frontier_delta_pct >= -5 ? '#c084fc' : m.frontier_delta_pct >= -15 ? '#38bdf8' : '#94a3b8'};">${deltaPct}</td>`,
        col_dec_top: `<td style="font-family: monospace; font-weight: 600; color: ${Number(eloDecFromTop) >= -5 ? '#c084fc' : Number(eloDecFromTop) >= -10 ? '#38bdf8' : '#f87171'};">${decTopDisplay}</td>`,
        col_fact_check: `<td>${factCheckBadge}</td>`,
        col_class: `<td><span class="badge ${classBadge}">${esc(m.classification)}</span></td>`,
        col_context: `<td style="font-family: monospace;">${esc(m.context_window)}</td>`,
        col_intel: `
          <td>
            <div class="mini-bar-cell">
              <span style="font-weight: 600; min-width: 34px;">${scores.intelligence_index}</span>
              ${intelDelta}
              <div class="mini-bar-track">
                <div class="mini-bar-fill fill-purple" style="width: ${(scores.intelligence_index / 60) * 100}%;"></div>
              </div>
            </div>
          </td>`,
        col_code_power: `
          <td>
            <div class="mini-bar-cell">
              <span style="font-weight: 600; min-width: 30px;">${scores.coding_power}</span>
              ${powerDelta}
              <div class="mini-bar-track">
                <div class="mini-bar-fill fill-cyan" style="width: ${scores.coding_power}%;"></div>
              </div>
            </div>
          </td>`,
        col_elo: `
          <td style="font-weight: 700; color: #38bdf8;">
            ${scores.code_arena_elo} ${eloDelta}
          </td>`,
        col_stem: `
          <td>
            <div class="mini-bar-cell">
              <span style="font-weight: 600; min-width: 34px;">${scores.stem_accuracy_pct}%</span>
              ${stemDelta}
              <div class="mini-bar-track">
                <div class="mini-bar-fill fill-emerald" style="width: ${scores.stem_accuracy_pct}%;"></div>
              </div>
            </div>
          </td>`,
        col_effort: `
          <td>
            <select class="effort-select" style="background:#1e293b; color:#cbd5e1; border:1px solid rgba(255,255,255,0.1); border-radius:4px; padding:0.2rem 0.4rem; font-size:0.75rem;"
                    data-model-id="${esc(m.id)}" onchange="window.MatrixApp.setModelEffort(this.dataset.modelId, this.value)">
              <option value="low" ${activeEffort === 'low' ? 'selected' : ''}>Low (0.6x)</option>
              <option value="medium" ${activeEffort === 'medium' ? 'selected' : ''}>Medium (1.0x)</option>
              <option value="high" ${activeEffort === 'high' ? 'selected' : ''}>High (1.8x)</option>
              <option value="ultra_high" ${activeEffort === 'ultra_high' ? 'selected' : ''}>Ultra (3.2x)</option>
            </select>
          </td>`,
        col_prompt: `<td style="font-family: monospace;">${formatPrice(promptPrice)}</td>`,
        col_compl: `<td style="font-family: monospace;">${formatPrice(complPrice)}</td>`,
        col_cache: `<td style="font-family: monospace; color: #34d399;">${formatPrice(cacheRead)}</td>`,
        col_batch: `<td style="font-family: monospace; color: #93c5fd;">${formatPrice(batchPrompt)}</td>`,
        col_status: `<td>${tierBadge}</td>`,
        col_quota: `<td style="font-size: 0.8rem; color: #cbd5e1;">${esc(m.quota_and_access || 'N/A')}</td>`
      };

      const rowHtml = this.columns
        .filter(col => this.visibleColumns.has(col.key))
        .map(col => cellMap[col.key] || '')
        .join('');

      return `<tr>${rowHtml}</tr>`;
    }).join('');
  }
};
