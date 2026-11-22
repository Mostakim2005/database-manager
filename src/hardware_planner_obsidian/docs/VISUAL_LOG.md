# Visual Feature & Change Log (`VISUAL_LOG.md`)
> **1-Line Summary:** Visual flowcharts explaining key user interaction flows in PC Hardware Planner.

## Feature & Change Flowcharts

### [VISUAL: Upgrade-Analysis-Flow] | Aliases: compare gpu workflow, benchmark calculation
> **1-Line Summary:** Complete flow from user hardware input to Pareto value chart rendering.

* **Plain-English Walkthrough:** The user opens the comparison modal, inputs budget or target game title. The engine looks up benchmark data, checks PSU margin, calculates Pareto efficiency, and draws the color-coded Chart.js scatter plot.

```mermaid
flowchart TD
    %% Color Definitions (Obsidian & GitHub compatible)
    classDef startNode fill:#1d4ed8,stroke:#1e3a8a,color:#ffffff
    classDef processNode fill:#0f766e,stroke:#115e59,color:#ffffff
    classDef outputNode fill:#15803d,stroke:#14532d,color:#ffffff
    classDef trapNode fill:#b91c1c,stroke:#7f1d1d,color:#ffffff

    Start([Start: User opens Hardware Planner]):::startNode --> Input[User selects budget or target game]:::processNode
    Input --> PSUCheck{PSU Headroom Check}:::processNode
    PSUCheck -->|Exceeds 550W limit| Warn[Display Red Transient Warning]:::trapNode
    PSUCheck -->|Safe| Calc[Compute FPS per BDT / USD]:::processNode
    Calc --> Pareto[Generate Pareto Curve]:::processNode
    Pareto --> Output([Render Chart.js Dashboard]):::outputNode

    subgraph Legend["Legend (Color Guide)"]
        L1([Blue = Starting User Action]):::startNode
        L2[Teal = Processing & Calculation]:::processNode
        L3([Green = Rendered Visual Output]):::outputNode
        L4[Red = Power Limit Warning]:::trapNode
    end
```
