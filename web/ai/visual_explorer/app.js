/**
 * ==========================================================================
 * AI Architecture & Ecosystem Explorer - Modular Application Logic
 * ==========================================================================
 */

const State = {
  activeTab: 'hierarchy',
  viewMode: 'simple', // 'simple' or 'complex'
  selectedConceptId: 'ai',
  selectedLayer: 4,
  selectedPipelineIdx: 0,
  selectedStepIdx: 0
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  renderActiveView();
});

function setViewMode(mode) {
  State.viewMode = mode;
  document.getElementById('btnSimpleMode').className = `mode-toggle-btn ${mode === 'simple' ? 'active' : ''}`;
  document.getElementById('btnComplexMode').className = `mode-toggle-btn ${mode === 'complex' ? 'active' : ''}`;
  
  const modeSubtitle = document.getElementById('modeSubtitle');
  if (modeSubtitle) {
    modeSubtitle.textContent = mode === 'simple' 
      ? '⚡ Simple View: Core journey from AI to Claude Code, Antigravity, MCP & Agents.' 
      : '🔬 Complex Mode: Full master architecture including horizontal domains, tensor math & enterprise pipelines.';
  }

  renderActiveView();
}

function setActiveTab(tabId) {
  State.activeTab = tabId;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.className = 'tab-btn px-3.5 py-1.5 rounded-lg font-medium text-xs md:text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition';
  });
  const activeBtn = document.getElementById('tab-' + tabId);
  if (activeBtn) {
    activeBtn.className = 'tab-btn px-3.5 py-1.5 rounded-lg font-medium text-xs md:text-sm bg-blue-600 text-white transition shadow-sm';
  }

  // Update standalone link in top right
  const directLink = document.getElementById('directFileLink');
  if (directLink) {
    directLink.href = `${tabId}.html`;
    directLink.textContent = `Open ${tabId}.html Directly ↗`;
  }

  renderActiveView();
}

function renderActiveView() {
  const container = document.getElementById('contentViewport');
  if (!container) return;

  switch (State.activeTab) {
    case 'hierarchy':
      renderHierarchy(container);
      break;
    case 'agent-stack':
      renderAgentStack(container);
      break;
    case 'pipeline':
      renderPipelines(container);
      break;
    case 'ecosystem':
      renderEcosystem(container);
      break;
    case 'builder-studio':
      renderBuilderStudio(container);
      break;
    default:
      renderHierarchy(container);
  }
}

