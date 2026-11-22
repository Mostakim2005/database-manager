"""Manga, Manhwa, Manhua & Adaptation Management package for Database Manager."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MANGA_DATA_DIR = ROOT_DIR / "data" / "manga"
CATALOG_JSON_PATH = MANGA_DATA_DIR / "manga_catalog.json"
SITEMAPS_DIR = MANGA_DATA_DIR / "sitemaps"
DEFAULT_VAULT_FILE = Path("C:/Users/kazir/Documents/Obsidian Vaults/Nihon/Manhua Links.md")
