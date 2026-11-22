# PC Hardware Planner

Obsidian workspace planner for GPU upgrade comparison, PSU transient spike safety analysis, and build budgeting.

## UI/UX Surface Inventory

| Surface | Implementation |
| :--- | :--- |
| **Ribbon Icon** | CPU icon (`Open PC Hardware Planner`) launching the dedicated `HardwarePlannerView`. |
| **Workspace View** | `HardwarePlannerView` (`ItemView`) with interactive PSU transient calculator and GPU presets. |
| **Status Bar** | Clickable `PSU: <W>` indicator opening the planner view. |
| **Settings Tab** | `HardwarePlannerSettingTab` with PSU wattage, Pareto toggle, glassmorphism, and guarded Reset. |
| **Commands** | `Open PC Hardware Planner`. |

## Documentation

- `docs/PRODUCT.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS_AND_TRAPS.md`
- `docs/VISUAL_LOG.md`
- `AGENTS.md`

## Develop

```bash
npm install
npm run build
```

## License

See `LICENSE`.
