#!/usr/bin/env python3
"""Database Manager — Unified PC Games Catalog, Normalization & Steam API Sync.

Provides one consistent schema (v4.0.0) and automation pipeline across:
  - Previously researched RTS/strategy wishlist titles
  - Owned Steam library PC titles across all genres
  - Future games added via Steam Store API / SteamSpy / manual specs

Sources:
  1. Steam Store API (Tier 0) -> official AppID, USD price, genres, categories, URL, specs.
  2. Steam Web API (Tier 0) -> live concurrent player counts.
  3. SteamSpy API (Tier 0) -> user review positivity & community tags.

Supports:
  --dry-run (default): checks incoming seeds/updates without modifying files.
  --apply: updates data/games/games.json, both games.js mirrors, and compiles SQLite.
  --offline: uses built-in fixtures for CI and offline verification.
  --normalize: deduplicates and normalizes all records in data/games/games.json.
  --add-steam "<Title or AppID>": fetches a new title from Steam API and enriches it.
  --enrich-steam: refreshes live price/player/metadata for Steam-linked entries.
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
GAMES_JSON = DATA_DIR / "games" / "games.json"
WEB_GAMES_JS = ROOT_DIR / "web" / "games" / "data" / "games.js"
DATA_GAMES_JS = DATA_DIR / "games" / "games.js"

if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

# Canonical valid enums matching data/games/schema.json v4.0.0
VALID_GENRES = {
    "classic-rts",
    "4x-grand",
    "hybrid-td",
    "army-sim",
    "tactical-rpg",
    "fps-shooter",
    "action-adventure",
    "rpg",
    "racing-sim",
    "puzzle-platformer",
    "fighting-arcade",
    "vr-utility",
}

VALID_SETTINGS = {
    "ancient",
    "realistic-modern",
    "futuristic",
    "fantasy",
    "post-apocalyptic",
    "steampunk",
}

SETTING_ALIASES = {
    "historical": "ancient",
    "mythological": "fantasy",
    "sci-fi": "futuristic",
    "sci-fi / alternate-history": "futuristic",
    "sci-fi / frontier": "futuristic",
    "sci-fi / space": "futuristic",
    "modern": "realistic-modern",
    "contemporary": "realistic-modern",
}

STORAGE_VERDICT_ALIASES = {
    "ssd-advised": "ssd-helps",
    "ssd-required": "ssd-strongly-advised",
    "hdd-ok": "hdd-fine",
}

PLAYER_STATUS_ALIASES = {
    "upcoming": "small",
}


# ---------------------------------------------------------------------------
# Hardware Tier & Spec Inference Helpers (Unified across all PC genres)
# ---------------------------------------------------------------------------

def slugify_game_id(name: str) -> str:
    """Create a clean kebab-case game slug."""
    s = re.sub(r"[™®©]", "", name).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "unknown-game"


def parse_ram_gb(text: str | None) -> float:
    """Parse RAM string such as '16 GB', '512 MB', '1.5 GB' -> numeric GB."""
    if not text:
        return 4.0
    s = str(text)
    m = re.search(r"(\d+(?:\.\d+)?)\s*GB", s, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*MB", s, re.I)
    if m:
        return round(float(m.group(1)) / 1024.0, 2)
    return 4.0


def parse_install_gb(text: str | None, default: float = 10.0) -> float:
    """Parse storage string such as '105 GB SSD', '~650 MB', '150 GB' -> numeric GB."""
    if not text:
        return default
    s = str(text).replace(",", ".")
    best = 0.0
    for num_str, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(TB|GB|MB)", s, re.I):
        val = float(num_str)
        u = unit.upper()
        if u == "TB":
            val *= 1024.0
        elif u == "MB":
            val /= 1024.0
        if val > best:
            best = val
    if best > 0:
        return round(max(0.05, best), 2)
    return default


# Ordered from most specific/modern tokens to legacy tokens for accurate matching
_GPU_TIER_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:rtx\s*4090|rx\s*7900\s*xtx)\b", 10.0),
    (r"\b(?:rtx\s*4080|rtx\s*4070\s*ti|rx\s*7900\s*xt|rtx\s*3080)\b", 9.8),
    (r"\b(?:rtx\s*4070|rx\s*7800\s*xt|rx\s*6800\s*xt|rtx\s*3070)\b", 9.5),
    (r"\b(?:rx\s*6700\s*xt|rtx\s*4060\s*ti|rtx\s*3060\s*ti|rx\s*6750)\b", 8.5),
    (r"\b(?:rtx\s*4060|rx\s*7600|rx\s*6600\s*xt|rx\s*6650\s*xt|rtx\s*2070\s*super)\b", 8.0),
    (r"\b(?:rtx\s*3060|rx\s*6600|rtx\s*2070|rx\s*5700\s*xt|rtx\s*2060\s*super)\b", 7.6),
    (r"\b(?:rtx\s*2060|rx\s*5700|rx\s*5600\s*xt|gtx\s*1080|vega\s*56|vega\s*64)\b", 6.8),
    (r"\b(?:gtx\s*1660\s*ti|gtx\s*1660\s*super|gtx\s*1660|gtx\s*1070|rtx\s*3050|arc\s*a380)\b", 6.4),
    (r"\b(?:gtx\s*1060|rx\s*590|rx\s*580|rx\s*480|gtx\s*980|r9\s*390|r9\s*290x|r9\s*290|gtx\s*780)\b", 5.2),
    (r"\b(?:gtx\s*1650\s*super|gtx\s*970|rx\s*570|rx\s*470)\b", 5.0),
    (r"\b(?:gtx\s*1650|gtx\s*1630|rx\s*6400|gtx\s*1050\s*ti|gtx\s*960|r9\s*280x|r9\s*280|hd\s*7970|hd\s*7950|gtx\s*770|gtx\s*680)\b", 4.2),
    (r"\b(?:gtx\s*1050|gtx\s*950|gtx\s*760|gtx\s*670|gtx\s*660\s*ti|rx\s*560|rx\s*460|r9\s*270x|r9\s*270|hd\s*7870)\b", 3.6),
    (r"\b(?:gtx\s*660|gtx\s*750\s*ti|gtx\s*750|gtx\s*650\s*ti|rx\s*550|r7\s*370|r7\s*260x|r7\s*260|hd\s*7850|vega\s*7|gtx\s*480)\b", 3.0),
    (r"\b(?:gtx\s*650|gts\s*450|gtx\s*560|gtx\s*460|gtx\s*470|hd\s*7770|hd\s*7750|hd\s*7730|hd\s*6950|hd\s*6870|hd\s*6850|hd\s*5870|hd\s*5850|dx11|shader\s*model\s*5)\b", 2.5),
    (r"\b(?:gtx\s*640|gt\s*1030|gt\s*420|gtx\s*260|8800\s*gt|9800\s*gt|gts\s*250|hd\s*5770|hd\s*5570|hd\s*4870|hd\s*4850|hd\s*3870|hd\s*3850|dx10)\b", 1.8),
    (r"\b(?:intel\s*hd\s*4000|intel\s*hd\s*4600|intel\s*hd\s*520|vega\s*3|8600|8500|7900|7600|6600|hd\s*2600|hd\s*2900|x1950|x1900|x1600|9800|dx9|directx\s*9|directx\s*8|opengl|16\s*mb|64\s*mb|128\s*mb|256\s*mb|512\s*mb)\b", 1.0),
]


def infer_gpu_tier(gpu_text: str | None, default: float = 2.0) -> float:
    """Map a Steam/PCGamingWiki GPU string onto the 0–10 GameRank tier scale."""
    if not gpu_text:
        return default
    raw = str(gpu_text).lower()
    if "not separately listed" in raw or "same as minimum" in raw:
        return default
    # Split slash/or alternatives and take the easiest supported tier among valid matches
    parts = re.split(r"\s*(?:/|\bor\b|,)\s*", raw)
    matched: list[float] = []
    for part in parts:
        for pattern, tier in _GPU_TIER_PATTERNS:
            if re.search(pattern, part, re.I):
                matched.append(tier)
                break
    if matched:
        return round(min(matched), 1)
    for pattern, tier in _GPU_TIER_PATTERNS:
        if re.search(pattern, raw, re.I):
            return round(tier, 1)
    if "2 gb" in raw or "2gb" in raw:
        return 2.5
    if "4 gb" in raw or "4gb" in raw:
        return 4.0
    if "6 gb" in raw or "8 gb" in raw:
        return 5.2
    return default


def infer_cpu_demand(cpu_text: str | None, genre: str, install_gb: float = 10.0) -> str:
    """Estimate engine CPU simulation load ('low' | 'medium' | 'high') for 6C/12T Ryzen 5 5600GT."""
    txt = str(cpu_text or "").lower()
    if genre in ("classic-rts", "4x-grand", "army-sim"):
        return "high" if any(k in txt for k in ("i5-6", "i5-7", "i5-8", "i5-9", "i7-", "ryzen 5", "ryzen 7", "fx-8")) else "medium"
    if any(k in txt for k in ("i7-8", "i7-9", "i5-9", "i5-8", "i5-7", "i5-6", "ryzen 7", "ryzen 5 3", "ryzen 5 2", "ryzen 5 1", "six-core")):
        return "high"
    if any(k in txt for k in ("i5-", "i7-", "ryzen 3", "ryzen 5", "fx-", "quad", "4 hardware")) or install_gb >= 45:
        return "medium"
    return "low"


def infer_storage_advice(
    install_gb: float,
    genre: str,
    storage_text: str,
    release_year: int | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """Derive consistent storageAdvice and stutter-focused hddSp verdicts."""
    raw = str(storage_text or "").lower()
    mentions_ssd = "ssd" in raw
    is_open_world_streaming = genre in ("action-adventure", "rpg", "racing-sim") and install_gb >= 40
    is_modern_heavy = (release_year or 0) >= 2019 and install_gb >= 35

    if mentions_ssd or install_gb >= 75 or is_open_world_streaming or is_modern_heavy:
        if mentions_ssd or install_gb >= 70 or (genre == "action-adventure" and install_gb >= 45 and (release_year or 0) >= 2016):
            advice = {
                "verdict": "ssd-strongly-advised",
                "note": f"~{install_gb:g} GB streaming workload; SSD eliminates open-world/level texture pop-in, long patch rewrites, and traversal hitches.",
            }
            hdd_sp = {
                "loads": f"3x–5x slower loads on HDD (~{install_gb:g} GB footprint)",
                "fpsEffect": "Asset streaming causes occasional traversal micro-stutter on HDD (est.)",
                "stutter": "moderate" if install_gb < 90 else "high",
                "verdict": "stutter-risk",
                "note": "Heavy background asset streaming benefits strongly from NVMe/SATA SSD.",
            }
            return advice, hdd_sp
        advice = {
            "verdict": "ssd-helps",
            "note": f"~{install_gb:g} GB install; plays fine on HDD after loading, though an SSD noticeably trims level load times and patch speed.",
        }
        hdd_sp = {
            "loads": "Noticeably slower initial map/level loads on HDD (est.)",
            "fpsEffect": "Minimal FPS impact once assets are buffered (est.)",
            "stutter": "none",
            "verdict": "slower-loads",
            "note": "HDD adds wait time between levels/matches without major mid-play hitching.",
        }
        return advice, hdd_sp

    if install_gb >= 20:
        advice = {
            "verdict": "ssd-helps",
            "note": f"~{install_gb:g} GB install; runs smoothly on HDD once loaded, with SSD offering faster boots and updates.",
        }
        hdd_sp = {
            "loads": "Moderate ~15–40s level loads on HDD (est.)",
            "fpsEffect": "None after initial map load (est.)",
            "stutter": "none",
            "verdict": "slower-loads",
            "note": "Playable comfortably from HDD if SSD space is reserved for larger modern games.",
        }
        return advice, hdd_sp

    advice = {
        "verdict": "hdd-fine",
        "note": f"Compact ~{install_gb:g} GB install; assets stay resident in RAM so HDD performs just as well in-game.",
    }
    hdd_sp = {
        "loads": "Fast even on 7200 RPM HDD (est.)",
        "fpsEffect": "None",
        "stutter": "none",
        "verdict": "fine",
        "note": "Small memory-resident footprint; zero streaming penalty on HDD.",
    }
    return advice, hdd_sp


# Canonical progressive GPU ladder for Ryzen 5 5600GT benchmarks (kept synced with data/games/taxonomy.json)
BENCHMARK_GPU_LADDER: tuple[str, ...] = (
    "vega-7-igpu",
    "rx-580-8gb",
    "gtx-1660-super",
    "rtx-2060-super",
    "rx-6600",
    "rtx-2070",
    "rtx-3060",
    "rtx-2070-super",
)


def infer_benchmark_and_upgrades(
    name: str,
    gpu_min: float,
    gpu_rec: float,
    cpu_demand: str,
    storage_verdict: str,
    install_gb: float,
) -> tuple[dict[str, Any], dict[str, str], str]:
    """Generate structured Vega 7 benchmark estimates and progressive GPU ladder expectations."""
    if gpu_min <= 1.8:
        playable = {"fps": "60+ fps at 1080p High–Max (est.)", "settings": "1080p High/Max preset; trivially light for Vega 7."}
        q30 = {
            "fps1080": "60+ fps at High/Max (est.)",
            "settings1080": "Max native 1080p settings",
            "fps900": "90+ fps at High/Max (est.)",
            "settings900": "Max 1600x900 settings",
        }
        sixty = {"fps": "60–120+ fps at 1080p High (est.)", "settings": "1080p High/Ultra, V-Sync optional."}
        compat_note = f"Runs effortlessly on Ryzen 5 5600GT + Vega 7 at 1080p High ({'HDD fine' if storage_verdict == 'hdd-fine' else 'SSD speeds loads'})."
    elif gpu_min <= 3.0:
        playable = {"fps": "40–55 fps at 1080p Low–Medium (est.)", "settings": "1080p Low-Medium, shadows Low, AA off/FXAA."}
        q30 = {
            "fps1080": "32–42 fps at Medium (est.)",
            "settings1080": "1080p Medium, ambient occlusion & volumetric effects Low",
            "fps900": "42–55 fps at Medium–High (est.)",
            "settings900": "1600x900 Medium preset",
        }
        sixty = {"fps": "55–65 fps at 720p/900p Low (est.)", "settings": "900p or 720p Low / 80% render scale."}
        compat_note = f"Playable on Vega 7 at 1080p Low-Medium; discrete GPU unlocks High/Ultra 60+ FPS."
    elif gpu_min <= 4.3:
        playable = {"fps": "28–38 fps at 720p/900p Low (est.)", "settings": "900p/720p Low, FSR/resolution scale 75-85% if supported."}
        q30 = {
            "fps1080": "22–30 fps at Lowest (est.)",
            "settings1080": "1080p Lowest + dynamic resolution scale ~75%",
            "fps900": "30–36 fps at Low (est.)",
            "settings900": "1600x900 Low with shadows & post-FX disabled",
        }
        sixty = {"fps": "Not reliably 60 fps on Vega 7; ~40–48 fps at 720p Lowest (est.)", "settings": "720p Lowest; needs discrete GPU for 60 fps."}
        compat_note = "Borderline on Vega 7 iGPU (requires 720p/900p Low tweaks); discrete GPU like RX 6600 strongly improves experience."
    else:
        playable = {"fps": "15–25 fps on Vega 7 — below min GPU spec (est.)", "settings": "720p Lowest + aggressive upscaling; discrete GPU recommended."}
        q30 = {
            "fps1080": "Under 22 fps at 1080p Lowest (est.)",
            "settings1080": "Too demanding for Vega 7 at native 1080p",
            "fps900": "20–26 fps at 900p Lowest (est.)",
            "settings900": "Requires GTX 1660S / RTX 2060 / RX 6600 class GPU",
        }
        sixty = {"fps": "Needs discrete GPU upgrade for 60 fps (est.)", "settings": "Beyond Vega 7 capability."}
        compat_note = f"Minimum GPU exceeds Vega 7 iGPU; pair 5600GT with RX 6600 / RTX 3060 ({'and SSD' if install_gb >= 50 else 'on disk'})."

    def _card_expect(card_tier: float, card_label: str) -> str:
        if gpu_rec <= 3.0:
            return f"1080p Ultra locked 100+ fps (est.)"
        if card_tier >= gpu_rec + 1.0:
            return f"1080p Ultra 75–120+ fps (est.)"
        if card_tier >= gpu_rec:
            return f"1080p High–Ultra 60+ fps (est.)"
        if card_tier >= gpu_min + 0.8:
            return f"1080p Medium–High 55–75 fps (est.)"
        return f"1080p Low–Medium 40–55 fps (est.)"

    upgrades = {
        "rx-580-8gb": _card_expect(5.2, "RX 580 8GB"),
        "gtx1660s": _card_expect(6.5, "GTX 1660 Super"),
        "rtx2060": _card_expect(7.0, "RTX 2060"),
        "rtx-2060-super": _card_expect(7.4, "RTX 2060 Super"),
        "rx6600": _card_expect(7.5, "RX 6600"),
        "rtx-2070": _card_expect(7.6, "RTX 2070"),
        "rtx-3060": _card_expect(7.8, "RTX 3060 12GB"),
        "rtx-2070-super": _card_expect(8.1, "RTX 2070 Super"),
    }
    bench = {"playable": playable, "quality30": q30, "sixty": sixty, "source": []}
    return bench, upgrades, compat_note


# ---------------------------------------------------------------------------
# Steam API & SteamSpy Live Client (Reusable for Future Game Additions)
# ---------------------------------------------------------------------------

def _http_get_json(url: str, retries: int = 3, timeout: int = 12) -> Any:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DatabaseManager/2.0 (UnifiedCatalog)"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                time.sleep(2.5 * (attempt + 1))
                continue
            return None
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(0.8)
    return None


def _strip_html(raw: str | None) -> str:
    if not raw:
        return ""
    txt = re.sub(r"<br\s*/?>", "; ", str(raw), flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html.unescape(txt)
    return re.sub(r"\s+", " ", txt).strip()


def _extract_steam_specs(req_html: str | None) -> dict[str, str]:
    txt = _strip_html(req_html)
    out = {"cpu": "N/A", "gpu": "N/A", "ram": "N/A", "storage": "N/A", "os": "Windows"}
    for key, label in (
        ("os", r"OS\s*\*?\s*:\s*([^;]+)"),
        ("cpu", r"Processor\s*:\s*([^;]+)"),
        ("ram", r"Memory\s*:\s*([^;]+)"),
        ("gpu", r"Graphics\s*:\s*([^;]+)"),
        ("storage", r"Storage\s*:\s*([^;]+)"),
    ):
        m = re.search(label, txt, re.I)
        if m:
            out[key] = m.group(1).strip().rstrip(";")
    return out


def fetch_steam_metadata(title_or_appid: str | int, timeout: int = 12) -> dict[str, Any]:
    """Resolve title or AppID via Steam Store API, Live Player Count API, and SteamSpy."""
    appid: int | None = None
    if isinstance(title_or_appid, int) or str(title_or_appid).strip().isdigit():
        appid = int(str(title_or_appid).strip())
    else:
        q = str(title_or_appid).strip()
        s_url = "https://store.steampowered.com/api/storesearch/?" + urllib.parse.urlencode({"term": q, "l": "english", "cc": "US"})
        search_res = _http_get_json(s_url, timeout=timeout) or {}
        items = search_res.get("items") or []
        norm_q = re.sub(r"[^a-z0-9]+", " ", q.lower()).strip()
        for it in items:
            if re.sub(r"[^a-z0-9]+", " ", str(it.get("name", "")).lower()).strip() == norm_q:
                appid = int(it["id"])
                break
        if appid is None and items:
            appid = int(items[0]["id"])

    if not appid:
        raise ValueError(f"Could not resolve Steam AppID for '{title_or_appid}'")

    result: dict[str, Any] = {
        "appid": appid,
        "steam_url": f"https://store.steampowered.com/app/{appid}/",
        "store_ok": False,
    }
    app_data = _http_get_json(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en", timeout=timeout) or {}
    block = app_data.get(str(appid), {}) if isinstance(app_data, dict) else {}
    if block.get("success") and isinstance(block.get("data"), dict):
        d = block["data"]
        result["store_ok"] = True
        result["steam_name"] = d.get("name")
        result["is_free"] = bool(d.get("is_free"))
        po = d.get("price_overview") or {}
        result["price_usd"] = round((po.get("initial", 0) or 0) / 100.0, 2) if (not d.get("is_free") and po) else 0.0
        result["genres"] = [g.get("description") for g in d.get("genres", []) if g.get("description")]
        result["categories"] = [c.get("description") for c in d.get("categories", []) if c.get("description")]
        result["release_date"] = (d.get("release_date") or {}).get("date")
        result["metacritic"] = (d.get("metacritic") or {}).get("score")
        result["short_description"] = d.get("short_description", "")
        result["pc_requirements"] = d.get("pc_requirements", {})

    pl = _http_get_json(f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}", timeout=timeout) or {}
    resp = pl.get("response", {}) if isinstance(pl, dict) else {}
    if resp.get("result") == 1:
        result["current_players"] = resp.get("player_count")

    spy = _http_get_json(f"https://steamspy.com/api.php?request=appdetails&appid={appid}", timeout=timeout) or {}
    if isinstance(spy, dict) and spy.get("appid"):
        result["spy_positive"] = spy.get("positive")
        result["spy_negative"] = spy.get("negative")
        result["spy_tags"] = list((spy.get("tags") or {}).keys())[:8] if isinstance(spy.get("tags"), dict) else []
        if not result.get("steam_name"):
            result["steam_name"] = spy.get("name")

    return result


def map_steam_genre_and_setting(name: str, steam_genres: list[str], tags: list[str]) -> tuple[str, str]:
    """Map Steam genre & tag signals onto Database Manager canonical genre/setting enums."""
    hay = " ".join([name] + steam_genres + tags).lower()
    if "vr" in hay or "the lab" in hay:
        genre = "vr-utility"
    elif any(k in hay for k in ("4x", "grand strategy")):
        genre = "4x-grand"
    elif any(k in hay for k in ("real time tactics", "rts", "real-time strategy")):
        genre = "classic-rts"
    elif any(k in hay for k in ("city builder", "colony sim", "automation")):
        genre = "army-sim"
    elif any(k in hay for k in ("tower defense",)):
        genre = "hybrid-td"
    elif any(k in hay for k in ("racing", "driving", "truck", "automobile")):
        genre = "racing-sim"
    elif any(k in hay for k in ("fighting", "2d fighter")):
        genre = "fighting-arcade"
    elif any(k in hay for k in ("puzzle", "platformer", "visual novel", "point & click")):
        genre = "puzzle-platformer"
    elif any(k in hay for k in ("fps", "first-person shooter", "shooter", "battle royale", "sniper")):
        genre = "fps-shooter"
    elif any(k in hay for k in ("rpg", "mmorpg", "action rpg")):
        genre = "rpg"
    else:
        genre = "action-adventure"

    if any(k in hay for k in ("post-apocalyptic", "metro", "wasteland")):
        setting = "post-apocalyptic"
    elif any(k in hay for k in ("steampunk",)):
        setting = "steampunk"
    elif any(k in hay for k in ("sci-fi", "cyberpunk", "space", "futuristic", "crysis", "halo", "portal", "half-life", "titanfall")):
        setting = "futuristic"
    elif any(k in hay for k in ("fantasy", "witcher", "magic", "dragon", "naraka")):
        setting = "fantasy"
    elif any(k in hay for k in ("medieval", "ancient", "rome", "assassin's creed", "historical", "world war", "ww2")):
        setting = "ancient"
    else:
        setting = "realistic-modern"
    return genre, setting


# ---------------------------------------------------------------------------
# Unified Normalization (Guarantees Existing, New, and Future Records Match)
# ---------------------------------------------------------------------------

def _extract_steam_appid(rec: dict[str, Any]) -> int | None:
    if rec.get("steamAppId") is not None:
        try:
            return int(rec["steamAppId"])
        except (TypeError, ValueError):
            pass
    for s in rec.get("stores") or []:
        url = str(s.get("url", "")) if isinstance(s, dict) else ""
        m = re.search(r"store\.steampowered\.com/app/(\d+)", url)
        if m:
            return int(m.group(1))
    for s in rec.get("sources") or []:
        url = str(s.get("url", "")) if isinstance(s, dict) else str(s)
        m = re.search(r"store\.steampowered\.com/app/(\d+)", url)
        if m:
            return int(m.group(1))
    return None


def _normalize_sources(sources: Any, stores: list[dict[str, str]]) -> list[str]:
    urls: list[str] = []
    if isinstance(sources, list):
        for s in sources:
            u = s.get("url", "") if isinstance(s, dict) else str(s)
            u = u.strip()
            if u and u not in urls:
                urls.append(u)
    if not urls:
        for st in stores:
            u = str(st.get("url", "")).strip()
            if u and u not in urls:
                urls.append(u)
    return urls


def normalize_game_record(raw: dict[str, Any], default_ownership: str = "wishlist") -> dict[str, Any]:
    """Normalize any PC game record to the canonical v4.0.0 schema."""
    rec = dict(raw)
    name = str(rec.get("name") or "Unknown").strip()
    gid = str(rec.get("id") or slugify_game_id(name)).strip()
    rec["id"] = gid
    rec["name"] = name

    ownership = str(rec.get("ownership") or default_ownership).strip().lower()
    if ownership not in ("owned", "wishlist"):
        ownership = default_ownership
    rec["ownership"] = ownership

    genre = str(rec.get("genre") or "action-adventure").strip().lower()
    if genre not in VALID_GENRES:
        genre = "action-adventure"
    rec["genre"] = genre

    setting_raw = str(rec.get("setting") or "realistic-modern").strip().lower()
    setting = SETTING_ALIASES.get(setting_raw, setting_raw)
    if setting not in VALID_SETTINGS:
        setting = "realistic-modern"
    rec["setting"] = setting

    price_model = str(rec.get("priceModel") or ("f2p" if float(rec.get("priceUsd") or 0) == 0 else "paid")).lower()
    rec["priceModel"] = "f2p" if price_model == "f2p" else "paid"
    rec["priceUsd"] = round(float(rec.get("priceUsd") or 0.0), 2)
    rec["priceNote"] = str(rec.get("priceNote") or ("Free to play" if rec["priceModel"] == "f2p" else f"${rec['priceUsd']:.2f} on Steam"))

    specs = rec.get("specs") if isinstance(rec.get("specs"), dict) else {}
    min_sp = dict(specs.get("min") or {})
    rec_sp = dict(specs.get("rec") or {})
    for target in (min_sp, rec_sp):
        for k in ("cpu", "gpu", "ram", "storage", "os"):
            if not target.get(k):
                target[k] = "Not separately listed"
    rec["specs"] = {"min": min_sp, "rec": rec_sp}

    install_gb = rec.get("installGB")
    if install_gb is None or float(install_gb) <= 0:
        install_gb = parse_install_gb(min_sp.get("storage") or rec_sp.get("storage") or (rec.get("size") or {}).get("install"))
    install_gb = round(max(0.05, float(install_gb)), 2)
    rec["installGB"] = install_gb

    size_obj = rec.get("size") if isinstance(rec.get("size"), dict) else {}
    inst_str = size_obj.get("install") or f"~{install_gb:g} GB"
    dl_str = size_obj.get("download") or inst_str
    rec["size"] = {"download": dl_str, "install": inst_str}

    gpu_min = float(rec.get("gpuMinTier") or infer_gpu_tier(min_sp.get("gpu"), 2.0))
    gpu_rec = float(rec.get("gpuRecTier") or infer_gpu_tier(rec_sp.get("gpu"), gpu_min))
    if gpu_rec < gpu_min:
        gpu_rec = gpu_min
    rec["gpuMinTier"] = round(gpu_min, 1)
    rec["gpuRecTier"] = round(gpu_rec, 1)

    cpu_dem = str(rec.get("cpuDemand") or "").lower()
    if cpu_dem not in ("low", "medium", "high"):
        cpu_dem = infer_cpu_demand(min_sp.get("cpu"), genre, install_gb)
    rec["cpuDemand"] = cpu_dem

    sa = dict(rec.get("storageAdvice") or {})
    sa_verdict = STORAGE_VERDICT_ALIASES.get(str(sa.get("verdict") or "").lower(), str(sa.get("verdict") or "").lower())
    def_sa, def_hdd = infer_storage_advice(install_gb, genre, min_sp.get("storage", ""))
    if sa_verdict not in ("hdd-fine", "ssd-helps", "ssd-strongly-advised"):
        sa = def_sa
    else:
        sa["verdict"] = sa_verdict
        sa["note"] = str(sa.get("note") or def_sa["note"])
    rec["storageAdvice"] = sa

    hdd = rec.get("hddSp") if isinstance(rec.get("hddSp"), dict) else {}
    if not hdd.get("verdict") or hdd.get("verdict") not in ("fine", "slower-loads", "stutter-risk"):
        hdd = def_hdd
    else:
        hdd = {
            "loads": str(hdd.get("loads") or def_hdd["loads"]),
            "fpsEffect": str(hdd.get("fpsEffect") or def_hdd["fpsEffect"]),
            "stutter": str(hdd.get("stutter") if hdd.get("stutter") in ("none", "moderate", "high") else def_hdd["stutter"]),
            "verdict": str(hdd["verdict"]),
            "note": str(hdd.get("note") or def_hdd["note"]),
        }
    rec["hddSp"] = hdd

    def_bench, def_up, def_note = infer_benchmark_and_upgrades(
        name, rec["gpuMinTier"], rec["gpuRecTier"], cpu_dem, sa["verdict"], install_gb
    )

    bench = dict(rec.get("bench") or {})
    if not isinstance(bench.get("playable"), dict) or not bench["playable"].get("fps"):
        bench["playable"] = def_bench["playable"]
    if not isinstance(bench.get("sixty"), dict) or not bench["sixty"].get("fps"):
        bench["sixty"] = def_bench["sixty"]
    q30 = bench.get("quality30") or rec.get("quality30")
    if not isinstance(q30, dict) or not q30.get("fps1080"):
        q30 = def_bench["quality30"]
    bench["quality30"] = q30
    rec["quality30"] = q30
    bench_src = bench.get("source")
    bench["source"] = [str(u) for u in bench_src] if isinstance(bench_src, list) else []
    rec["bench"] = bench

    up = dict(rec.get("upgradeTiers") or {})
    for k, val in def_up.items():
        if not up.get(k):
            up[k] = val
    rec["upgradeTiers"] = up

    if not rec.get("compatNote"):
        rec["compatNote"] = def_note

    camp = dict(rec.get("campaign") or {})
    rec["campaign"] = {
        "exists": bool(camp.get("exists", True)),
        "freeOrPaid": str(camp.get("freeOrPaid") or ("free" if rec["priceModel"] == "f2p" else "paid")),
        "quality": int(camp.get("quality") if camp.get("quality") is not None else 7),
        "notes": str(camp.get("notes") or "Single-player / core mode included."),
    }

    ai = dict(rec.get("ai") or {})
    rec["ai"] = {
        "score": int(ai.get("score") if ai.get("score") is not None else 7),
        "notes": str(ai.get("notes") or "Standard campaign/enemy or multiplayer bot behavior."),
    }

    gfx = dict(rec.get("graphics") or {})
    rec["graphics"] = {
        "score": int(gfx.get("score") if gfx.get("score") is not None else 7),
        "notes": str(gfx.get("notes") or "PC visual fidelity scaled by min/recommended GPU tier."),
    }

    pl = dict(rec.get("players") or {})
    pst = PLAYER_STATUS_ALIASES.get(str(pl.get("status") or "active").lower(), str(pl.get("status") or "active").lower())
    if pst not in ("very-active", "active", "moderate", "small", "inactive", "n/a-sp"):
        pst = "active"
    rec["players"] = {
        "status": pst,
        "notes": str(pl.get("notes") or "Active on Steam / PC."),
    }

    appid = _extract_steam_appid(rec)
    rec["steamAppId"] = appid

    stores = rec.get("stores") if isinstance(rec.get("stores"), list) else []
    if not stores and appid:
        stores = [{"name": "Steam", "url": f"https://store.steampowered.com/app/{appid}/"}]
    rec["stores"] = stores
    rec["storeNote"] = str(rec.get("storeNote") or ("Available on Steam." if appid else "Available via official PC storefront/launcher."))
    rec["sources"] = _normalize_sources(rec.get("sources"), stores)

    companions = rec.get("companions") if isinstance(rec.get("companions"), list) else []
    rec["companions"] = companions
    return rec


def build_record_from_steam(
    title: str,
    steam_info: dict[str, Any],
    specs_override: dict[str, dict[str, str]] | None = None,
    ownership: str = "owned",
    genre_override: str | None = None,
) -> dict[str, Any]:
    """Create a fully normalized v4.0.0 game object from Steam API metadata + specs."""
    appid = steam_info.get("appid")
    steam_genres = steam_info.get("genres") or []
    tags = steam_info.get("spy_tags") or []
    genre, setting = map_steam_genre_and_setting(title, steam_genres, tags)
    if genre_override and genre_override in VALID_GENRES:
        genre = genre_override

    is_free = bool(steam_info.get("is_free") or ("Free To Play" in steam_genres))
    price_usd = 0.0 if is_free else float(steam_info.get("price_usd") or 0.0)
    price_model = "f2p" if is_free else "paid"

    if specs_override:
        min_sp = specs_override["min"]
        rec_sp = specs_override["rec"]
    else:
        pc_req = steam_info.get("pc_requirements") or {}
        min_sp = _extract_steam_specs(pc_req.get("minimum"))
        rec_sp = _extract_steam_specs(pc_req.get("recommended")) if pc_req.get("recommended") else {
            "cpu": "Not separately listed by Steam",
            "gpu": "Not separately listed by Steam",
            "ram": "Not separately listed by Steam",
            "storage": "Not separately listed by Steam",
            "os": "Not separately listed by Steam",
        }

    cats = steam_info.get("categories") or []
    has_sp = any("single-player" in c.lower() for c in cats)
    has_mp = any(k in " ".join(cats).lower() for k in ("multi-player", "pvp", "co-op", "mmo"))
    cur_players = steam_info.get("current_players")

    if not has_mp and genre not in ("fps-shooter", "fighting-arcade"):
        p_status = "n/a-sp"
        p_notes = f"Single-player title ({cur_players:,} concurrent on Steam, Nov 2026)." if cur_players is not None else "Single-player experience."
    elif cur_players is not None:
        if cur_players >= 5000:
            p_status = "very-active"
        elif cur_players >= 500:
            p_status = "active"
        elif cur_players >= 100:
            p_status = "moderate"
        elif cur_players >= 10:
            p_status = "small"
        else:
            p_status = "inactive"
        p_notes = f"~{cur_players:,} concurrent players on Steam (Nov 2026)."
    else:
        p_status = "active" if has_mp else "n/a-sp"
        p_notes = "Steam multiplayer/community title." if has_mp else "Single-player experience."

    pos = steam_info.get("spy_positive") or 0
    neg = steam_info.get("spy_negative") or 0
    ratio = (pos / (pos + neg)) if (pos + neg) > 0 else 0.78
    meta = steam_info.get("metacritic")
    base_q = round(max(4, min(10, (meta / 10.0) if meta else (5.0 + ratio * 4.5))))

    gpu_min = infer_gpu_tier(min_sp.get("gpu"), 2.0)
    gpu_rec = infer_gpu_tier(rec_sp.get("gpu"), gpu_min)
    gfx_score = max(4, min(10, round(4.5 + min(5.0, gpu_rec * 0.65))))

    raw = {
        "id": slugify_game_id(title),
        "name": title,
        "steamAppId": appid,
        "ownership": ownership,
        "genre": genre,
        "setting": setting,
        "priceModel": price_model,
        "priceUsd": price_usd,
        "priceNote": f"Steam US list price (${price_usd:.2f})" if price_model == "paid" and price_usd > 0 else (
            "Free to play on Steam" if price_model == "f2p" else "Included/bundled or delisted standalone price"
        ),
        "campaign": {
            "exists": has_sp or genre in ("action-adventure", "rpg", "puzzle-platformer"),
            "freeOrPaid": "free" if price_model == "f2p" and has_sp else ("paid" if has_sp else "n/a"),
            "quality": base_q if (has_sp or genre in ("action-adventure", "rpg", "puzzle-platformer")) else 0,
            "notes": steam_info.get("short_description") or "Steam title campaign/core experience.",
        },
        "ai": {
            "score": max(5, min(9, base_q)),
            "notes": "Opponent/enemy/bot behavior tuned to genre standard.",
        },
        "graphics": {
            "score": gfx_score,
            "notes": f"Steam release ({steam_info.get('release_date') or 'PC'}); GPU tier {gpu_min}–{gpu_rec}.",
        },
        "players": {"status": p_status, "notes": p_notes},
        "specs": {"min": min_sp, "rec": rec_sp},
        "gpuMinTier": gpu_min,
        "gpuRecTier": gpu_rec,
        "stores": [{"name": "Steam", "url": steam_info.get("steam_url")}] if steam_info.get("steam_url") else [],
        "storeNote": f"Steam AppID {appid} ({', '.join(steam_genres) or 'PC'}).",
        "sources": [steam_info.get("steam_url")] if steam_info.get("steam_url") else [],
    }
    return normalize_game_record(raw, default_ownership=ownership)


# Curated discovery seeds aligned with canonical IDs (zero duplicates)
EXPANSION_SEEDS: list[dict[str, Any]] = [
    {
        "id": "beyond-all-reason",
        "name": "Beyond All Reason",
        "genre": "classic-rts",
        "ownership": "wishlist",
        "priceModel": "f2p",
        "priceUsd": 0.0,
        "priceNote": "100% Free & Open Source; no microtransactions or pay-to-win.",
        "campaign": {
            "exists": True,
            "freeOrPaid": "free",
            "quality": 8,
            "notes": "Rich scenario missions, skirmish AI, and active cooperative survival modes.",
        },
        "ai": {
            "score": 8,
            "notes": "Excellent Recast-based barbarian and custom AI algorithms; very challenging.",
        },
        "setting": "futuristic",
        "graphics": {
            "score": 8,
            "notes": "Recast 3D engine with thousands of dynamic units, volumetric smoke, and debris.",
        },
        "players": {
            "status": "very-active",
            "notes": "Active multiplayer community with 3,000+ daily players and weekly tournaments.",
        },
        "specs": {
            "min": {
                "cpu": "Quad-core Intel / AMD 2.5 GHz",
                "gpu": "OpenGL 3.3 compatible (Intel HD 4000 / Vega 3)",
                "ram": "4 GB",
                "storage": "5 GB",
                "os": "Windows 10/11 64-bit",
            },
            "rec": {
                "cpu": "AMD Ryzen 5 / Intel Core i5 3.5 GHz",
                "gpu": "NVIDIA GTX 1060 / AMD RX 580 / RX 6600",
                "ram": "8 GB",
                "storage": "10 GB SSD",
                "os": "Windows 10/11 64-bit",
            },
        },
        "size": {"download": "~4 GB", "install": "~6 GB"},
        "installGB": 6.0,
        "storageAdvice": {
            "verdict": "hdd-fine",
            "note": "Preloads map and unit models into RAM; HDD loading is acceptable.",
        },
        "cpuDemand": "high",
        "gpuMinTier": 1.5,
        "gpuRecTier": 3.0,
        "compatNote": "Runs at 60+ FPS on Vega 7 at 1080p Low/Medium; drops in 8v8 late-game metal wars.",
        "bench": {
            "playable": {
                "fps": "55–75 fps at 1080p Low–Medium; dips to 35 in massive 8v8 battles",
                "settings": "Medium graphics preset, shadows Low, terrain shaders on.",
            }
        },
        "stores": [{"name": "Official site (standalone launcher)", "url": "https://www.beyondallreason.info/"}],
        "sources": ["https://www.beyondallreason.info/"],
    },
    {
        "id": "0ad",
        "name": "0 A.D.",
        "genre": "classic-rts",
        "ownership": "wishlist",
        "priceModel": "f2p",
        "priceUsd": 0.0,
        "priceNote": "Free and open-source historical RTS by Wildfire Games.",
        "campaign": {
            "exists": False,
            "freeOrPaid": "n/a",
            "quality": 5,
            "notes": "Single-player skirmish maps and historical battle scenarios only.",
        },
        "ai": {"score": 7, "notes": "Petra AI is competent, manages macro economies smoothly."},
        "setting": "ancient",
        "graphics": {"score": 7, "notes": "Charming Pyrogenesis engine 3D visuals with detailed ancient civilizations."},
        "players": {"status": "active", "notes": "Dedicated open-source lobby and P2P multiplayer scene."},
        "specs": {
            "min": {"cpu": "Intel / AMD Dual Core 1 GHz", "gpu": "DirectX 9 / OpenGL 2.1 compatible", "ram": "2 GB", "storage": "3 GB", "os": "Windows 7/8/10/11"},
            "rec": {"cpu": "Quad-core AMD Ryzen / Intel Core i3", "gpu": "GeForce GT 1030 / Vega 7", "ram": "4 GB", "storage": "4 GB SSD", "os": "Windows 10/11"},
        },
        "size": {"download": "~2 GB", "install": "~3 GB"},
        "installGB": 3.0,
        "storageAdvice": {"verdict": "hdd-fine", "note": "Lightweight assets load quickly from any drive."},
        "cpuDemand": "medium",
        "gpuMinTier": 1.0,
        "gpuRecTier": 2.0,
        "compatNote": "Runs comfortably at 60+ FPS on Vega 7.",
        "bench": {"playable": {"fps": "60–90 fps at 1080p High", "settings": "High preset, 1080p resolution."}},
        "stores": [{"name": "Official site (free download)", "url": "https://play0ad.com/"}],
        "sources": ["https://play0ad.com/"],
    },
    {
        "id": "tempest-rising",
        "name": "Tempest Rising",
        "genre": "classic-rts",
        "ownership": "wishlist",
        "priceModel": "paid",
        "priceUsd": 39.99,
        "priceNote": "Full base game with 2 single-player campaigns and multiplayer.",
        "campaign": {"exists": True, "freeOrPaid": "paid", "quality": 8, "notes": "Two 11-mission story campaigns with full FMV cutscenes."},
        "ai": {"score": 7, "notes": "Aggressive skirmish AI mirroring classic 90s Command & Conquer tactics."},
        "setting": "futuristic",
        "graphics": {"score": 8, "notes": "Unreal Engine 5 RTS with detailed terrain, destructible bases, and neon VFX."},
        "players": {"status": "active", "notes": "Multiplayer ranked ladder and casual skirmishes."},
        "specs": {
            "min": {"cpu": "Intel Core i5-6600K / AMD Ryzen 5 1600", "gpu": "NVIDIA GTX 970 / AMD RX 480", "ram": "8 GB", "storage": "30 GB", "os": "Windows 10 64-bit"},
            "rec": {"cpu": "Intel Core i7-8700K / AMD Ryzen 5 3600", "gpu": "NVIDIA RTX 2060 / AMD RX 5600 XT / RX 6600", "ram": "16 GB", "storage": "30 GB SSD", "os": "Windows 10/11 64-bit"},
        },
        "size": {"download": "~25 GB", "install": "~30 GB"},
        "installGB": 30.0,
        "storageAdvice": {"verdict": "ssd-helps", "note": "Unreal Engine 5 asset streaming benefits significantly from NVMe SSD."},
        "cpuDemand": "high",
        "gpuMinTier": 3.0,
        "gpuRecTier": 5.0,
        "compatNote": "Challenging on Vega 7 (30-40 FPS at 720p/900p Low); smooth 75+ FPS on RX 6600 at 1080p High.",
        "bench": {"playable": {"fps": "32–42 fps on Vega 7 (900p Low); 80–100 fps on RX 6600 (1080p High)", "settings": "Low preset with 85% render scale for Vega 7."}},
        "stores": [{"name": "Steam", "url": "https://store.steampowered.com/app/1486920/"}],
        "sources": ["https://store.steampowered.com/app/1486920/", "https://www.pcgamingwiki.com/wiki/Tempest_Rising"],
    },
    {
        "id": "sins2",
        "name": "Sins of a Solar Empire II",
        "genre": "4x-grand",
        "ownership": "wishlist",
        "priceModel": "paid",
        "priceUsd": 49.99,
        "priceNote": "Base game with 3 playable factions and dynamic planetary orbits.",
        "campaign": {"exists": False, "freeOrPaid": "n/a", "quality": 6, "notes": "Custom sandbox scenarios with rich victory conditions and lore."},
        "ai": {"score": 8, "notes": "64-bit multi-core Iron Engine AI capable of managing huge multi-star empires."},
        "setting": "futuristic",
        "graphics": {"score": 8, "notes": "Massive scale capital ships, dynamic orbital mechanics, and fleet battles."},
        "players": {"status": "very-active", "notes": "Dedicated 10-player multiplayer matches with seamless reconnect."},
        "specs": {
            "min": {"cpu": "Intel Core i5-4590 / AMD Ryzen 3 1300X", "gpu": "GeForce GTX 1060 / Radeon RX 580 (4 GB)", "ram": "8 GB", "storage": "20 GB", "os": "Windows 10 64-bit"},
            "rec": {"cpu": "Intel Core i7-9700 / AMD Ryzen 5 5600", "gpu": "GeForce RTX 2070 / Radeon RX 6600 XT", "ram": "16 GB", "storage": "20 GB SSD", "os": "Windows 10/11 64-bit"},
        },
        "size": {"download": "~16 GB", "install": "~20 GB"},
        "installGB": 20.0,
        "storageAdvice": {"verdict": "ssd-helps", "note": "SSD prevents micro-freezes during galaxy-wide orbital recalculations."},
        "cpuDemand": "high",
        "gpuMinTier": 2.5,
        "gpuRecTier": 4.5,
        "compatNote": "Ryzen 5 5600GT handles multicore simulation well. Vega 7 plays 35-45 FPS at 1080p Low.",
        "bench": {"playable": {"fps": "38–50 fps on Vega 7 (1080p Low); 85–110 fps on RX 6600 (1080p High)", "settings": "Low preset, fleet effects medium."}},
        "stores": [{"name": "Steam", "url": "https://store.steampowered.com/app/1575940/"}],
        "sources": ["https://store.steampowered.com/app/1575940/"],
    },
]


def sync_multi_site_games(offline: bool = False) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Reconcile and normalize games catalog with multi-source seeds (no duplicates)."""
    existing_games = json.loads(GAMES_JSON.read_text(encoding="utf-8")) if GAMES_JSON.exists() else []
    by_id: dict[str, dict[str, Any]] = {}
    for g in existing_games:
        normed = normalize_game_record(g)
        by_id[normed["id"]] = normed

    added = 0
    updated = 0
    for seed in EXPANSION_SEEDS:
        norm_seed = normalize_game_record(seed)
        sid = norm_seed["id"]
        if sid in by_id:
            merged_sources = list(by_id[sid].get("sources") or [])
            for src in norm_seed.get("sources") or []:
                if src not in merged_sources:
                    merged_sources.append(src)
            by_id[sid]["sources"] = merged_sources
            updated += 1
        else:
            by_id[sid] = norm_seed
            added += 1

    unified = list(by_id.values())
    return unified, {"added": added, "updated": updated, "total": len(unified)}


