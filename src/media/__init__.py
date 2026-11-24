"""Media, Comics, Novels, Anime, Movies & TV Series package for Database Manager."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DATA_DIR = ROOT_DIR / "data" / "media"
CATALOG_JSON_PATH = MEDIA_DATA_DIR / "media_catalog.json"
SITEMAPS_DIR = MEDIA_DATA_DIR / "sitemaps"


def load_catalog(catalog_path: Path = CATALOG_JSON_PATH) -> list[dict[str, Any]]:
    """Load media catalog records from JSON."""
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog JSON not found at {catalog_path}")
    return json.loads(catalog_path.read_text(encoding="utf-8"))
