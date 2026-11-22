/**
 * AI Frontier & Budget Matrix — Chart Controller Subsystem (v1.3.0)
 * Encapsulates Chart.js lifecycle: Pareto Efficiency Frontier, Reasoning Effort Trade-off,
 * Dual-Axis Coding ELO, 5-Axis Spider Radar, Cost-Performance Bubble Matrix, and Cache Savings.
 * Features dual-source Models.dev + OpenRouter verification telemetry annotations.
 */

window.MatrixCharts = {
  instance: null,
  currentTab: 'intel',

  init(models) {
    this.render(models);
  },

  switchTab(tab, models, tabElement) {
    this.currentTab = tab;
    document.querySelectorAll('.chart-tab').forEach(el => el.classList.remove('active'));
    if (tabElement) tabElement.classList.add('active');
    this.render(models);
  },

  setHeight(px) {
    const wrapper = document.getElementById('chartWrapper');
    if (wrapper) {
      wrapper.style.height = `${px}px`;
    }
    if (this.instance) {
      this.instance.resize();
    }
  },

  render(models) {
    const wrapper = document.getElementById('chartWrapper');
    if (!wrapper) return;

    if (typeof Chart === 'undefined') {
      wrapper.innerHTML = '<div style="display:flex; justify-content:center; align-items:center; height:100%; color:var(--text-muted);">Chart.js is offline. Full table and filters remain active.</div>';
      return;
    }

    const canvas = document.getElementById('mainChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (this.instance) {
      this.instance.destroy();
      this.instance = null;
    }

    const staleEmpty = document.getElementById('chartEmptyState');
    if (staleEmpty) staleEmpty.remove();

    if (models.length === 0) {
      wrapper.innerHTML = '<canvas id="mainChart"></canvas><div id="chartEmptyState" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:var(--text-muted);">No models match the selected filters.</div>';
      return;
    }

    switch (this.currentTab) {
      case 'intel':
        this.instance = this.buildIntelChart(ctx, models);
        break;
      case 'coding':
        this.instance = this.buildCodingChart(ctx, models);
        break;
      case 'stem':
        this.instance = this.buildStemChart(ctx, models);
        break;
      case 'radar':
        this.instance = this.buildRadarChart(ctx, models);
        break;
      case 'pareto':
        this.instance = this.buildParetoChart(ctx, models);
        break;
      case 'effort_tradeoff':
        this.instance = this.buildEffortTradeoffChart(ctx, models);
        break;
      case 'cost_perf':
        this.instance = this.buildCostPerfChart(ctx, models);
        break;
      case 'cache_savings':
        this.instance = this.buildCacheSavingsChart(ctx, models);
        break;
      default:
        this.instance = this.buildIntelChart(ctx, models);
    }
  },

  getModelColors(models) {
    return models.map(m => {
      if (m.pricing && m.pricing.is_free) return '#10b981';
      if (m.classification === 'Frontier') return '#a855f7';
      return '#06b6d4';
    });
  },

  buildIntelChart(ctx, models) {
    const labels = models.map(m => m.name);
    const data = models.map(m => m.effective_scores ? m.effective_scores.intelligence_index : m.scores.intelligence_index);
    const colors = this.getModelColors(models);

    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Artificial Analysis Intelligence Index (0-60 Scale)',
          data: data,
          backgroundColor: colors,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const m = models[context.dataIndex];
                const delta = m.frontier_delta_pct !== undefined ? `${m.frontier_delta_pct}%` : '0%';
                const fc = (m.fact_check && m.fact_check.is_verified) ? ' | [Dual-Verified: OR + Dev]' : '';
                return `Tier: ${m.frontier_tier || m.classification} (${delta})${fc} | Access: ${m.quota_and_access || 'N/A'}`;
              }
            }
          }
        },
        scales: {
          x: { ticks: { color: '#9ca3af', font: { size: 10 }, maxRotation: 45, minRotation: 45 }, grid: { display: false } },
          y: { min: 0, max: 62, ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.06)' } }
        }
      }
    });
  },

  buildCodingChart(ctx, models) {
    const labels = models.map(m => m.name);
    const eloData = models.map(m => m.effective_scores ? m.effective_scores.code_arena_elo : m.scores.code_arena_elo);
    const powerData = models.map(m => m.effective_scores ? m.effective_scores.coding_power : m.scores.coding_power);

    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Code Arena ELO',
            data: eloData,
            backgroundColor: '#38bdf8',
            borderRadius: 6,
            yAxisID: 'yElo'
          },
          {
            label: 'Coding Power Index (0-100)',
            data: powerData,
            backgroundColor: 'rgba(168, 85, 247, 0.7)',
            borderRadius: 6,
            yAxisID: 'yPower'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#e2e8f0' } },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const m = models[context.dataIndex];
                const delta = m.frontier_delta_pct !== undefined ? `${m.frontier_delta_pct}%` : '0%';
                const fc = (m.fact_check && m.fact_check.is_verified) ? ' | [Dual-Verified: OR + Dev]' : '';
                return `Tier: ${m.frontier_tier || m.classification} (${delta})${fc}`;
              }
            }
          }
        },
        scales: {
          x: { ticks: { color: '#9ca3af', font: { size: 10 }, maxRotation: 45, minRotation: 45 }, grid: { display: false } },
          yElo: { type: 'linear', position: 'left', min: 1100, max: 1450, ticks: { color: '#38bdf8' }, grid: { color: 'rgba(255,255,255,0.06)' } },
          yPower: { type: 'linear', position: 'right', min: 0, max: 100, ticks: { color: '#c084fc' }, grid: { display: false } }
        }
      }
    });
  },

  buildStemChart(ctx, models) {
    const labels = models.map(m => m.name);
    const stemData = models.map(m => m.effective_scores ? m.effective_scores.stem_accuracy_pct : m.scores.stem_accuracy_pct);

    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'STEM & Math Proof Accuracy (%)',
          data: stemData,
          backgroundColor: '#34d399',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const m = models[context.dataIndex];
                const delta = m.frontier_delta_pct !== undefined ? `${m.frontier_delta_pct}%` : '0%';
                const fc = (m.fact_check && m.fact_check.is_verified) ? ' | [Dual-Verified: OR + Dev]' : '';
                return `Tier: ${m.frontier_tier || m.classification} (${delta})${fc}`;
              }
            }
          }
        },
        scales: {
          x: { ticks: { color: '#9ca3af', font: { size: 10 }, maxRotation: 45, minRotation: 45 }, grid: { display: false } },
          y: { min: 40, max: 100, ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.06)' } }
        }
      }
    });
  },

  buildRadarChart(ctx, models) {
    // If more than 6 models are active, take top 6 to prevent spider chart overcrowding
    const displayModels = models.slice(0, 6);
    const radarColors = [
      { border: '#c084fc', bg: 'rgba(192, 132, 252, 0.2)' },
      { border: '#38bdf8', bg: 'rgba(56, 189, 248, 0.2)' },
      { border: '#34d399', bg: 'rgba(52, 211, 153, 0.2)' },
      { border: '#fbbf24', bg: 'rgba(251, 191, 36, 0.2)' },
      { border: '#f43f5e', bg: 'rgba(244, 63, 94, 0.2)' },
      { border: '#a855f7', bg: 'rgba(168, 85, 247, 0.2)' }
    ];

    const datasets = displayModels.map((m, idx) => {
      const color = radarColors[idx % radarColors.length];
      const scores = m.effective_scores || m.scores;
      // Guard against missing/NaN values so one bad model can't degenerate the whole radar
      const safe = (v, max) => (typeof v === 'number' && !Number.isNaN(v)) ? Math.round(Math.max(0, Math.min(100, (v / max) * 100))) : 0;
      const intelNorm = safe(scores.intelligence_index, 57.6);
      const codeNorm = safe(scores.coding_power, 92);
      const stemNorm = safe(scores.stem_accuracy_pct, 95);
      const contextNorm = Math.min(100, Math.round(((m.context_tokens || 128000) / 1000000) * 100));

      let costNorm = 100;
      if (!m.pricing || !m.pricing.is_free) {
        const cost = m.pricing ? m.pricing.prompt_per_m : 2.0;
        costNorm = Math.max(20, Math.round(100 - (cost * 7.5)));
      }

      return {
        label: m.name,
        data: [intelNorm, codeNorm, stemNorm, contextNorm, costNorm],
        borderColor: color.border,
        backgroundColor: color.bg,
        borderWidth: 2,
        pointBackgroundColor: color.border
      };
    });

    return new Chart(ctx, {
      type: 'radar',
      data: {
        labels: ['Intelligence (AA)', 'Coding Power', 'STEM Accuracy', 'Context Scale', 'Cost Efficiency'],
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#e2e8f0', font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: (context) => `${context.dataset.label}: ${context.raw}% Normalized`
            }
          }
        },
        scales: {
          r: {
            angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
            grid: { color: 'rgba(255, 255, 255, 0.08)' },
            pointLabels: { color: '#93c5fd', font: { size: 11, weight: '600' } },
            ticks: { display: false, min: 0, max: 100 }
          }
        }
      }
    });
  },

  /**
   * Pareto Efficiency Frontier (Cost vs Code Arena ELO)
   * Calculates non-dominated frontier curve (Gold) and plots all active models.
   */
  buildParetoChart(ctx, models) {
    // 1. Map model points: X = Prompt Cost ($/M), Y = Code Arena ELO
    const points = models.map(m => {
      const cost = m.pricing ? m.pricing.prompt_per_m : 0;
      const scores = m.effective_scores || m.scores;
      const elo = scores ? scores.code_arena_elo : 0;
      return {
        x: cost,
        y: elo,
        model: m
      };
    });

    // 2. Compute non-dominated Pareto Frontier:
    // A point (cost_A, elo_A) dominates (cost_B, elo_B) if cost_A <= cost_B and elo_A >= elo_B with at least one strict
    const paretoModels = [];
    points.forEach(p => {
      let dominated = false;
      for (const other of points) {
        if (other === p) continue;
        if (other.x <= p.x && other.y >= p.y && (other.x < p.x || other.y > p.y)) {
          dominated = true;
          break;
        }
      }
      if (!dominated) {
        paretoModels.push(p);
      }
    });

    // Sort Pareto points by cost ascending to draw smooth frontier line
    paretoModels.sort((a, b) => a.x - b.x);

    const paretoSet = new Set(paretoModels.map(p => p.model.id));

    // Separate into Pareto Optimal vs Dominated points for clear visual contrast
    const nonParetoPoints = points.filter(p => !paretoSet.has(p.model.id));

    return new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [
          {
            type: 'line',
            label: 'Gold Pareto Efficiency Frontier (Non-Dominated Optimal)',
            data: paretoModels.map(p => ({ x: p.x, y: p.y })),
            borderColor: '#fbbf24',
            backgroundColor: 'rgba(251, 191, 36, 0.15)',
            borderWidth: 3,
            fill: false,
            tension: 0.15,
            pointRadius: 7,
            pointHoverRadius: 9,
            pointBackgroundColor: '#fbbf24',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            order: 1
          },
          {
            type: 'scatter',
            label: 'Pareto Optimal Models',
            data: paretoModels.map(p => ({ x: p.x, y: p.y, model: p.model })),
            backgroundColor: '#fbbf24',
            pointRadius: 7,
            pointHoverRadius: 9,
            order: 2
          },
          {
            type: 'scatter',
            label: 'Sub-Frontier / Dominated Models',
            data: nonParetoPoints.map(p => ({ x: p.x, y: p.y, model: p.model })),
            backgroundColor: nonParetoPoints.map(p => (p.model.pricing && p.model.pricing.is_free ? '#10b981' : '#38bdf8')),
            pointRadius: 5,
            pointHoverRadius: 7,
            order: 3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            labels: { color: '#e2e8f0', font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const item = context.raw.model;
                if (!item) {
                  return `Frontier Vertex: $${context.raw.x}/M | ELO ${context.raw.y}`;
                }
                const isOptimal = paretoSet.has(item.id);
                const cost = item.pricing ? item.pricing.prompt_per_m : 0;
                const scores = item.effective_scores || item.scores;
                const fc = (item.fact_check && item.fact_check.is_verified) ? ' [Dual-Verified: OR + Dev]' : '';
                return [
                  `${isOptimal ? '⭐ PARETO OPTIMAL: ' : ''}${item.name} (${item.provider_family})${fc}`,
                  `Base Prompt Cost: $${cost.toFixed(2)} / 1M tokens`,
                  `Code Arena ELO: ${scores.code_arena_elo} | Coding Power: ${scores.coding_power}`,
                  `Frontier Tier: ${item.frontier_tier || item.classification} (${item.frontier_delta_pct}%)`
                ];
              }
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: 'Base Prompt Cost ($ / Million Tokens)', color: '#9ca3af' },
            ticks: { color: '#9ca3af' },
            grid: { color: 'rgba(255,255,255,0.06)' },
            min: 0
          },
          y: {
            min: 1120,
            max: 1450,
            title: { display: true, text: 'Code Arena ELO Ranking', color: '#9ca3af' },
            ticks: { color: '#9ca3af' },
            grid: { color: 'rgba(255,255,255,0.06)' }
          }
        }
      }
    });
  },

  /**
   * Reasoning Effort Trade-off Chart
   * Contrasts Baseline vs Ultra-High Effort across representative architectures,
   * showing frontier amplification vs distilled overthinking regression.
   */
  buildEffortTradeoffChart(ctx, models) {
    // Pick representative models across the spectrum
    const targetNames = [
      'Claude Opus 5.5', 'Claude Sonnet 5.5', 'GPT-6 Astra', 'Gemini 4 Argon',
      'Meta Muse Spark 1.3', 'Qwen 2.5 Coder 32B', 'DeepSeek 4.1 Flash', 'Claude Haiku 5.5'
    ];

    const sampleModels = models.filter(m => targetNames.some(t => m.name.includes(t))).slice(0, 8);
    if (sampleModels.length === 0) {
      // Fallback to top 8 models
      sampleModels.push(...models.slice(0, 8));
    }

    const labels = sampleModels.map(m => m.name);

    // Baseline ELO (stored base scores, effort-independent)
    const baseElo = sampleModels.map(m => m.scores ? m.scores.code_arena_elo : 1200);

    // Simulated Ultra-High ELO
    // data.js schema stores the ultra spec under key 'ultra' with field 'code_delta'
    const ultraSpec = (m) => {
      const sim = m.effort_simulation;
      if (!sim || !sim.multipliers) return 0;
      const spec = sim.multipliers.ultra || sim.multipliers.ultra_high;
      if (!spec) return 0;
      return (spec.coding_elo_delta !== undefined ? spec.coding_elo_delta : (spec.code_delta || 0));
    };

    const ultraElo = sampleModels.map(m => {
      const base = m.scores ? m.scores.code_arena_elo : 1200;
      return base + ultraSpec(m);
    });

    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Baseline Effort (Medium 1.0x)',
            data: baseElo,
            backgroundColor: '#64748b',
            borderRadius: 6
          },
          {
            label: 'Ultra-High Effort (Deep Reasoning Multiplier)',
            data: ultraElo,
            backgroundColor: sampleModels.map(m => ultraSpec(m) < 0 ? '#ef4444' : '#fbbf24'),
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#e2e8f0' } },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const m = sampleModels[context.dataIndex];
                const delta = ultraSpec(m);
                if (delta < 0) {
                  return `⚠️ Overthinking Regression: ${delta} ELO drop under Ultra-High effort (Loop penalty)`;
                }
                return `🚀 Frontier Amplification: +${delta} ELO gain with deep test-time compute`;
              }
            }
          }
        },
        scales: {
          x: { ticks: { color: '#9ca3af', font: { size: 10 }, maxRotation: 45, minRotation: 45 }, grid: { display: false } },
          y: { min: 1100, max: 1460, title: { display: true, text: 'Code Arena ELO', color: '#9ca3af' }, ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.06)' } }
        }
      }
    });
  },

  buildCostPerfChart(ctx, models) {
    const colors = this.getModelColors(models);
    const scatterData = models.map(m => {
      const scores = m.effective_scores || m.scores;
      return {
        x: m.pricing ? m.pricing.prompt_per_m : 0,
        y: scores ? scores.code_arena_elo : 0,
        r: Math.max(5, Math.round((scores ? scores.intelligence_index : 30) / 4)),
        model: m
      };
    });

    return new Chart(ctx, {
      type: 'bubble',
      data: {
        datasets: [{
          label: 'Models (Prompt $/M vs Code ELO, Bubble Size = Intelligence)',
          data: scatterData,
          backgroundColor: colors
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                const item = context.raw.model;
                const cost = item.pricing ? item.pricing.prompt_per_m : 0;
                const scores = item.effective_scores || item.scores;
                const elo = scores ? scores.code_arena_elo : 0;
                const intel = scores ? scores.intelligence_index : 0;
                const fc = (item.fact_check && item.fact_check.is_verified) ? ' [Dual-Verified]' : '';
                return `${item.name}${fc}: $${cost}/M | Code ELO: ${elo} | Intel: ${intel} (${item.quota_and_access || 'N/A'})`;
              }
            }
          }
        },
        scales: {
          x: { title: { display: true, text: 'Base Prompt Cost ($ / Million Tokens)', color: '#9ca3af' }, ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.06)' } },
          y: { min: 1120, max: 1450, title: { display: true, text: 'Code Arena ELO', color: '#9ca3af' }, ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.06)' } }
        }
      }
    });
  },

  buildCacheSavingsChart(ctx, models) {
    const labels = models.map(m => m.name);
    const standardCost = models.map(m => m.pricing ? m.pricing.prompt_per_m : 0);
    const cachedCost = models.map(m => m.pricing ? m.pricing.cache_read_per_m : 0);

    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Base Prompt ($/M)',
            data: standardCost,
            backgroundColor: 'rgba(239, 68, 68, 0.7)',
            borderRadius: 6
          },
          {
            label: '90% Prompt Cache Read ($/M)',
            data: cachedCost,
            backgroundColor: 'rgba(16, 185, 129, 0.85)',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#e2e8f0' } },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const m = models[context.dataIndex];
                if (!m.pricing || m.pricing.prompt_per_m === 0) return '100% Free Model';
                const savingsPct = Math.round((1 - (m.pricing.cache_read_per_m / m.pricing.prompt_per_m)) * 100);
                return `Prompt Caching Discount: ${savingsPct}% off`;
              }
            }
          }
        },
        scales: {
          x: { ticks: { color: '#9ca3af', font: { size: 10 }, maxRotation: 45, minRotation: 45 }, grid: { display: false } },
          y: { title: { display: true, text: 'Cost ($ / 1M Tokens)', color: '#9ca3af' }, ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.06)' } }
        }
      }
    });
  }
};