// --------------------------------------------------------------------------
// 1. Hierarchy Renderer (Adapts to Simple vs Complex)
// --------------------------------------------------------------------------
function renderHierarchy(container) {
  const data = window.AI_DATA;
  const isComplex = State.viewMode === 'complex';

  let listHtml = data.coreJourney.map(item => `
    <div onclick="selectConcept('${item.id}')" id="card-${item.id}" class="interactive-card p-3.5 ${item.id === State.selectedConceptId ? 'active' : ''}">
      <div class="flex items-center justify-between">
        <span class="text-[11px] font-mono uppercase text-blue-400 font-semibold">${item.badge}</span>
        <span class="text-[10px] text-slate-500 font-mono">Core Spine</span>
      </div>
      <div class="text-sm font-bold text-white mt-1">${item.title}</div>
      <div class="text-xs text-slate-400 mt-1">${item.layman.substring(0, 75)}...</div>
    </div>
  `).join('');

  let horizontalHtml = '';
  if (isComplex) {
    horizontalHtml = `
      <div class="mt-6 pt-6 border-t border-slate-800">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-mono uppercase tracking-wider text-purple-400 font-bold">Horizontal Sister Domains (Unlocked in Complex Mode)</span>
          <span class="text-[10px] text-slate-500">Perception, Media, Control</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          ${data.horizontalDomains.map(item => `
            <div onclick="selectConcept('${item.id}')" id="card-${item.id}" class="interactive-card p-3 ${item.id === State.selectedConceptId ? 'active' : ''}">
              <div class="text-[10px] font-mono text-purple-400 uppercase">${item.category}</div>
              <div class="text-xs font-bold text-slate-200 mt-0.5">${item.title}</div>
              <div class="text-[11px] text-slate-400 mt-1">${item.layman.substring(0, 60)}...</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  container.innerHTML = `
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 p-6">
      <!-- Left Column: Concept Cards -->
      <div class="lg:col-span-7 space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs font-mono uppercase text-slate-400 font-semibold">
            ${isComplex ? 'Full Architecture (Core + Horizontals)' : 'The Core Journey (Click to inspect)'}
          </span>
          <a href="../../docs/guides/ai_ecosystem_map.md#1-from-raw-ai-to-the-llm-brain" target="_blank" class="text-xs text-indigo-400 hover:underline">
            Markdown Section 1 ↗
          </a>
        </div>
        <div class="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
          ${listHtml}
          ${horizontalHtml}
        </div>
      </div>

      <!-- Right Column: Detail Drawer -->
      <div class="lg:col-span-5">
        <div id="conceptDrawer" class="sticky top-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3.5">
          <!-- Populated by selectConcept() -->
        </div>
      </div>
    </div>
  `;

  selectConcept(State.selectedConceptId);
}

function selectConcept(id) {
  State.selectedConceptId = id;
  document.querySelectorAll('.interactive-card').forEach(c => c.classList.remove('active'));
  const card = document.getElementById('card-' + id);
  if (card) card.classList.add('active');

  const allConcepts = [...window.AI_DATA.coreJourney, ...window.AI_DATA.horizontalDomains];
  const item = allConcepts.find(c => c.id === id) || allConcepts[0];
  const isComplex = State.viewMode === 'complex';

  const drawer = document.getElementById('conceptDrawer');
  if (!drawer) return;

  drawer.innerHTML = `
    <div class="border-b border-slate-800 pb-3">
      <span class="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">
        ${item.badge || item.category}
      </span>
      <h3 class="text-base font-bold text-white mt-1.5">${item.title}</h3>
    </div>

    <!-- Tier 1: Layman -->
    <div class="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
      <span class="font-semibold text-emerald-400 flex items-center gap-1 mb-1">💡 Simple Layman Explanation</span>
      <p class="text-slate-200 leading-relaxed">${item.layman}</p>
    </div>

    <!-- Tier 2: Grade 11 Student -->
    <div class="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
      <span class="font-semibold text-amber-400 flex items-center gap-1 mb-1">🎓 Grade 11 High School Analogy</span>
      <p class="text-slate-300 leading-relaxed">${item.analogy}</p>
    </div>

    <!-- Tier 3: Technical (Always visible in complex, collapsible in simple) -->
    <div class="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
      <div class="flex items-center justify-between mb-1">
        <span class="font-semibold text-indigo-400 flex items-center gap-1">⚙️ Deep-Dive Technical Spec</span>
        ${!isComplex ? '<span class="text-[10px] text-indigo-400 font-mono">(Unlocked)</span>' : ''}
      </div>
      <p class="text-slate-300 font-mono text-[11px] leading-relaxed">${item.tech}</p>
    </div>

    <div class="text-[11px] text-slate-500 text-right">
      Matches Markdown: <a href="../../docs/guides/ai_ecosystem_map.md" target="_blank" class="text-blue-400 hover:underline">ai_ecosystem_map.md</a>
    </div>
  `;
}

// --------------------------------------------------------------------------
// 2. Agent Stack Renderer
// --------------------------------------------------------------------------
function renderAgentStack(container) {
  const stack = window.AI_DATA.agentStack;
  container.innerHTML = `
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 p-6">
      <div class="lg:col-span-6 space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs font-mono uppercase text-slate-400 font-semibold">The 5-Layer Stack (Top to Bottom)</span>
          <a href="../../docs/guides/ai_ecosystem_map.md#7-instruction-sets-skills-agents--sub-agents" target="_blank" class="text-xs text-indigo-400 hover:underline">Markdown #7 ↗</a>
        </div>
        ${stack.map(layer => `
          <div onclick="selectLayer(${layer.level})" id="layer-${layer.level}" class="interactive-card p-4 border-l-4 ${layer.level === State.selectedLayer ? 'active border-l-indigo-500' : 'border-l-slate-700'}">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-mono text-indigo-400 font-semibold">Layer ${layer.level}: ${layer.badge}</span>
            </div>
            <div class="text-sm font-bold text-white mt-1">${layer.name}</div>
            <div class="text-xs text-slate-400 mt-1">${layer.analogy.substring(0, 80)}...</div>
          </div>
        `).join('')}
      </div>
      <div class="lg:col-span-6">
        <div id="layerDrawer" class="sticky top-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <!-- Populated by selectLayer() -->
        </div>
      </div>
    </div>
  `;
  selectLayer(State.selectedLayer);
}

function selectLayer(lvl) {
  State.selectedLayer = lvl;
  document.querySelectorAll('.interactive-card').forEach(c => c.classList.remove('active'));
  const card = document.getElementById('layer-' + lvl);
  if (card) card.classList.add('active');

  const layer = window.AI_DATA.agentStack.find(l => l.level === lvl) || window.AI_DATA.agentStack[0];
  const drawer = document.getElementById('layerDrawer');
  if (!drawer) return;

  drawer.innerHTML = `
    <div class="border-b border-slate-800 pb-3">
      <span class="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400">Layer ${layer.level} Active</span>
      <h3 class="text-base font-bold text-white mt-1">${layer.name}</h3>
    </div>
    <div class="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
      <span class="font-semibold text-amber-400 block mb-1">🎓 High School Analogy:</span>
      <p class="text-slate-200 leading-relaxed">${layer.analogy}</p>
    </div>
    <div class="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs">
      <span class="font-semibold text-indigo-400 block mb-1">⚙️ Technical Execution:</span>
      <p class="text-slate-300 leading-relaxed">${layer.tech}</p>
    </div>
    <div>
      <span class="text-[11px] font-mono text-slate-400 block mb-1">Live Code / Schema Representation:</span>
      <pre class="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono text-cyan-300 overflow-x-auto">${layer.code}</pre>
    </div>
  `;
}

// --------------------------------------------------------------------------
// 3. Pipelines Renderer
// --------------------------------------------------------------------------
function renderPipelines(container) {
  const pipelines = window.AI_DATA.pipelines;
  const currentPipeline = pipelines[State.selectedPipelineIdx];

  container.innerHTML = `
    <div class="p-6 space-y-6">
      <div class="flex items-center gap-2 overflow-x-auto border-b border-slate-800 pb-3 text-xs">
        ${pipelines.map((p, idx) => `
          <button onclick="switchPipeline(${idx})" class="px-3 py-1.5 rounded-lg font-medium transition ${idx === State.selectedPipelineIdx ? 'bg-blue-600 text-white' : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'}">
            ${p.name}
          </button>
        `).join('')}
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div class="lg:col-span-6 space-y-3">
          <div class="text-xs font-mono uppercase text-slate-400 font-semibold mb-2">Sequential Pipeline Steps</div>
          ${currentPipeline.steps.map((s, sIdx) => `
            <div onclick="selectPipelineStep(${sIdx})" id="step-card-${sIdx}" class="interactive-card p-3.5 flex items-center justify-between ${sIdx === State.selectedStepIdx ? 'active' : ''}">
              <div class="flex items-center gap-3">
                <span class="w-6 h-6 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs">${sIdx + 1}</span>
                <div>
                  <div class="text-xs font-bold text-white">${s.name}</div>
                  <div class="text-[11px] text-slate-400">${s.desc.substring(0, 60)}...</div>
                </div>
              </div>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">${s.tech.split(',')[0]}</span>
            </div>
          `).join('')}
        </div>

        <div class="lg:col-span-6">
          <div id="stepDrawer" class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3 text-xs">
            <!-- Populated by selectPipelineStep() -->
          </div>
        </div>
      </div>
    </div>
  `;
  selectPipelineStep(State.selectedStepIdx);
}

function switchPipeline(idx) {
  State.selectedPipelineIdx = idx;
  State.selectedStepIdx = 0;
  renderPipelines(document.getElementById('contentViewport'));
}

function selectPipelineStep(sIdx) {
  State.selectedStepIdx = sIdx;
  document.querySelectorAll('.interactive-card').forEach(c => c.classList.remove('active'));
  const card = document.getElementById('step-card-' + sIdx);
  if (card) card.classList.add('active');

  const p = window.AI_DATA.pipelines[State.selectedPipelineIdx];
  const step = p.steps[sIdx];
  const drawer = document.getElementById('stepDrawer');
  if (!drawer) return;

  drawer.innerHTML = `
    <div class="border-b border-slate-800 pb-3">
      <span class="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">Step ${sIdx + 1} of ${p.steps.length}</span>
      <h3 class="text-base font-bold text-white mt-1">${step.name}</h3>
    </div>
    <div class="p-3 rounded-lg bg-slate-950 border border-slate-800">
      <span class="text-slate-400 font-semibold block mb-1">What Happens in this Stage:</span>
      <p class="text-slate-200 leading-relaxed">${step.desc}</p>
    </div>
    <div class="p-3 rounded-lg bg-slate-950 border border-slate-800">
      <span class="text-amber-400 font-semibold block mb-1">🛠️ Underlying Tools & Algorithms:</span>
      <span class="font-mono text-cyan-300 text-[11px]">${step.tech}</span>
    </div>
    <div class="text-[11px] text-slate-500 text-right">
      Reference: <a href="../../docs/guides/ai_ecosystem_map.md#11-the-5-core-end-to-end-engineering-pipelines" target="_blank" class="text-blue-400 hover:underline">Markdown Pipelines (#11) ↗</a>
    </div>
  `;
}

// --------------------------------------------------------------------------
// 4. Ecosystem & Tool Comparison Renderer
// --------------------------------------------------------------------------
function renderEcosystem(container) {
  container.innerHTML = `
    <div class="p-6 space-y-6">
      <div>
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-bold text-white uppercase font-mono">Agentic Coding Platforms</h3>
          <a href="../../docs/guides/ai_ecosystem_map.md#8-frontier-coding-agents-antigravity--claude-code" target="_blank" class="text-xs text-indigo-400 hover:underline">Markdown #8 ↗</a>
        </div>
        <div class="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 text-xs">
          <table class="w-full text-left">
            <thead class="bg-slate-900 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
              <tr>
                <th class="p-3">Platform</th>
                <th class="p-3">Developer</th>
                <th class="p-3">Form Factor</th>
                <th class="p-3">MCP Support</th>
                <th class="p-3">Primary Superpower</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800 text-slate-300">
              <tr>
                <td class="p-3 font-bold text-white">Antigravity</td>
                <td class="p-3 text-slate-400">Google DeepMind</td>
                <td class="p-3">Full Agentic IDE</td>
                <td class="p-3 text-emerald-400 font-semibold">Native First-Class</td>
                <td class="p-3">Multi-agent swarms, interactive sidecars, full local system execution.</td>
              </tr>
              <tr>
                <td class="p-3 font-bold text-white">Claude Code</td>
                <td class="p-3 text-slate-400">Anthropic</td>
                <td class="p-3">Terminal CLI (claude)</td>
                <td class="p-3 text-emerald-400 font-semibold">Protocol Creator</td>
                <td class="p-3">Blazing fast terminal commands, git diffs, minimal overhead.</td>
              </tr>
              <tr>
                <td class="p-3 font-bold text-white">OpenHands</td>
                <td class="p-3 text-slate-400">Open Source</td>
                <td class="p-3">Web Sandbox / Docker</td>
                <td class="p-3 text-slate-400">Supported</td>
                <td class="p-3">Completely open-source, vendor-neutral Docker micro-VMs.</td>
              </tr>
              <tr>
                <td class="p-3 font-bold text-white">Aider</td>
                <td class="p-3 text-slate-400">Paul Gauthier</td>
                <td class="p-3">CLI Terminal</td>
                <td class="p-3 text-slate-400">CLI Native</td>
                <td class="p-3">Automated Git commits with concise descriptive messages.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

// --------------------------------------------------------------------------
// 5. Builder Studio Renderer
// --------------------------------------------------------------------------
function renderBuilderStudio(container) {
  container.innerHTML = `
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 p-6">
      <div class="lg:col-span-6 space-y-4">
        <!-- MCP Schema Generator -->
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div class="text-xs font-bold text-cyan-400 uppercase font-mono mb-2">1. Live MCP Tool Generator</div>
          <div class="grid grid-cols-2 gap-2 mb-2 text-xs">
            <input id="inputToolName" type="text" value="query_postgres" class="p-2 rounded bg-slate-950 border border-slate-800 text-white font-mono" placeholder="Tool name">
            <input id="inputToolArg" type="text" value="sql_query" class="p-2 rounded bg-slate-950 border border-slate-800 text-white font-mono" placeholder="Argument name">
          </div>
          <button onclick="generateMCPTool()" class="w-full py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium">Generate JSON-RPC Schema</button>
          <pre id="outputMCP" class="mt-3 p-3 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-cyan-300 overflow-x-auto max-h-36">{\n  "name": "query_postgres",\n  "parameters": {\n    "type": "object",\n    "properties": { "sql_query": { "type": "string" } },\n    "required": ["sql_query"]\n  }\n}</pre>
        </div>

        <!-- Skill Generator -->
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div class="text-xs font-bold text-indigo-400 uppercase font-mono mb-2">2. Live SKILL.md Generator</div>
          <input id="inputSkillName" type="text" value="react-performance-audit" class="w-full p-2 rounded bg-slate-950 border border-slate-800 text-white font-mono text-xs mb-2" placeholder="Skill name">
          <button onclick="generateSkillDoc()" class="w-full py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium">Generate SKILL.md Template</button>
          <pre id="outputSkill" class="mt-3 p-3 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-indigo-300 overflow-x-auto max-h-36">---\nname: react-performance-audit\ndescription: Heuristics to audit React re-renders\n---\n\n# Workflow\n1. Check React Profiler flamegraphs.\n2. Verify memoization on high-frequency components.</pre>
        </div>
      </div>

      <!-- Live JSON Graph Data Editor -->
      <div class="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col gap-3">
        <div class="flex items-center justify-between border-b border-slate-800 pb-2">
          <span class="text-xs font-mono uppercase text-emerald-400 font-bold">Dynamic Graph Schema (Editable JSON)</span>
          <button onclick="copyDataJSON()" class="px-2 py-1 rounded bg-slate-800 text-slate-300 text-xs hover:bg-slate-700">Copy JSON</button>
        </div>
        <p class="text-xs text-slate-400">
          This modular JSON drives the architecture. Any future AI or developer can edit or extend these nodes!
        </p>
        <textarea id="liveJsonArea" class="w-full h-80 p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-emerald-300 resize-none focus:outline-none"></textarea>
      </div>
    </div>
  `;

  document.getElementById('liveJsonArea').value = JSON.stringify(window.AI_DATA.coreJourney.map(c => ({ id: c.id, title: c.title, badge: c.badge })), null, 2);
}

function generateMCPTool() {
  const name = document.getElementById('inputToolName').value || 'tool';
  const arg = document.getElementById('inputToolArg').value || 'param';
  const schema = {
    name: name,
    description: `Automated tool schema for ${name}`,
    parameters: {
      type: "object",
      properties: { [arg]: { type: "string" } },
      required: [arg]
    }
  };
  document.getElementById('outputMCP').textContent = JSON.stringify(schema, null, 2);
}

function generateSkillDoc() {
  const name = document.getElementById('inputSkillName').value || 'my-skill';
  const doc = `---\nname: ${name}\ndescription: Standard operating procedures for ${name}\n---\n\n# Trigger\nActivate when the user asks for ${name}.\n\n# Heuristics\n1. Inspect environment state.\n2. Apply patch.\n3. Verify with tests.`;
  document.getElementById('outputSkill').textContent = doc;
}

function copyDataJSON() {
  const text = document.getElementById('liveJsonArea').value;
  navigator.clipboard.writeText(text);
  alert('Copied JSON to clipboard!');
}
