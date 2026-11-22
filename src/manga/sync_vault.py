"""Obsidian vault synchronization module for Manga domain.

Reads data/manga/manga_catalog.json, formats a 3-column Markdown table, and
updates the Obsidian vault note while preserving the personal ### Outlander section.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from manga import CATALOG_JSON_PATH, DEFAULT_VAULT_FILE


def load_catalog(catalog_path: Path = CATALOG_JSON_PATH) -> list[dict[str, Any]]:
    """Load manga catalog records from JSON."""
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog JSON not found at {catalog_path}")
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def generate_markdown_table(catalog_items: list[dict[str, Any]]) -> str:
    """Render Obsidian-ready YAML frontmatter + 3-column comic/adaptation table."""
    lines = [
        "---",
        "aliases:",
        "  - TV Series Link",
        "  - Anime Links",
        "  - Donghua",
        "  - Motion Manhua",
        "  - Chinese Animation",
        "  - Movie Links",
        "---",
        "",
        "# Comic & Adaptation Master Catalog",
        "",
        "A unified master index covering every manga, manhwa, manhua, and web novel from your collection.",
        "- **Title / Read Link:** Hyperlinked directly to the canonical title page on **comix.to** (or relevance search where direct index is unavailable).",
        "- **Anime / Donghua Adaptation:** Official anime, donghua, and dynamic motion comics with streaming links, official teaser links, in-production news, or community fan-made motion comics for unadapted works.",
        "- **Live-Action Adaptation:** Official C-Dramas, K-Dramas, and Japanese films/series with streaming sources, or upcoming production news.",
        "",
        "---",
        "",
        "| Name & Comic Link | Anime / Donghua Adaptation & Fan Animation | Live-Action Adaptation |",
        "| :--- | :--- | :--- |",
    ]
    for item in catalog_items:
        name_cell = f"[**{item['name']}**]({item['link']})<br>*{item.get('alt', '')}*<br>🏷️ *{item['origin']}*"
        lines.append(f"| {name_cell} | {item['anime']} | {item['live_action']} |")
    lines.extend(["", "---", "", ""])
    return "\n".join(lines)


def sync_to_obsidian(
    vault_path: Path | str = DEFAULT_VAULT_FILE,
    catalog_path: Path = CATALOG_JSON_PATH,
    create_backup: bool = True,
) -> int:
    """Write updated 3-column Markdown table to Obsidian while preserving ### Outlander."""
    target = Path(vault_path)
    catalog = load_catalog(catalog_path)
    table_md = generate_markdown_table(catalog)

    outlander_content = ""
    if target.exists():
        if create_backup:
            shutil.copy2(target, target.with_suffix(target.suffix + ".bak"))
        content = target.read_text(encoding="utf-8")
        idx = content.find("### Outlander")
        if idx != -1:
            outlander_content = content[idx:]

    if not outlander_content:
        outlander_content = "### Outlander\n\n(No previous outlander links found)\n"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(table_md + outlander_content, encoding="utf-8")
    print(f"[manga.sync_vault] Successfully synced {len(catalog)} titles to {target}")
    return len(catalog)
