import { Plugin, WorkspaceLeaf } from "obsidian";
import { DEFAULT_SETTINGS, type HardwareSettings } from "./settings";
import { HardwarePlannerSettingTab } from "./settings-tab";
import { HardwarePlannerView, VIEW_TYPE_HARDWARE_PLANNER } from "./view";

export default class HardwarePlannerPlugin extends Plugin {
  settings: HardwareSettings = { ...DEFAULT_SETTINGS };
  private statusBarEl: HTMLElement | null = null;

  async onload(): Promise<void> {
    await this.loadSettings();
    this.applyThemePreferences();

    this.registerView(VIEW_TYPE_HARDWARE_PLANNER, (leaf: WorkspaceLeaf) => new HardwarePlannerView(leaf, this));
    this.addSettingTab(new HardwarePlannerSettingTab(this.app, this));

    const ribbonEl = this.addRibbonIcon("cpu", "Open PC Hardware Planner", () => {
      void this.activateView();
    });
    ribbonEl.setAttribute("aria-label", "Open PC Hardware Planner");

    this.addCommand({
      id: "open-hardware-planner",
      name: "Open PC Hardware Planner",
      callback: () => {
        void this.activateView();
      },
    });

    this.statusBarEl = this.addStatusBarItem();
    this.statusBarEl.addClass("hp-status-pill");
    this.statusBarEl.setAttribute("role", "button");
    this.statusBarEl.setAttribute("tabindex", "0");
    this.statusBarEl.setAttribute("aria-label", "Open PC Hardware Planner");
    this.statusBarEl.addEventListener("click", () => void this.activateView());
    this.statusBarEl.addEventListener("keydown", (evt: KeyboardEvent) => {
      if (evt.key === "Enter" || evt.key === " ") {
        evt.preventDefault();
        void this.activateView();
      }
    });
    this.refreshViewsAndStatus();
  }

  onunload(): void {
    document.body.removeClass("hp-glassmorphic");
  }

  applyThemePreferences(): void {
    document.body.toggleClass("hp-glassmorphic", Boolean(this.settings.glassmorphism));
  }

  refreshViewsAndStatus(): void {
    if (this.statusBarEl) {
      this.statusBarEl.setText(`PSU: ${this.settings.psuWattage}W`);
    }
    for (const leaf of this.app.workspace.getLeavesOfType(VIEW_TYPE_HARDWARE_PLANNER)) {
      if (leaf.view instanceof HardwarePlannerView) {
        leaf.view.render();
      }
    }
  }

  async activateView(): Promise<void> {
    const existing = this.app.workspace.getLeavesOfType(VIEW_TYPE_HARDWARE_PLANNER);
    const leaf = existing.length > 0 ? existing[0] : this.app.workspace.getLeaf(true);
    if (!leaf) return;
    await leaf.setViewState({ type: VIEW_TYPE_HARDWARE_PLANNER, active: true });
    this.app.workspace.revealLeaf(leaf);
  }

  async loadSettings(): Promise<void> {
    const loaded = (await this.loadData()) as Partial<HardwareSettings> | undefined;
    this.settings = Object.assign({}, DEFAULT_SETTINGS, loaded ?? {});
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }
}