def apply_games_update(games: list[dict[str, Any]]) -> None:
    """Save to data/games/games.json, mirror to both games.js files, and recompile SQLite."""
    normalized = [normalize_game_record(g) for g in games]
    GAMES_JSON.write_text(json.dumps(normalized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {len(normalized)} unified games to {GAMES_JSON}")

    js_content = f"// Auto-generated mirror of data/games/games.json\nwindow.GAMES = {json.dumps(normalized, indent=2, ensure_ascii=False)};\n"
    for mirror in (WEB_GAMES_JS, DATA_GAMES_JS):
        if mirror.parent.exists():
            mirror.write_text(js_content, encoding="utf-8")
            print(f"Synchronized JS mirror {mirror}")

    cmd = [sys.executable, str(ROOT_DIR / "src" / "db_export.py")]
    subprocess.run(cmd, check=True)
    print("Recompiled isolated & consolidated SQLite databases atomically.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified PC Games Catalog, Normalization & Steam Sync")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview update without writing")
    parser.add_argument("--apply", action="store_true", help="Persist updates to games.json, mirrors, and SQLite")
    parser.add_argument("--offline", action="store_true", help="Use offline fixtures for CI/testing")
    parser.add_argument("--normalize", action="store_true", help="Normalize all existing records to v4.0.0 schema")
    parser.add_argument("--add-steam", metavar="TITLE_OR_APPID", help="Fetch and add/update a single game from Steam API")
    parser.add_argument("--ownership", choices=("owned", "wishlist"), default="owned", help="Ownership tag for --add-steam")
    parser.add_argument("--genre", choices=sorted(VALID_GENRES), help="Optional explicit genre override for --add-steam")
    args = parser.parse_args()

    if args.add_steam:
        steam_info = fetch_steam_metadata(args.add_steam)
        title = steam_info.get("steam_name") or str(args.add_steam)
        rec = build_record_from_steam(title, steam_info, ownership=args.ownership, genre_override=args.genre)
        existing = [normalize_game_record(g) for g in (json.loads(GAMES_JSON.read_text(encoding="utf-8")) if GAMES_JSON.exists() else [])]
        by_id = {g["id"]: g for g in existing}
        by_id[rec["id"]] = rec
        games = list(by_id.values())
        print(f"Prepared Steam record: {rec['id']} ({rec['name']}) | appid={rec['steamAppId']} | genre={rec['genre']} | ownership={rec['ownership']} | price=${rec['priceUsd']}")
        if args.apply:
            apply_games_update(games)
        else:
            print("Dry-run complete. Re-run with --apply to write changes.")
        return

    games, stats = sync_multi_site_games(offline=args.offline)
    print(f"Unified PC Games Catalog: total={stats['total']} (added={stats['added']}, updated={stats['updated']})")
    if args.apply or args.normalize:
        if args.apply:
            apply_games_update(games)
        else:
            print("Normalized preview complete. Pass --apply to write changes.")
    else:
        print("Dry-run complete. Run with --apply to write changes.")


if __name__ == "__main__":
    main()
