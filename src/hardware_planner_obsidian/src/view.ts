import { ItemView, WorkspaceLeaf } from "obsidian";
import { analyzePsuLoad } from "./psu";
import type HardwarePlannerPlugin from "./main";

export const VIEW_TYPE_HARDWARE_PLANNER = "hardware-planner-view";

interface GpuPreset {
  name: string;
  tdpWatts: number;
  tier: string;
}

const GPU_PRESETS: GpuPreset[] = [
  { name: "RX 6600 (8 GB)", tdpWatts: 132, tier: "1080p Value" },
  { name: "RTX 4060 (8 GB)", tdpWatts: 115, tier: "1080p Efficient" },
  { name: "RX 6700 XT (12 GB)", tdpWatts: 230, tier: "1440p Mid" },
  { name: "RTX 4070 Super (12 GB)", tdpWatts: 220, tier: "1440p High" },
  { name: "RX 7800 XT (16 GB)", tdpWatts: 263, tier: "1440p Ultra" },
];

export class HardwarePlannerView extends ItemView {
  private selectedTdp = 132;
  private systemBaseWatts = 85;

  constructor(leaf: WorkspaceLeaf, private readonly plugin: HardwarePlannerPlugin) {
    super(leaf);
  }

  getViewType(): string {
    return VIEW_TYPE_HARDWARE_PLANNER;
  }

  getDisplayText(): string {
    return "PC Hardware Planner";
  }

  getIcon(): string {
    return "cpu";
  }

  async onOpen(): Promise<void> {
    this.render();
  }

  async onClose(): Promise<void> {
    this.contentEl.empty();
  }

  render(): void {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass("hp-root", "hp-view");

    const header = contentEl.createDiv({ cls: "hp-header" });
    header.createEl("h2", { text: "PC Hardware Planner" });
    header.createEl("p", {
      text: `PSU Transient Spike Guard & Upgrade Matrix (Configured PSU: ${this.plugin.settings.psuWattage}W)`,
      cls: "hp-subtitle",
    });

    const controls = contentEl.createDiv({ cls: "hp-controls" });
    const tdpLabel = controls.createEl("label", { text: "GPU TDP (Watts): ", cls: "hp-label" });
    const tdpInput = tdpLabel.createEl("input", {
      type: "number",
      value: String(this.selectedTdp),
      attr: { min: "30", max: "600", step: "5", "aria-label": "GPU TDP in Watts" },
    });
    tdpInput.addEventListener("input", () => {
      this.selectedTdp = Math.max(0, Number(tdpInput.value) || 0);
      this.renderAnalysis(resultBox);
    });

    const baseLabel = controls.createEl("label", { text: "System Base (Watts): ", cls: "hp-label" });
    const baseInput = baseLabel.createEl("input", {
      type: "number",
      value: String(this.systemBaseWatts),
      attr: { min: "30", max: "300", step: "5", "aria-label": "System base power in Watts" },
    });
    baseInput.addEventListener("input", () => {
      this.systemBaseWatts = Math.max(0, Number(baseInput.value) || 0);
      this.renderAnalysis(resultBox);
    });

    const resultBox = contentEl.createDiv({ cls: "hp-psu-card" });
    this.renderAnalysis(resultBox);

    contentEl.createEl("h3", { text: "Quick GPU Presets" });
    const grid = contentEl.createDiv({ cls: "hp-preset-grid" });
    for (const preset of GPU_PRESETS) {
      const analysis = analyzePsuLoad(preset.tdpWatts, this.plugin.settings.psuWattage, this.systemBaseWatts);
      const card = grid.createEl("button", {
        cls: `hp-preset-card hp-status-${analysis.status}`,
        attr: { type: "button", "aria-label": `Analyze ${preset.name}` },
      });
      card.createEl("strong", { text: preset.name });
      card.createDiv({ text: `${preset.tier} · ${preset.tdpWatts}W TDP`, cls: "hp-preset-meta" });
      card.createDiv({ text: `${analysis.badgeText} (Peak ~${analysis.peakWatts}W)`, cls: "hp-preset-badge" });
      card.addEventListener("click", () => {
        this.selectedTdp = preset.tdpWatts;
        tdpInput.value = String(preset.tdpWatts);
        this.renderAnalysis(resultBox);
      });
    }
  }

  private renderAnalysis(container: HTMLElement): void {
    container.empty();
    const res = analyzePsuLoad(this.selectedTdp, this.plugin.settings.psuWattage, this.systemBaseWatts);
    container.setAttr("data-status", res.status);
    container.createEl("h3", { text: `${res.badgeText} — Continuous ${res.continuousWatts}W / Peak ~${res.peakWatts}W` });
    container.createEl("p", { text: res.explanation });
  }
}
