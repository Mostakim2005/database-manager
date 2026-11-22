import { App, Notice, PluginSettingTab, Setting } from "obsidian";
import { ConfirmModal } from "./confirm-modal";
import { DEFAULT_SETTINGS } from "./settings";
import type HardwarePlannerPlugin from "./main";

export class HardwarePlannerSettingTab extends PluginSettingTab {
  constructor(app: App, private readonly plugin: HardwarePlannerPlugin) {
    super(app, plugin);
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.addClass("hp-root");
    containerEl.createEl("h2", { text: "PC Hardware Planner Settings" });

    new Setting(containerEl)
      .setName("PSU rated wattage (W)")
      .setDesc("Used by the transient spike guard and status bar indicator.")
      .addText((text) =>
        text
          .setPlaceholder("550")
          .setValue(String(this.plugin.settings.psuWattage))
          .onChange(async (val) => {
            const parsed = Math.max(100, Number(val) || DEFAULT_SETTINGS.psuWattage);
            this.plugin.settings.psuWattage = parsed;
            await this.plugin.saveSettings();
            this.plugin.refreshViewsAndStatus();
          })
      );

    new Setting(containerEl)
      .setName("Enable Pareto price/performance highlighting")
      .setDesc("Highlights optimal value GPUs along the efficiency frontier.")
      .addToggle((toggle) =>
        toggle.setValue(this.plugin.settings.enablePareto).onChange(async (val) => {
          this.plugin.settings.enablePareto = val;
          await this.plugin.saveSettings();
          this.plugin.refreshViewsAndStatus();
        })
      );

    new Setting(containerEl)
      .setName("Glassmorphism surface styling")
      .setDesc("Applies subtle translucent backdrop styling to planner panels.")
      .addToggle((toggle) =>
        toggle.setValue(this.plugin.settings.glassmorphism).onChange(async (val) => {
          this.plugin.settings.glassmorphism = val;
          await this.plugin.saveSettings();
          this.plugin.applyThemePreferences();
        })
      );

    new Setting(containerEl)
      .setName("Reset settings to defaults")
      .setDesc("Restores default PSU wattage and planner preferences.")
      .addButton((btn) =>
        btn
          .setButtonText("Reset defaults")
          .setWarning()
          .onClick(() => {
            new ConfirmModal(this.app, {
              title: "Reset PC Hardware Planner settings?",
              message: "This will restore PSU wattage to 550W and reset all planner toggles.",
              confirmLabel: "Reset",
              destructive: true,
              cssPrefix: "hp",
              onConfirm: async () => {
                this.plugin.settings = { ...DEFAULT_SETTINGS };
                await this.plugin.saveSettings();
                this.plugin.applyThemePreferences();
                this.plugin.refreshViewsAndStatus();
                this.display();
                new Notice("PC Hardware Planner settings reset to defaults.");
              },
            }).open();
          })
      );
  }
}
