"""Multi-tier franchise builder, Obsidian importer, and metadata/poster enricher."""

from __future__ import annotations

import datetime
import json
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from media import CATALOG_JSON_PATH, load_catalog
from media.mappings import extract_entry_ids, resolve_cross_ids
from media.poster_cache import (
    POSTER_CACHE_DIR,
    download_poster_to_cache,
    extract_youtube_thumbnail,
    query_anilist_franchise,
    query_bangumi,
    query_imdb_suggestion,
    query_mangaupdates,
    query_tvmaze,
    query_wikipedia_summary,
)

OBSIDIAN_BATCH_2026_11_26 = {
    "the-fantasie-of-a-stepmother",
    "secret-class",
    "perfect-world",
    "martial-universe",
    "a-record-of-a-mortals-journey-to-immortality",
    "the-great-ruler",
    "battle-through-the-heavens",
    "soul-land",
    "against-the-gods",
    "the-girl-downstairs",
    "martial-peak",
}

_YEAR_RE = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")


def extract_year_from_text(*texts: str) -> int | None:
    """Return latest realistic 4-digit release year found in entry text, if any."""
    years = [int(y) for t in texts for y in _YEAR_RE.findall(str(t or ""))]
    return max(years) if years else None

_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")

OFFICIAL_HOSTS = (
    "wetv.vip",
    "iq.com",
    "iqiyi.com",
    "crunchyroll.com",
    "netflix.com",
    "viki.com",
    "primevideo.com",
    "hulu.com",
    "disneyplus.com",
    "hidive.com",
    "webtoons.com",
    "tapas.io",
    "toptoon.com",
    "webnovel.com",
    "wuxiaworld.com",
    "youku.tv",
    "bilibili.tv",
    "bilibili.com",
    "apple.com",
    "lezhinsnack.com",
    "ac.qq.com",
    "animenewsnetwork.com",
    "soompi.com",
    "wikipedia.org",
)

TRACKER_HOSTS = (
    "imdb.com",
    "novelupdates.com",
    "anilist.co",
    "mangaupdates.com",
    "mydramalist.com",
    "tvmaze.com",
)


def classify_link_kind(url: str, label: str = "") -> str:
    """Classify a link as official, tracker, or unofficial."""
    url_l = (url or "").lower()
    lbl_l = (label or "").lower()
    host = urllib.parse.urlparse(url_l).netloc.lower()
    if "fan" in lbl_l or "unofficial" in lbl_l or "motion recap" in lbl_l or "search_query=" in url_l:
        if any(h in host for h in ("youtube.com", "youtu.be")) and ("official" in lbl_l or "bilibili" in lbl_l or "yuewen" in lbl_l or "tencent" in lbl_l or "pv" in lbl_l or "trailer" in lbl_l):
            return "official"
        return "unofficial"
    if any(h in host for h in OFFICIAL_HOSTS):
        return "official"
    if "youtube.com" in host or "youtu.be" in host:
        return "official" if ("watch?v=" in url_l or "playlist?" in url_l) else "unofficial"
    if any(h in host for h in TRACKER_HOSTS):
        return "tracker"
    return "unofficial"


def extract_markdown_links(text: str) -> list[dict[str, str]]:
    """Extract unique labeled URLs from markdown text, excluding private cloud hosts."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for label, url in _MD_LINK_RE.findall(text or ""):
        clean_url = url.strip()
        if "mega.nz" in clean_url.lower() or clean_url in seen:
            continue
        seen.add(clean_url)
        clean_label = re.sub(r"\s+", " ", label).strip()
        out.append({"label": clean_label, "url": clean_url, "kind": classify_link_kind(clean_url, clean_label)})
    return out


def strip_markdown(text: str) -> str:
    """Convert markdown inline links/emphasis into clean plain text."""
    s = _MD_LINK_RE.sub(r"\1", text or "")
    s = re.sub(r"<br\s*/?>", " · ", s, flags=re.IGNORECASE)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = s.replace("•", " ").strip()
    return re.sub(r"\s+", " ", s).strip(" ·")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-") or "media-item"


def _detect_comic_sub_format(origin: str) -> str:
    ol = (origin or "").lower()
    if "manhua" in ol:
        return "Chinese Manhua"
    if "manhwa" in ol:
        return "Korean Manhwa"
    if "manga" in ol:
        return "Japanese Manga"
    if "webtoon" in ol:
        return "Webtoon"
    return "Comic"


def _has_text_source(origin: str) -> bool:
    ol = (origin or "").lower()
    return any(tok in ol for tok in ("novel", "web serial", "light novel", "web novel"))


def _unique_name(desired: str, used_names: set[str], fallback_suffix: str = "") -> str:
    candidate = desired.strip()
    if candidate.lower() not in used_names:
        used_names.add(candidate.lower())
        return candidate
    if fallback_suffix:
        cand2 = f"{candidate} [{fallback_suffix}]"
        if cand2.lower() not in used_names:
            used_names.add(cand2.lower())
            return cand2
    n = 2
    while f"{candidate} #{n}".lower() in used_names:
        n += 1
    final = f"{candidate} #{n}"
    used_names.add(final.lower())
    return final


def _unique_id(desired: str, used_ids: set[str]) -> str:
    cand = _slugify(desired)
    if cand not in used_ids:
        used_ids.add(cand)
        return cand
    n = 2
    while f"{cand}-{n}" in used_ids:
        n += 1
    final = f"{cand}-{n}"
    used_ids.add(final)
    return final


def _parse_obsidian_new_franchises(md_path: Path | None = None) -> list[dict[str, Any]]:
    """Build deduplicated multi-tier records for the 11 new franchises from the Obsidian catalog."""
    raw_defs: list[dict[str, Any]] = [
        {
            "franchise_id": "the-fantasie-of-a-stepmother",
            "title": "The Fantasie of a Stepmother",
            "alt": "A Stepmother's Märchen / Shuri von Neuschwanstein",
            "origin": "Korean Webtoon & Web Novel",
            "nsfw": False,
            "description": "Widowed noblewoman Shuri von Neuschwanstein regresses after her tragic death and navigates ruthless imperial politics while fiercely protecting her four stepchildren.",
            "novel": {
                "name": "The Fantasie of a Stepmother (Web Novel)",
                "sub_format": "Korean Web Novel",
                "link": "https://www.novelupdates.com/series/a-stepmothers-marchen/",
                "links": [{"label": "NovelUpdates (Tracker)", "url": "https://www.novelupdates.com/series/a-stepmothers-marchen/", "kind": "tracker"}],
            },
            "comic": {
                "id": "the-fantasie-of-a-stepmother",
                "name": "The Fantasie of a Stepmother",
                "sub_format": "Korean Webtoon / Manhwa",
                "link": "https://tapas.io/series/the-fantasie-of-a-stepmother/info",
                "links": [
                    {"label": "Tapas — Official Webtoon", "url": "https://tapas.io/series/the-fantasie-of-a-stepmother/info", "kind": "official"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=The%20Fantasie%20of%20a%20Stepmother&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [],
        },
        {
            "franchise_id": "secret-class",
            "title": "Secret Class",
            "alt": "Secret Class (18+ Explicit Korean Webtoon)",
            "origin": "Korean Manhwa / Webtoon (18+)",
            "nsfw": True,
            "description": "Explicit 18+ full-color Korean webtoon centered on adopted son Dae-ho living with his foster mother Mrs. Cha and stepsisters.",
            "novel": None,
            "comic": {
                "id": "secret-class",
                "name": "Secret Class",
                "sub_format": "Adult Korean Webtoon (18+)",
                "link": "https://global.toptoon.com/content/100559",
                "links": [
                    {"label": "TOPTOON Global — Official Webtoon", "url": "https://global.toptoon.com/content/100559", "kind": "official"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=Secret%20Class&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [],
        },
        {
            "franchise_id": "perfect-world",
            "title": "Perfect World",
            "alt": "Wanmei Shijie",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "Born with a legendary Supreme Bone stolen by his clan in childhood, Shi Hao grows up in a wilderness village guarded by Liu Shen (the Willow Deity) before tearing through ancient dynasties and primordial realms.",
            "novel": {
                "name": "Perfect World (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "link": "https://www.wuxiaworld.com/novel/perfect-world",
                "links": [
                    {"label": "Wuxiaworld — Official Novel", "url": "https://www.wuxiaworld.com/novel/perfect-world", "kind": "official"},
                    {"label": "WebNovel — Complete Novel (2,015 Chs)", "url": "https://www.webnovel.com/id/book/perfect-world_8094026805004405", "kind": "official"},
                ],
            },
            "comic": {
                "id": "perfect-world",
                "name": "Perfect World",
                "sub_format": "Chinese Manhua",
                "link": "https://comix.to/browse?q=Perfect%20World&sort=relevance%3Adesc",
                "links": [
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=Perfect%20World&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "perfect-world-donghua",
                    "name": "Perfect World (3D Donghua Series)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "link": "https://wetv.vip/en/album/oz5ppkfjx9niv57",
                    "description": "Ultra-high-resolution 3D donghua spanning 288+ episodes adapting Shi Hao's primordial cultivation saga.",
                    "links": [{"label": "WeTV — 3D Series (288+ EPs)", "url": "https://wetv.vip/en/album/oz5ppkfjx9niv57", "kind": "official"}],
                },
                {
                    "id": "perfect-world-ninefold-movie",
                    "name": "Perfect World: Ninefold The Burning Sky (2026 Movie)",
                    "media_type": "movie",
                    "sub_format": "3D Donghua Movie",
                    "link": "https://wetv.vip/album/buhm7cg0846qtxc",
                    "description": "2026 feature film centered on Liu Shen (Willow Deity) and the Burning Sky battle.",
                    "links": [{"label": "WeTV — 2026 Movie", "url": "https://wetv.vip/album/buhm7cg0846qtxc", "kind": "official"}],
                },
            ],
        },
        {
            "franchise_id": "martial-universe",
            "title": "Martial Universe",
            "alt": "Wu Dong Qian Kun",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "shared_universe": ["battle-through-the-heavens", "the-great-ruler"],
            "description": "Shared cosmos with BTTH & The Great Ruler. Branch-family outcast Lin Dong discovers an ancient stone talisman to avenge his crippled father while entangled with aloof sect elder Ling Qingzhu.",
            "novel": {
                "name": "Martial Universe (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "link": "https://www.wuxiaworld.com/novel/wu-dong-qian-kun",
                "links": [{"label": "Wuxiaworld — Complete Novel (1,317 Chs)", "url": "https://www.wuxiaworld.com/novel/wu-dong-qian-kun", "kind": "official"}],
            },
            "comic": {
                "id": "martial-universe",
                "name": "Martial Universe",
                "sub_format": "Chinese Manhua",
                "link": "https://comix.to/browse?q=Martial%20Universe&sort=relevance%3Adesc",
                "links": [{"label": "comix.to Search", "url": "https://comix.to/browse?q=Martial%20Universe&sort=relevance%3Adesc", "kind": "unofficial"}],
            },
            "motion": [
                {
                    "id": "martial-universe-donghua",
                    "name": "Martial Universe (3D Donghua S1–S7)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "link": "https://wetv.vip/en/album/7bdooic0j6sge7f",
                    "description": "Long-running 3D donghua adaptation spanning Season 1 through Season 5 and Season 7.",
                    "links": [
                        {"label": "WeTV — Season 1", "url": "https://wetv.vip/en/album/7bdooic0j6sge7f", "kind": "official"},
                        {"label": "WeTV — Season 5", "url": "https://wetv.vip/en/album/wmag858rxt7xuj8", "kind": "official"},
                    ],
                },
                {
                    "id": "martial-universe-live-action",
                    "name": "Martial Universe (Live-Action C-Drama)",
                    "media_type": "tv_series",
                    "sub_format": "Live-Action C-Drama",
                    "link": "https://www.youku.tv/v/v_show/id_XNTE3OTI3MzQxMg==.html",
                    "description": "Live-action Chinese television adaptation streaming on Youku.",
                    "links": [{"label": "Youku — Live-Action", "url": "https://www.youku.tv/v/v_show/id_XNTE3OTI3MzQxMg==.html", "kind": "official"}],
                },
            ],
        },
        {
            "franchise_id": "a-record-of-a-mortals-journey-to-immortality",
            "title": "A Record of a Mortal's Journey to Immortality",
            "alt": "RMJI · Fanren Xiu Xian Zhuan",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "Born a poor village boy with mediocre talent, Han Li survives murderous cultivation sects through extreme caution, resource management, and cold calculation.",
            "novel": {
                "name": "A Record of a Mortal's Journey to Immortality (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "link": "https://www.wuxiaworld.com/novel/rmji",
                "links": [
                    {"label": "Wuxiaworld — Complete Novel (2,455 Chs)", "url": "https://www.wuxiaworld.com/novel/rmji", "kind": "official"},
                    {"label": "Wuxiaworld — Immortal Realm Sequel", "url": "https://www.wuxiaworld.com/novel/rmjiir", "kind": "official"},
                ],
            },
            "comic": {
                "id": "a-record-of-a-mortals-journey-to-immortality",
                "name": "A Record of a Mortal's Journey to Immortality",
                "sub_format": "Chinese Manhua",
                "link": "https://comix.to/browse?q=Record%20of%20a%20Mortal%27s%20Journey%20to%20Immortality&sort=relevance%3Adesc",
                "links": [{"label": "comix.to Search", "url": "https://comix.to/browse?q=Record%20of%20a%20Mortal%27s%20Journey%20to%20Immortality&sort=relevance%3Adesc", "kind": "unofficial"}],
            },
            "motion": [
                {
                    "id": "rmji-3d-donghua",
                    "name": "A Record of a Mortal's Journey to Immortality (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "link": "https://www.youtube.com/watch?v=LXDouB-6zMM",
                    "description": "Photorealistic 3D donghua series & 3D remake produced by Bilibili featuring Nangong Wan and Han Li.",
                    "links": [
                        {"label": "YouTube — Made By Bilibili EP 1–100", "url": "https://www.youtube.com/watch?v=LXDouB-6zMM", "kind": "official"},
                        {"label": "YouTube — Bilibili 3D Remake EP 1–72", "url": "https://www.youtube.com/watch?v=M_57l_zi_q4", "kind": "official"},
                    ],
                },
                {
                    "id": "rmji-immortal-ascension-cdrama",
                    "name": "The Immortal Ascension (2025 Live-Action C-Drama)",
                    "media_type": "tv_series",
                    "sub_format": "Live-Action C-Drama",
                    "link": "https://www.youku.tv/v/v_show/id_XNjQ4NDc0NTk2OA==.html",
                    "description": "2025 Youku live-action adaptation of A Record of a Mortal's Journey to Immortality.",
                    "links": [{"label": "Youku — The Immortal Ascension", "url": "https://www.youku.tv/v/v_show/id_XNjQ4NDc0NTk2OA==.html", "kind": "official"}],
                },
            ],
        },
        {
            "franchise_id": "the-great-ruler",
            "title": "The Great Ruler",
            "alt": "Da Zhu Zai",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "shared_universe": ["battle-through-the-heavens", "martial-universe"],
            "description": "Shared crossover cosmos with BTTH and Martial Universe. Young prodigy Mu Chen fights among supreme sovereigns in the Great Thousand World while uncovering the legacy of his sovereign-clan mother Qing Yanjing.",
            "novel": {
                "name": "The Great Ruler (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "link": "https://www.wuxiaworld.com/novel/the-great-ruler/tgr-chapter-1",
                "links": [
                    {"label": "Wuxiaworld — Official Novel", "url": "https://www.wuxiaworld.com/novel/the-great-ruler/tgr-chapter-1", "kind": "official"},
                    {"label": "WebNovel — Official Novel (1,565 Chs)", "url": "https://m.webnovel.com/book/8094160805005105", "kind": "official"},
                ],
            },
            "comic": {
                "id": "the-great-ruler",
                "name": "The Great Ruler",
                "sub_format": "Chinese Manhua",
                "link": "https://comix.to/browse?q=The%20Great%20Ruler&sort=relevance%3Adesc",
                "links": [{"label": "comix.to Search", "url": "https://comix.to/browse?q=The%20Great%20Ruler&sort=relevance%3Adesc", "kind": "unofficial"}],
            },
            "motion": [
                {
                    "id": "the-great-ruler-donghua",
                    "name": "The Great Ruler (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "link": "https://www.iq.com/wiki/en_us/album/the-great-ruler-2023-123o36k0uo9",
                    "description": "4K 3D donghua adaptation streaming on iQIYI and YouTube.",
                    "links": [
                        {"label": "iQIYI — Official 3D Donghua", "url": "https://www.iq.com/wiki/en_us/album/the-great-ruler-2023-123o36k0uo9", "kind": "official"},
                        {"label": "YouTube — iQIYI EP 1–52", "url": "https://www.youtube.com/watch?v=WQsdviSE2A4", "kind": "official"},
                    ],
                },
                {
                    "id": "the-great-ruler-live-action",
                    "name": "The Great Ruler (Live-Action C-Drama)",
                    "media_type": "tv_series",
                    "sub_format": "Live-Action C-Drama",
                    "link": "https://www.youtube.com/watch?v=nUvoYNMwTi8",
                    "description": "iQIYI live-action fantasy drama adaptation of The Great Ruler.",
                    "links": [{"label": "YouTube — iQIYI Live-Action EP 1", "url": "https://www.youtube.com/watch?v=nUvoYNMwTi8", "kind": "official"}],
                },
            ],
        },
        {
            "franchise_id": "battle-through-the-heavens",
            "title": "Battle Through the Heavens",
            "alt": "Doupo Cangqiong · Fights Break Sphere",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "shared_universe": ["martial-universe", "the-great-ruler"],
            "description": "Prodigy Xiao Yan mysteriously loses his powers until he discovers a grandmaster's spirit inside his mother's ring, sparking alchemy politics, sect wars, and romances with Yun Yun, Ya Fei, and Queen Medusa.",
            "novel": {
                "name": "Battle Through the Heavens (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "link": "https://m.webnovel.com/book/battle-through-the-heavens_8093990805004205",
                "links": [{"label": "WebNovel — Official Novel (1,646 Chs)", "url": "https://m.webnovel.com/book/battle-through-the-heavens_8093990805004205", "kind": "official"}],
            },
            "comic": {
                "id": "battle-through-the-heavens",
                "name": "Battle Through the Heavens",
                "sub_format": "Chinese Manhua",
                "link": "https://comix.to/browse?q=Battle%20Through%20the%20Heavens&sort=relevance%3Adesc",
                "links": [{"label": "comix.to Search", "url": "https://comix.to/browse?q=Battle%20Through%20the%20Heavens&sort=relevance%3Adesc", "kind": "unofficial"}],
            },
            "motion": [
                {
                    "id": "btth-3d-donghua",
                    "name": "Battle Through the Heavens (3D Donghua S1–S5)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "link": "https://wetv.vip/en/album/fc0jm32uyhpfqae",
                    "description": "Flagship 3D donghua spanning Season 1 through the 219-episode Nian Fan run.",
                    "links": [
                        {"label": "WeTV — Season 1", "url": "https://wetv.vip/en/album/7tvogbkk02zrjtf", "kind": "official"},
                        {"label": "WeTV — Season 5 (219 EPs)", "url": "https://wetv.vip/en/album/fc0jm32uyhpfqae", "kind": "official"},
                        {"label": "YouTube — Yuewen ENG SUB", "url": "https://www.youtube.com/playlist?list=PLJ573C5aBJTI", "kind": "official"},
                        {"label": "YouTube — 4K Remaster", "url": "https://www.youtube.com/watch?v=eTHWQYWZgZQ", "kind": "official"},
                    ],
                },
                {
                    "id": "btth-battle-of-two-emperors-movie",
                    "name": "Battle Through the Heavens: Battle of the Two Emperors",
                    "media_type": "movie",
                    "sub_format": "3D Donghua Finale Movie",
                    "link": "https://wetv.vip/album/8rawc5epwdtac2u",
                    "description": "Theatrical 3D donghua finale event surpassing 5.6M pre-reservations in November 2026.",
                    "links": [{"label": "WeTV — Finale Movie", "url": "https://wetv.vip/album/8rawc5epwdtac2u", "kind": "official"}],
                },
                {
                    "id": "fights-break-sphere-cdrama",
                    "name": "Fights Break Sphere (Live-Action C-Drama S1–S2)",
                    "media_type": "tv_series",
                    "sub_format": "Live-Action C-Drama",
                    "link": "https://www.viki.com/tv/35887c-fights-break-sphere",
                    "description": "Live-action television adaptation across Season 1 (Viki) and Season 2 (Prime Video).",
                    "links": [
                        {"label": "Viki — Live-Action S1", "url": "https://www.viki.com/tv/35887c-fights-break-sphere", "kind": "official"},
                        {"label": "Prime Video — Live-Action S2", "url": "https://www.primevideo.com/detail/0H2E0AW4NB59FH1ZQF49Z79QQR", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "soul-land",
            "title": "Soul Land",
            "alt": "Douluo Dalu",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "Hidden-weapons prodigy Tang San reincarnates into a world of Martial Souls and Spirit Rings, rising through academy tournaments into a continental war against Spirit Hall ruled by Supreme Pontiff Bibi Dong.",
            "novel": {
                "name": "Soul Land (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "link": "https://m.webnovel.com/search?keyword=soul+land",
                "links": [{"label": "WebNovel — Official Novels Catalog", "url": "https://m.webnovel.com/search?keyword=soul+land", "kind": "official"}],
            },
            "comic": {
                "id": "soul-land",
                "name": "Soul Land",
                "sub_format": "Chinese Manhua",
                "link": "https://comix.to/browse?q=Soul%20Land&sort=relevance%3Adesc",
                "links": [
                    {"label": "WebNovel — Official Manhua Catalog", "url": "https://m.webnovel.com/search?keyword=soul+land", "kind": "official"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=Soul%20Land&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "soul-land-donghua",
                    "name": "Soul Land (Complete 3D Donghua — 266 EPs)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "link": "https://wetv.vip/en/album/wzx7pbebgpxlqqr",
                    "description": "Complete 266-episode 3D donghua adaptation on WeTV and Tencent Animation YouTube.",
                    "links": [
                        {"label": "WeTV — Complete 266 EPs", "url": "https://wetv.vip/en/album/wzx7pbebgpxlqqr", "kind": "official"},
                        {"label": "YouTube — Tencent Animation", "url": "https://youtube.com/playlist?list=PLxOs22nkVmnJI1_URegvYQM8tOUg-iaug", "kind": "official"},
                        {"label": "YouTube — EP 131–264 Full", "url": "https://www.youtube.com/watch?v=b3YvbSpTnVw", "kind": "official"},
                    ],
                },
                {
                    "id": "douluo-continent-cdrama",
                    "name": "Douluo Continent (Live-Action C-Drama)",
                    "media_type": "tv_series",
                    "sub_format": "Live-Action C-Drama",
                    "link": "https://www.viki.com/tv/36952c-douluo-continent",
                    "description": "Live-action drama adaptation starring Xiao Zhan as Tang San.",
                    "links": [{"label": "Viki — Douluo Continent", "url": "https://www.viki.com/tv/36952c-douluo-continent", "kind": "official"}],
                },
            ],
        },
        {
            "franchise_id": "against-the-gods",
            "title": "Against the Gods",
            "alt": "Ni Tian Xie Shen",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "Poisoned and betrayed on his wedding night, Yun Che awakens with the Sky Poison Pearl and ancient medical legacy, cutting a ruthless path across noble clans and icy sect elders.",
            "novel": {
                "name": "Against the Gods (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "link": "https://www.wuxiaworld.com/novel/against-the-gods",
                "links": [
                    {"label": "Wuxiaworld — Official English Webnovel", "url": "https://www.wuxiaworld.com/novel/against-the-gods", "kind": "official"},
                    {"label": "Tapas — Official Novel", "url": "https://tapas.io/series/Against-the-Gods/info", "kind": "official"},
                ],
            },
            "comic": {
                "id": "against-the-gods",
                "name": "Against the Gods",
                "sub_format": "Chinese Manhua",
                "link": "https://comix.to/browse?q=Against%20the%20Gods&sort=relevance%3Adesc",
                "links": [{"label": "comix.to Search", "url": "https://comix.to/browse?q=Against%20the%20Gods&sort=relevance%3Adesc", "kind": "unofficial"}],
            },
            "motion": [
                {
                    "id": "against-the-gods-donghua",
                    "name": "Against the Gods (3D Donghua S1–S2)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "link": "https://www.iq.com/play/exclusive-against-the-gods-%E2%85%B1-2023-20yoqe7hzcx",
                    "description": "3D donghua adaptation on iQIYI including Season 1 and Season 2 (launched April 2026).",
                    "links": [
                        {"label": "iQIYI — Season 1", "url": "https://www.iq.com/wiki/en_us/album/against-the-gods-2019-19rrhsgdfl", "kind": "official"},
                        {"label": "iQIYI — Season 2", "url": "https://www.iq.com/play/exclusive-against-the-gods-%E2%85%B1-2023-20yoqe7hzcx", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "the-girl-downstairs",
            "title": "The Girl Downstairs",
            "alt": "Aishang Ta De Liyou · Doona!",
            "origin": "Korean Manhwa / Webtoon",
            "nsfw": False,
            "description": "Ordinary college freshman Yuan Jun moves into a share-house and discovers former pop idol Li Shiya (Lee Duna) living downstairs—sparking a grounded, slow-burn romance.",
            "novel": None,
            "comic": {
                "id": "the-girl-downstairs",
                "name": "The Girl Downstairs",
                "sub_format": "Korean Manhwa / Webtoon",
                "link": "https://www.webtoons.com/en/romance/the-girl-downstairs/list?title_no=1809",
                "links": [
                    {"label": "WEBTOON — Original Manhwa", "url": "https://www.webtoons.com/en/romance/the-girl-downstairs/list?title_no=1809", "kind": "official"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=The%20Girl%20Downstairs&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "the-girl-downstairs-2d-donghua",
                    "name": "The Girl Downstairs (2D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "2D Donghua",
                    "link": "https://www.youtube.com/playlist?list=PLBakWosU0sfhwdV_CleP1Uqk8lienfjRO",
                    "description": "Soft-lit 2D donghua adaptation produced by Bilibili.",
                    "links": [{"label": "YouTube — Made By Bilibili 2D Donghua", "url": "https://www.youtube.com/playlist?list=PLBakWosU0sfhwdV_CleP1Uqk8lienfjRO", "kind": "official"}],
                },
                {
                    "id": "doona-netflix-kdrama",
                    "name": "Doona! (Netflix Live-Action K-Drama)",
                    "media_type": "tv_series",
                    "sub_format": "Live-Action K-Drama",
                    "link": "https://www.netflix.com/in/title/81595046",
                    "description": "Netflix Korean drama starring Bae Suzy and Yang Se-jong.",
                    "links": [{"label": "Netflix — Doona!", "url": "https://www.netflix.com/in/title/81595046", "kind": "official"}],
                },
            ],
        },
        {
            "franchise_id": "martial-peak",
            "title": "Martial Peak",
            "alt": "Wu Lian Dianfeng",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "Lowly floor-sweeping trial disciple Yang Kai discovers a mysterious Wordless Black Book that lets him shatter cultivation bottlenecks across star-fields alongside Shan Qing Luo, Bing Yun, and Su Yan.",
            "novel": {
                "name": "Martial Peak (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "link": "https://m.webnovel.com/search?keywords=martial+peak",
                "links": [{"label": "WebNovel — Official Novel Catalog", "url": "https://m.webnovel.com/search?keywords=martial+peak", "kind": "official"}],
            },
            "comic": {
                "id": "martial-peak",
                "name": "Martial Peak",
                "sub_format": "Chinese Manhua",
                "link": "https://m.webnovel.com/comic/martial-peak_14866013705882901",
                "links": [
                    {"label": "WebNovel — Official Manhua (1,640+ Chs)", "url": "https://m.webnovel.com/comic/martial-peak_14866013705882901", "kind": "official"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=Martial%20Peak&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "martial-peak-3d-donghua",
                    "name": "Martial Peak (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "link": "https://www.youtube.com/watch?v=zUsjwwdsP88",
                    "description": "Yuewen / Tencent Video 3D donghua adaptation (EP 1–48+).",
                    "links": [{"label": "YouTube — Yuewen 3D Donghua EP 1–48", "url": "https://www.youtube.com/watch?v=zUsjwwdsP88", "kind": "official"}],
                },
            ],
        },
    ]
    return raw_defs


def _parse_donghua_curated_franchises() -> list[dict[str, Any]]:
    """Build multi-tier records for the curated Donghua & adaptation batch."""
    return [
        {
            "franchise_id": "ling-cage",
            "title": "Ling Cage",
            "alt": "Ling Long: Incarnation · 灵笼",
            "origin": "Original Donghua",
            "nsfw": False,
            "description": "Industrial-grade 3D post-apocalyptic sci-fi/cyberpunk donghua by YHKT Entertainment. Season 2 broke 100M views (8.9 Douban), consulting real scientists to ground its dystopian ecosystem around Mark and Bai Yuekui.",
            "novel": None,
            "comic": None,
            "motion": [
                {
                    "id": "ling-cage-3d-donghua",
                    "name": "Ling Cage (3D Donghua S1–S2)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2019,
                    "link": "https://anilist.co/anime/110459",
                    "description": "Industrial-grade 3D sci-fi/cyberpunk action and intensely raw, emotional voice acting. Season 2 broke 100M views (8.9 Douban), blending brutal survival stakes, tragic character deaths, and deep philosophy around Mark and Bai Yuekui.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/110459", "kind": "tracker"},
                        {"label": "IMDb", "url": "https://www.imdb.com/title/tt10827146/", "kind": "tracker"},
                        {"label": "Bilibili Search", "url": "https://www.bilibili.tv/en/search-result?q=Ling%20Cage", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "lord-of-mysteries",
            "title": "Lord of Mysteries",
            "alt": "Guimi Zhi Zhu · Lord of the Mysteries · 诡秘之主",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "Victorian Lovecraftian steampunk mystery following Klein Moretti through secret-society Tarot Club politics, Beyonder pathways, and cosmic horror.",
            "novel": {
                "name": "Lord of Mysteries (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2018,
                "link": "https://www.webnovel.com/book/lord-of-mysteries_11022733006234505",
                "links": [
                    {"label": "WebNovel — Official Novel", "url": "https://www.webnovel.com/book/lord-of-mysteries_11022733006234505", "kind": "official"},
                ],
            },
            "comic": {
                "id": "lord-of-mysteries",
                "name": "Lord of Mysteries",
                "sub_format": "Chinese Manhua",
                "release_year": 2025,
                "link": "https://anilist.co/manga/188249",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/188249", "kind": "tracker"},
                    {"label": "MangaUpdates", "url": "https://www.mangaupdates.com/series/uarp82h/lord-of-the-mysteries", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=Lord%20of%20Mysteries&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "lord-of-mysteries-donghua",
                    "name": "Lord of Mysteries (2D/3D Hybrid Donghua)",
                    "media_type": "donghua",
                    "sub_format": "2D/3D Hybrid Donghua",
                    "release_year": 2025,
                    "link": "https://anilist.co/anime/137667",
                    "description": "B.CMAY Pictures' 2025 breakout hit (8.77 MAL) with Ufotable-tier visuals and atmospheric VA work. Delivers dense Victorian mystery, Tarot Club politics, cosmic horror, and heavy emotional stakes, with Season 2 expanding runtime.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/137667", "kind": "tracker"},
                        {"label": "IMDb", "url": "https://www.imdb.com/title/tt28618556/", "kind": "tracker"},
                        {"label": "WeTV Search", "url": "https://wetv.vip/en/search?q=Lord%20of%20Mysteries", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "painting-rivers-and-lakes",
            "title": "Painting Rivers and Lakes",
            "alt": "Hua Jianghu: Buliang Ren · Bu Liang Ren · 画江湖之不良人",
            "origin": "Original Donghua",
            "nsfw": False,
            "description": "Ruthless Tang-collapse historical wuxia political thriller spanning Seasons 1–7 with sharp faction schemes and Empress Nv Di.",
            "novel": None,
            "comic": None,
            "motion": [
                {
                    "id": "painting-rivers-and-lakes-donghua",
                    "name": "Painting Rivers and Lakes: Bu Liang Ren (3D Donghua S1–S7)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2014,
                    "link": "https://anilist.co/anime/102561",
                    "description": "S4–S7 feature gorgeous wuxia 3D and razor-sharp theatrical VAs (S1–S3 CGI is dated). Season 6 sits near the very top of Douban's all-time chart as a Tang-collapse political thriller with unmatched dialogue and Empress Nv Di.",
                    "links": [
                        {"label": "AniList (S1)", "url": "https://anilist.co/anime/102561", "kind": "tracker"},
                        {"label": "AniList (S7)", "url": "https://anilist.co/anime/168133", "kind": "tracker"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "sword-of-coming",
            "title": "Sword of Coming",
            "alt": "Jian Lai · 剑来",
            "origin": "Chinese Web Novel",
            "nsfw": False,
            "description": "Deeply philosophical literary xianxia following Chen Ping'an from an impoverished small town through earned morality and human dignity.",
            "novel": {
                "name": "Sword of Coming (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2017,
                "link": "https://www.novelupdates.com/?s=Sword%20of%20Coming",
                "links": [
                    {"label": "NovelUpdates (Search)", "url": "https://www.novelupdates.com/?s=Sword%20of%20Coming", "kind": "tracker"},
                ],
            },
            "comic": None,
            "motion": [
                {
                    "id": "sword-of-coming-3d-donghua",
                    "name": "Sword of Coming (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2024,
                    "link": "https://anilist.co/anime/137672",
                    "description": "Painterly, ink-wash-inspired 3D art direction paired with deeply poetic, grounded voice performances (8.9 Douban). A rare slow-burn character study about poverty, earned morality, and human dignity.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/137672", "kind": "tracker"},
                        {"label": "WeTV Search", "url": "https://wetv.vip/en/search?q=Sword%20of%20Coming", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "tales-of-herding-gods",
            "title": "Tales of Herding Gods",
            "alt": "Mu Shen Ji · 牧神记",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "Raised in the cursed Great Ruins by nine eccentric, crippled grandmasters, Qin Mu ventures into a mythic world of fallen gods and imperial reform.",
            "novel": {
                "name": "Tales of Herding Gods (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2017,
                "link": "https://www.mangaupdates.com/series/64pbbwg/tales-of-herding-gods-novel",
                "links": [
                    {"label": "MangaUpdates (Novel)", "url": "https://www.mangaupdates.com/series/64pbbwg/tales-of-herding-gods-novel", "kind": "tracker"},
                ],
            },
            "comic": {
                "id": "tales-of-herding-gods",
                "name": "Tales of Herding Gods",
                "sub_format": "Chinese Manhua",
                "release_year": 2019,
                "link": "https://anilist.co/manga/133520",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/133520", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=Tales%20of%20Herding%20Gods&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "tales-of-herding-gods-3d-donghua",
                    "name": "Tales of Herding Gods (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2024,
                    "link": "https://anilist.co/anime/185721",
                    "description": "Sparkly Key's jaw-dropping mythic xuanhuan 3D showcase (8.9 Douban) with expressive facial animation and lively VAs. Protagonist Qin Mu is clever, cheeky, and proactive in a world of fallen gods.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/185721", "kind": "tracker"},
                        {"label": "Bilibili Search", "url": "https://www.bilibili.tv/en/search-result?q=Tales%20of%20Herding%20Gods", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "renegade-immortal",
            "title": "Renegade Immortal",
            "alt": "Xian Ni · 仙逆",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "Er Gen's dark xianxia classic charting Wang Lin's brutal transformation from naive village youth to ruthless, trauma-forged avenger.",
            "novel": {
                "name": "Renegade Immortal (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2009,
                "link": "https://www.wuxiaworld.com/novel/renegade-immortal",
                "links": [
                    {"label": "Wuxiaworld — Official Novel", "url": "https://www.wuxiaworld.com/novel/renegade-immortal", "kind": "official"},
                ],
            },
            "comic": {
                "id": "renegade-immortal",
                "name": "Renegade Immortal",
                "sub_format": "Chinese Manhua",
                "release_year": 2014,
                "link": "https://anilist.co/manga/85986",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/85986", "kind": "tracker"},
                    {"label": "MangaUpdates", "url": "https://www.mangaupdates.com/series/6rcmyj2/xian-ni", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=Renegade%20Immortal&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "renegade-immortal-3d-donghua",
                    "name": "Renegade Immortal (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2023,
                    "link": "https://anilist.co/anime/137653",
                    "description": "Crisp, dark-toned 3D choreography and ferocious, emotionally heavy voice acting (8.9 Douban). Wang Lin is one of cultivation's best trauma-forged, ruthless protagonists, paced faster than RMJI.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/137653", "kind": "tracker"},
                        {"label": "WeTV Search", "url": "https://wetv.vip/en/search?q=Renegade%20Immortal", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "swallowed-star",
            "title": "Swallowed Star",
            "alt": "Tunshi Xingkong · 吞噬星空",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "A virus mutates Earth's wildlife into giant monsters, forcing humanity behind walled cities as Luo Feng rises from poor teenager to elite Warrior, wealthy tycoon, and galactic conqueror.",
            "novel": {
                "name": "Swallowed Star (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2010,
                "link": "https://www.novelupdates.com/?s=Swallowed%20Star",
                "links": [
                    {"label": "NovelUpdates (Search)", "url": "https://www.novelupdates.com/?s=Swallowed%20Star", "kind": "tracker"},
                ],
            },
            "comic": {
                "id": "swallowed-star",
                "name": "Swallowed Star",
                "sub_format": "Chinese Manhua",
                "release_year": 2020,
                "link": "https://anilist.co/manga/130624",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/130624", "kind": "tracker"},
                    {"label": "MangaUpdates", "url": "https://www.mangaupdates.com/series/28cc0o7/swallowed-star", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=Swallowed%20Star&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "swallowed-star-3d-donghua",
                    "name": "Swallowed Star (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2020,
                    "link": "https://anilist.co/anime/117012",
                    "description": "Sparkly Key's slick futuristic 3D sci-fi cultivation flagship and crisp voice cast. Starts as tight post-apocalyptic monster-hunting survival drama before scaling cleanly into galactic empire politics around Luo Feng.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/117012", "kind": "tracker"},
                        {"label": "IMDb", "url": "https://www.imdb.com/title/tt17050076/", "kind": "tracker"},
                        {"label": "WeTV Search", "url": "https://wetv.vip/en/search?q=Swallowed%20Star", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "to-be-hero-x",
            "title": "To Be Hero X",
            "alt": "Tu Bian Yingxiong X · 凸变英雄X",
            "origin": "Original Donghua",
            "nsfw": False,
            "description": "One of 2025's biggest visual showstoppers (8.52 MAL), seamlessly blending stylized 2D and 3D in a superhero thriller where public trust value grants and warps superpowers.",
            "novel": None,
            "comic": None,
            "motion": [
                {
                    "id": "to-be-hero-x-donghua",
                    "name": "To Be Hero X (2D/3D Hybrid Donghua)",
                    "media_type": "donghua",
                    "sub_format": "2D/3D Hybrid Donghua",
                    "release_year": 2025,
                    "link": "https://anilist.co/anime/156092",
                    "description": "2025 visual showstopper (8.52 MAL) blending stylized 2D and 3D. Brilliant superhero thriller premise where public 'trust value' grants and warps superpowers across an anthology cast.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/156092", "kind": "tracker"},
                        {"label": "Bangumi", "url": "https://bgm.tv/subject/405212", "kind": "tracker"},
                        {"label": "IMDb", "url": "https://www.imdb.com/title/tt23139038/", "kind": "tracker"},
                        {"label": "Crunchyroll Search", "url": "https://www.crunchyroll.com/search?q=To%20Be%20Hero%20X", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "fog-hill-of-five-elements",
            "title": "Fog Hill of Five Elements",
            "alt": "Wu Shan Wu Xing · 雾山五行",
            "origin": "Original Donghua",
            "nsfw": False,
            "description": "Arguably the peak of modern hand-drawn ink-wash martial arts (9.2 Douban for S2) with raw VA energy and untouchable fight choreography.",
            "novel": None,
            "comic": None,
            "motion": [
                {
                    "id": "fog-hill-of-five-elements-donghua",
                    "name": "Fog Hill of Five Elements (2D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "2D Donghua",
                    "release_year": 2020,
                    "link": "https://anilist.co/anime/127099",
                    "description": "Peak modern hand-drawn ink-wash martial arts (9.2 Douban for S2) with raw VA energy and untouchable fight choreography, held back from S-Tier only by its short episode count.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/127099", "kind": "tracker"},
                        {"label": "Bilibili Search", "url": "https://www.bilibili.tv/en/search-result?q=Fog%20Hill%20of%20Five%20Elements", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "blades-of-the-guardians",
            "title": "Blades of the Guardians",
            "alt": "Biaoren · Biao Ren · 镖人",
            "origin": "Chinese Manhua",
            "nsfw": False,
            "description": "Gritty late Sui Dynasty desert escort politics and cynical anti-heroes led by Dao Ma, often compared to Blade of the Immortal.",
            "novel": None,
            "comic": {
                "id": "blades-of-the-guardians",
                "name": "Blades of the Guardians",
                "sub_format": "Chinese Manhua",
                "release_year": 2016,
                "link": "https://anilist.co/manga/102796",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/102796", "kind": "tracker"},
                    {"label": "MangaUpdates", "url": "https://www.mangaupdates.com/series/mmhi4t2/blades-of-the-guardians", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=Blades%20of%20the%20Guardians&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "blades-of-the-guardians-2d-donghua",
                    "name": "Blades of the Guardians (2D Donghua S1–S2)",
                    "media_type": "donghua",
                    "sub_format": "2D Donghua",
                    "release_year": 2023,
                    "link": "https://anilist.co/anime/122508",
                    "description": "Raw, cinematic, blood-soaked 2D swordplay and gruff, mature voice acting (8.4 Douban). Captures brutal late Sui Dynasty desert politics and cynical anti-heroes.",
                    "links": [
                        {"label": "AniList (S1)", "url": "https://anilist.co/anime/122508", "kind": "tracker"},
                        {"label": "AniList (S2)", "url": "https://anilist.co/anime/168179", "kind": "tracker"},
                        {"label": "IMDb", "url": "https://www.imdb.com/title/tt28259824/", "kind": "tracker"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "scissor-seven",
            "title": "Scissor Seven",
            "alt": "Wu Liuqi · Killer Seven · 伍六七",
            "origin": "Original Donghua",
            "nsfw": False,
            "description": "Fluid, hyper-expressive 2D action-comedy disguising a deeply emotional assassin conspiracy and richly realized cast.",
            "novel": None,
            "comic": None,
            "motion": [
                {
                    "id": "scissor-seven-2d-donghua",
                    "name": "Scissor Seven (2D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "2D Donghua",
                    "release_year": 2018,
                    "link": "https://anilist.co/anime/107912",
                    "description": "Fluid, hyper-expressive 2D action with iconic comedic-to-dramatic voice acting. Disguises itself as absurd slapstick comedy before steadily peeling back an emotional assassin conspiracy.",
                    "links": [
                        {"label": "Netflix", "url": "https://www.netflix.com/title/81156880", "kind": "official"},
                        {"label": "AniList", "url": "https://anilist.co/anime/107912", "kind": "tracker"},
                        {"label": "IMDb", "url": "https://www.imdb.com/title/tt10384610/", "kind": "tracker"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "beyond-times-gaze",
            "title": "Beyond Time's Gaze",
            "alt": "Guangyin Zhi Wai · Beyond the Timescape · 光阴之外",
            "origin": "Chinese Web Novel",
            "nsfw": False,
            "description": "Adapted from Er Gen's hit novel: a broken god's gaze pollutes the world into a deadly wasteland where Xu Qing ruthlessly hunts and evolves to survive.",
            "novel": {
                "name": "Beyond Time's Gaze (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2022,
                "link": "https://www.wuxiaworld.com/novel/beyond-the-timescape",
                "links": [
                    {"label": "Wuxiaworld — Official Novel", "url": "https://www.wuxiaworld.com/novel/beyond-the-timescape", "kind": "official"},
                ],
            },
            "comic": None,
            "motion": [
                {
                    "id": "beyond-times-gaze-3d-donghua",
                    "name": "Beyond Time's Gaze (3D Donghua S1–S2)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2025,
                    "link": "https://anilist.co/anime/205905",
                    "description": "Youku Animation post-apocalyptic dark power fantasy (S1 Dec 2025, S2 ongoing 2026; 25-min eps). Elite 2026 visuals and gritty voice acting following Xu Qing's ruthless survival and evolution.",
                    "links": [
                        {"label": "AniList (S1)", "url": "https://anilist.co/anime/205905", "kind": "tracker"},
                        {"label": "AniList (S2)", "url": "https://anilist.co/anime/213356", "kind": "tracker"},
                        {"label": "Youku", "url": "https://www.youku.tv/", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "the-richest-man-in-game",
            "title": "The Richest Man in GAME",
            "alt": "Losing Money to Be a Tycoon · Kui Cheng Shoufu Cong Youxi Kaishi · 亏成首富从游戏开始",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "Office worker Pei Qian gets a Wealth Conversion System where company losses go into his personal pocket—so he tries to make terrible video games and overpay staff, only for every project to become a mega-hit.",
            "novel": {
                "name": "Losing Money to Be a Tycoon (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2019,
                "link": "https://www.novelupdates.com/?s=Losing%20Money%20to%20Be%20a%20Tycoon",
                "links": [
                    {"label": "NovelUpdates (Search)", "url": "https://www.novelupdates.com/?s=Losing%20Money%20to%20Be%20a%20Tycoon", "kind": "tracker"},
                ],
            },
            "comic": {
                "id": "the-richest-man-in-game",
                "name": "Losing Money to Be a Tycoon",
                "sub_format": "Chinese Manhua",
                "release_year": 2022,
                "link": "https://anilist.co/manga/154769",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/154769", "kind": "tracker"},
                    {"label": "MangaUpdates", "url": "https://www.mangaupdates.com/series/cqiosyg/losing-money-to-be-a-tycoon", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=Losing%20Money%20to%20Be%20a%20Tycoon&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "the-richest-man-in-game-donghua",
                    "name": "The Richest Man in GAME (2D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "2D Donghua",
                    "release_year": 2024,
                    "link": "https://anilist.co/anime/156112",
                    "description": "2D Foch Film / Bilibili rich-system business comedy (16 eps, 9.2 Bilibili score; 2025 Japanese dub). Pei Qian's desperate attempts to lose money accidentally turn him into a worshipped billionaire genius.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/156112", "kind": "tracker"},
                        {"label": "Bilibili Search", "url": "https://www.bilibili.tv/en/search-result?q=The%20Richest%20Man%20in%20GAME", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "my-senior-brother-is-too-steady",
            "title": "My Senior Brother Is Too Steady",
            "alt": "Big Brother · Wo Shixiong Shizai Tai Wenjian Le · 师兄啊师兄",
            "origin": "Chinese Web Novel",
            "nsfw": False,
            "description": "A modern guy transmigrates into ancient mythology before a divine war, hiding 99% of his OP power while hoarding poison pills and escape clones from the shadows.",
            "novel": {
                "name": "My Senior Brother Is Too Steady (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2019,
                "link": "https://www.mangaupdates.com/series/2jvjtfi/my-senior-brother-is-too-steady-novel",
                "links": [
                    {"label": "MangaUpdates (Novel)", "url": "https://www.mangaupdates.com/series/2jvjtfi/my-senior-brother-is-too-steady-novel", "kind": "tracker"},
                ],
            },
            "comic": None,
            "motion": [
                {
                    "id": "my-senior-brother-is-too-steady-donghua",
                    "name": "My Senior Brother Is Too Steady / Big Brother (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2023,
                    "link": "https://anilist.co/anime/129238",
                    "description": "Youku high-end 3D transmigration/OP schemer comedy with top-notch comedic VA. Li Changshou hides 99% of his power, hoards poison pills and escape clones, and accidentally draws beauties and enemies alike.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/129238", "kind": "tracker"},
                        {"label": "IMDb", "url": "https://www.imdb.com/title/tt27834263/", "kind": "tracker"},
                        {"label": "Youku", "url": "https://www.youku.tv/", "kind": "official"},
                    ],
                },
                {
                    "id": "my-senior-brother-is-too-steady-cdrama",
                    "name": "Pull Strings / My Senior Brother Is Too Steady (2026 Live-Action C-Drama)",
                    "media_type": "tv_series",
                    "sub_format": "Live-Action C-Drama",
                    "release_year": 2026,
                    "link": "https://www.youku.tv/",
                    "description": "2026 Youku & iQIYI 30-episode live-action xianxia comedy adaptation starring Ao Ruipeng as Li Changshou.",
                    "links": [
                        {"label": "Youku", "url": "https://www.youku.tv/", "kind": "official"},
                        {"label": "iQIYI", "url": "https://www.iq.com/", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "the-daily-life-of-the-immortal-king",
            "title": "The Daily Life of the Immortal King",
            "alt": "Xian Wang de Richang Shenghuo · 仙王的日常生活",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "Modern high schooler Wang Ling is casually strong enough to shatter planets and just wants to eat crispy noodles quietly while obliterating annoying demons and rival sects.",
            "novel": {
                "name": "The Daily Life of the Immortal King (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2017,
                "link": "https://www.novelupdates.com/?s=The%20Daily%20Life%20of%20the%20Immortal%20King",
                "links": [
                    {"label": "NovelUpdates (Search)", "url": "https://www.novelupdates.com/?s=The%20Daily%20Life%20of%20the%20Immortal%20King", "kind": "tracker"},
                ],
            },
            "comic": {
                "id": "the-daily-life-of-the-immortal-king",
                "name": "The Daily Life of the Immortal King",
                "sub_format": "Chinese Manhua",
                "release_year": 2020,
                "link": "https://anilist.co/manga/141151",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/141151", "kind": "tracker"},
                    {"label": "MangaUpdates", "url": "https://www.mangaupdates.com/series/q7acqb8/the-daily-life-of-immortal-king", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=The%20Daily%20Life%20of%20the%20Immortal%20King&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "the-daily-life-of-the-immortal-king-donghua",
                    "name": "The Daily Life of the Immortal King (2D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "2D Donghua",
                    "release_year": 2020,
                    "link": "https://anilist.co/anime/114121",
                    "description": "Haoliners / Bilibili multi-season urban OP MC power fantasy with snappy 2D action and deadpan VA around Wang Ling's quest for crispy noodles and peace.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/114121", "kind": "tracker"},
                        {"label": "Crunchyroll Search", "url": "https://www.crunchyroll.com/search?q=The%20Daily%20Life%20of%20the%20Immortal%20King", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "how-dare-you",
            "title": "How Dare You?!",
            "alt": "Cheng He Titong · I Woke Up in the Wrong Story · 成何体统",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "An office worker transmigrates into a palace-intrigue novel as the doomed villainess—only to discover the ruthless 'tyrant emperor' is also a modern transmigrator when she tests him with English.",
            "novel": {
                "name": "How Dare You?! (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2021,
                "link": "https://www.novelupdates.com/?s=How%20Dare%20You",
                "links": [
                    {"label": "NovelUpdates (Search)", "url": "https://www.novelupdates.com/?s=How%20Dare%20You", "kind": "tracker"},
                ],
            },
            "comic": {
                "id": "how-dare-you",
                "name": "How Dare You?! (I Woke Up in the Wrong Story)",
                "sub_format": "Chinese Manhua",
                "release_year": 2025,
                "link": "https://anilist.co/manga/194938",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/194938", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=How%20Dare%20You&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "how-dare-you-donghua",
                    "name": "How Dare You?! (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2024,
                    "link": "https://anilist.co/anime/135511",
                    "description": "iQIYI expressive 3D palace-scheming transmigration comedy with hilarious VA as two modern office workers team up to rewrite the original tragic novel plot.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/135511", "kind": "tracker"},
                        {"label": "iQIYI", "url": "https://www.iq.com/", "kind": "official"},
                    ],
                },
                {
                    "id": "how-dare-you-cdrama",
                    "name": "How Dare You?! (2026 Live-Action C-Drama)",
                    "media_type": "tv_series",
                    "sub_format": "Live-Action C-Drama",
                    "release_year": 2026,
                    "link": "https://www.imdb.com/title/tt35231547/",
                    "description": "February 2026 iQIYI live-action palace comedy drama adaptation starring Wang Churan and Cheng Lei.",
                    "links": [
                        {"label": "IMDb", "url": "https://www.imdb.com/title/tt35231547/", "kind": "tracker"},
                        {"label": "iQIYI", "url": "https://www.iq.com/", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "the-super-cube",
            "title": "The Super Cube",
            "alt": "Chao Neng Lifang · 超能立方",
            "origin": "Chinese Manhua",
            "nsfw": False,
            "description": "An ordinary guy accidentally merges with a mysterious cube that grants insane superpowers, launching him into nonstop urban supernatural battles.",
            "novel": None,
            "comic": {
                "id": "the-super-cube",
                "name": "The Super Cube",
                "sub_format": "Chinese Manhua",
                "release_year": 2017,
                "link": "https://anilist.co/manga/120313",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/120313", "kind": "tracker"},
                    {"label": "MangaUpdates", "url": "https://www.mangaupdates.com/series/pibq932/super-cube", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=The%20Super%20Cube&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "the-super-cube-2d-donghua",
                    "name": "The Super Cube (2D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "2D Donghua",
                    "release_year": 2025,
                    "link": "https://anilist.co/anime/166442",
                    "description": "2025 breakout urban superpower fantasy praised for flashy 2D sakuga fights and eye-candy action animation.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/166442", "kind": "tracker"},
                        {"label": "iQIYI", "url": "https://www.iq.com/", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "over-the-divine-realms",
            "title": "Over the Divine Realms",
            "alt": "Shenguo Zhi Shang · Above the Kingdom of God · 神国之上",
            "origin": "Chinese Web Novel",
            "nsfw": False,
            "description": "A reincarnated Sword Supreme casually fights realms above his level while showing genuine romance and affection with his wives in a producer-confirmed faithful true harem.",
            "novel": {
                "name": "Over the Divine Realms (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2020,
                "link": "https://www.novelupdates.com/?s=Over%20the%20Divine%20Realms",
                "links": [
                    {"label": "NovelUpdates (Search)", "url": "https://www.novelupdates.com/?s=Over%20the%20Divine%20Realms", "kind": "tracker"},
                ],
            },
            "comic": None,
            "motion": [
                {
                    "id": "over-the-divine-realms-3d-donghua",
                    "name": "Over the Divine Realms (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2025,
                    "link": "https://anilist.co/anime/195883",
                    "description": "Full 18+ min episodes with strong modern 3D visuals on iQIYI (CG Year; S2 expected 2026–2027). One of the best-looking full-length true-harem donghua.",
                    "links": [
                        {"label": "AniList (S1)", "url": "https://anilist.co/anime/195883", "kind": "tracker"},
                        {"label": "AniList (S2)", "url": "https://anilist.co/anime/199088", "kind": "tracker"},
                        {"label": "iQIYI", "url": "https://www.iq.com/", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "the-first-order",
            "title": "The First Order",
            "alt": "Di Yi Xu Lie · 第一序列",
            "origin": "Chinese Manhua & Web Novel",
            "nsfw": False,
            "description": "In a harsh post-apocalyptic world of walled strongholds and mutants, sharp-witted scavenger Ren Xiaosu awakens a mysterious system that lets him copy abilities and outsmart factions.",
            "novel": {
                "name": "The First Order (Web Novel)",
                "sub_format": "Chinese Web Novel",
                "release_year": 2019,
                "link": "https://www.novelupdates.com/?s=The%20First%20Order",
                "links": [
                    {"label": "NovelUpdates (Search)", "url": "https://www.novelupdates.com/?s=The%20First%20Order", "kind": "tracker"},
                ],
            },
            "comic": {
                "id": "the-first-order",
                "name": "The First Order",
                "sub_format": "Chinese Manhua",
                "release_year": 2021,
                "link": "https://anilist.co/manga/140154",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/140154", "kind": "tracker"},
                    {"label": "MangaUpdates", "url": "https://www.mangaupdates.com/series/fea7f3b/the-first-order", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=The%20First%20Order&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "the-first-order-3d-donghua",
                    "name": "The First Order (3D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "3D Donghua",
                    "release_year": 2023,
                    "link": "https://anilist.co/anime/141857",
                    "description": "Gritty wasteland 3D post-apocalypse + system donghua with solid survival atmosphere around sharp-witted scavenger Ren Xiaosu.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/141857", "kind": "tracker"},
                        {"label": "WeTV Search", "url": "https://wetv.vip/en/search?q=The%20First%20Order", "kind": "official"},
                    ],
                },
            ],
        },
        {
            "franchise_id": "the-laid-off-demon",
            "title": "The Laid Off Demon",
            "alt": "Shiye Mowang · Wo Bei Yao Wang Jie Gu Le · 失业魔王",
            "origin": "Chinese Manhua",
            "nsfw": False,
            "description": "A lighthearted 2025 workplace comedy where an absurdly overqualified former Demon King desperately takes entry-level adventuring jobs just to pay the bills.",
            "novel": None,
            "comic": {
                "id": "the-laid-off-demon",
                "name": "The Laid Off Demon King",
                "sub_format": "Chinese Manhua",
                "release_year": 2019,
                "link": "https://anilist.co/manga/113485",
                "links": [
                    {"label": "AniList (Manhua)", "url": "https://anilist.co/manga/113485", "kind": "tracker"},
                    {"label": "comix.to Search", "url": "https://comix.to/browse?q=The%20Laid%20Off%20Demon&sort=relevance%3Adesc", "kind": "unofficial"},
                ],
            },
            "motion": [
                {
                    "id": "the-laid-off-demon-2d-donghua",
                    "name": "The Laid Off Demon (2D Donghua)",
                    "media_type": "donghua",
                    "sub_format": "2D Donghua",
                    "release_year": 2025,
                    "link": "https://anilist.co/anime/168244",
                    "description": "Skyloong / Tencent 2025 2D workplace comedy turning fantasy tropes on their head as an OP former Demon King works entry-level jobs for cash.",
                    "links": [
                        {"label": "AniList", "url": "https://anilist.co/anime/168244", "kind": "tracker"},
                        {"label": "WeTV Search", "url": "https://wetv.vip/en/search?q=The%20Laid%20Off%20Demon", "kind": "official"},
                    ],
                },
            ],
        },
    ]


def build_multi_tier_catalog(
    existing_catalog: list[dict[str, Any]],
    include_obsidian_batch: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Expand catalog into deduplicated, interconnected multi-tier sub-entries across all franchises."""
    items: list[dict[str, Any]] = [dict(x) for x in existing_catalog]
    used_ids: set[str] = {str(x.get("id", "")).strip() for x in items if x.get("id")}
    used_names: set[str] = {str(x.get("name", "")).strip().lower() for x in items if x.get("name")}
    by_franchise: dict[str, list[dict[str, Any]]] = {}
    for it in items:
        fid = str(it.get("franchise_id") or it.get("id") or _slugify(str(it.get("name") or ""))).strip()
        it["franchise_id"] = fid
        by_franchise.setdefault(fid, []).append(it)

    stats = {"imported_franchises": 0, "added_subentries": 0, "normalized_existing": 0}

    # 1. Import & deduplicate curated multi-tier batches (Obsidian + Donghua batches) if not already present
    if include_obsidian_batch:
        for fdef in _parse_obsidian_new_franchises() + _parse_donghua_curated_franchises():
            fid = fdef["franchise_id"]
            if fid in by_franchise or fdef["title"].lower() in used_names:
                continue
            stats["imported_franchises"] += 1
            created: list[dict[str, Any]] = []
            has_text = fdef["novel"] is not None
            nsfw = bool(fdef.get("nsfw"))

            novel_id = ""
            if fdef["novel"]:
                nov = fdef["novel"]
                novel_id = _unique_id(f"{fid}-novel", used_ids)
                novel_rec = {
                    "id": novel_id,
                    "name": _unique_name(nov["name"], used_names, "Novel"),
                    "alt": fdef["alt"],
                    "media_type": "light_novel",
                    "tier": "source",
                    "sub_format": nov["sub_format"],
                    "source_is_text": True,
                    "nsfw": nsfw,
                    "link": nov["link"],
                    "origin": fdef["origin"],
                    "anime": f"**See Franchise** — {len(fdef['motion'])} motion adaptation(s)." if fdef["motion"] else "**None**",
                    "live_action": "**None**",
                    "description": fdef["description"],
                    "poster_url": "",
                    "poster_cached_file": "",
                    "watchlist_status": "",
                    "franchise_id": fid,
                    "franchise_title": fdef["title"],
                    "parent_id": "",
                    "links": nov["links"],
                    "relations": [],
                }
                if nov.get("release_year") is not None:
                    novel_rec["release_year"] = int(nov["release_year"])
                created.append(novel_rec)
                stats["added_subentries"] += 1

            comic_id = ""
            comic_rec: dict[str, Any] | None = None
            com = fdef.get("comic")
            if com:
                comic_id = _unique_id(com["id"], used_ids)
                anime_summary = "**None**"
                live_summary = "**None**"
                motion_only = [m for m in fdef["motion"] if m["media_type"] in ("anime", "donghua", "movie")]
                live_only = [m for m in fdef["motion"] if m["media_type"] in ("tv_series",)]
                if motion_only:
                    anime_summary = " · ".join(f"[{m['name']}]({m['link']})" for m in motion_only)
                if live_only:
                    live_summary = " · ".join(f"[{m['name']}]({m['link']})" for m in live_only)

                comic_rec = {
                    "id": comic_id,
                    "name": _unique_name(com["name"], used_names, "Comic"),
                    "alt": fdef["alt"],
                    "media_type": "comic",
                    "tier": "visual",
                    "sub_format": com["sub_format"],
                    "source_is_text": has_text,
                    "nsfw": nsfw,
                    "link": com["link"],
                    "origin": fdef["origin"],
                    "anime": anime_summary,
                    "live_action": live_summary,
                    "description": fdef["description"],
                    "poster_url": "",
                    "poster_cached_file": "",
                    "watchlist_status": "",
                    "franchise_id": fid,
                    "franchise_title": fdef["title"],
                    "parent_id": novel_id,
                    "links": com["links"],
                    "relations": [],
                }
                if com.get("release_year") is not None:
                    comic_rec["release_year"] = int(com["release_year"])
                created.append(comic_rec)
                stats["added_subentries"] += 1

            for mot in fdef["motion"]:
                mot_id = _unique_id(mot["id"], used_ids)
                mot_rec = {
                    "id": mot_id,
                    "name": _unique_name(mot["name"], used_names, mot["sub_format"]),
                    "alt": fdef["alt"],
                    "media_type": mot["media_type"],
                    "tier": "motion",
                    "sub_format": mot["sub_format"],
                    "source_is_text": has_text,
                    "nsfw": nsfw,
                    "link": mot["link"],
                    "origin": fdef["origin"],
                    "anime": f"**{mot['sub_format']}** — {mot['description']}" if mot["media_type"] in ("anime", "donghua") else "**See Franchise**",
                    "live_action": f"**{mot['sub_format']}** — {mot['description']}" if mot["media_type"] in ("tv_series", "movie") else "**None**",
                    "description": mot["description"],
                    "poster_url": "",
                    "poster_cached_file": "",
                    "watchlist_status": "",
                    "franchise_id": fid,
                    "franchise_title": fdef["title"],
                    "parent_id": comic_id or novel_id,
                    "links": mot["links"],
                    "relations": [],
                }
                if mot.get("release_year") is not None:
                    mot_rec["release_year"] = int(mot["release_year"])
                created.append(mot_rec)
                stats["added_subentries"] += 1

            rel_anchor = comic_rec or (created[0] if created else None)
            if rel_anchor is not None:
                for su in fdef.get("shared_universe", []):
                    rel_anchor["relations"].append({"relation": "shared_universe", "target_id": su, "target_type": "comic", "title": su.replace("-", " ").title()})

            items.extend(created)
            by_franchise[fid] = created

    # 2. Backfill & normalize all existing entries into multi-tier sub-entries
    new_additions: list[dict[str, Any]] = []
    for fid, group in list(by_franchise.items()):
        existing_types = {str(g.get("media_type", "comic")).lower() for g in group}
        root_comic = next((g for g in group if g.get("media_type") == "comic"), None)
        root_primary = root_comic or group[0]
        franchise_title = str(root_primary.get("franchise_title") or re.sub(r"\s*\([^)]*\)\s*$", "", str(root_primary.get("name", fid))).strip())
        origin = str(root_primary.get("origin") or "")
        alt = str(root_primary.get("alt") or "")
        has_text = "light_novel" in existing_types or _has_text_source(origin)
        is_nsfw = any(bool(g.get("nsfw")) for g in group) or "secret class" in franchise_title.lower()

        # Normalize existing entries in group first
        for g in group:
            stats["normalized_existing"] += 1
            mt = str(g.get("media_type", "comic")).lower()
            g["franchise_id"] = fid
            g.setdefault("franchise_title", franchise_title)
            g.setdefault("nsfw", is_nsfw)
            g["source_is_text"] = has_text
            g.setdefault("description", "")
            g.setdefault("poster_url", "")
            g.setdefault("poster_cached_file", "")
            g.setdefault("watchlist_status", "")
            if not g.get("added_at"):
                if fid in OBSIDIAN_BATCH_2026_11_26:
                    g["added_at"] = "2026-11-26"
                elif g.get("watchlist_status") or fid == "outlander":
                    g["added_at"] = "2026-11-24"
                else:
                    g["added_at"] = "2026-11-20"
            g.setdefault("updated_at", "2026-11-26")
            if g.get("release_year") is None:
                inferred_year = extract_year_from_text(
                    g.get("name", ""),
                    g.get("description", ""),
                    g.get("anime", "") if mt in ("anime", "donghua", "movie") else "",
                    g.get("live_action", "") if mt in ("tv_series", "movie") else "",
                )
                if inferred_year:
                    g["release_year"] = inferred_year
            if mt == "light_novel":
                g["tier"] = "source"
                g.setdefault("sub_format", "Web Novel" if "web" in origin.lower() else "Light Novel")
            elif mt == "comic":
                g["tier"] = "visual"
                g.setdefault("sub_format", _detect_comic_sub_format(origin))
            else:
                g["tier"] = "motion"
                if not g.get("sub_format"):
                    if mt == "donghua":
                        g["sub_format"] = "3D Donghua" if "3d" in str(g.get("anime", "")).lower() else "Donghua"
                    elif mt == "movie":
                        g["sub_format"] = "Movie"
                    elif mt == "tv_series":
                        g["sub_format"] = "Live-Action Series"
                    else:
                        g["sub_format"] = "Anime"

            if not g.get("links"):
                links: list[dict[str, str]] = []
                primary_url = str(g.get("link") or "")
                if primary_url and "mega.nz" not in primary_url.lower():
                    lbl = "comix.to" if "comix.to" in primary_url else ("IMDb" if "imdb.com" in primary_url else "Primary Link")
                    links.append({"label": lbl, "url": primary_url, "kind": classify_link_kind(primary_url, lbl)})
                for field in ("anime", "live_action"):
                    for lk in extract_markdown_links(str(g.get(field, ""))):
                        if not any(x["url"] == lk["url"] for x in links):
                            links.append(lk)
                g["links"] = links

        # Create Tier 1 Source Novel sub-entry if text source exists without light_novel node
        novel_node = next((g for g in group if g.get("media_type") == "light_novel"), None)
        if has_text and novel_node is None and root_comic is not None and "phonetic" not in origin.lower():
            nov_fmt = "Web Novel" if "web novel" in origin.lower() or "web serial" in origin.lower() else "Light Novel"
            nov_id = _unique_id(f"{fid}-novel", used_ids)
            nov_link = f"https://www.novelupdates.com/series/{_slugify(franchise_title)}/"
            novel_node = {
                "id": nov_id,
                "name": _unique_name(f"{franchise_title} ({nov_fmt})", used_names, nov_fmt),
                "alt": alt,
                "media_type": "light_novel",
                "tier": "source",
                "sub_format": nov_fmt,
                "source_is_text": True,
                "nsfw": is_nsfw,
                "link": nov_link,
                "origin": origin,
                "anime": "**See Franchise**",
                "live_action": "**None**",
                "description": "",
                "poster_url": "",
                "poster_cached_file": "",
                "watchlist_status": "",
                "franchise_id": fid,
                "franchise_title": franchise_title,
                "parent_id": "",
                "links": [{"label": "NovelUpdates (Search)", "url": f"https://www.novelupdates.com/?s={urllib.parse.quote(franchise_title)}", "kind": "tracker"}],
                "relations": [],
            }
            group.append(novel_node)
            new_additions.append(novel_node)
            stats["added_subentries"] += 1

        if root_comic is not None:
            root_comic["parent_id"] = novel_node["id"] if novel_node else ""
            if novel_node and root_comic.get("links"):
                # Keep comic's own links focused on comic reading + keep anime/live on their nodes
                comic_only_links = [lk for lk in root_comic["links"] if "comix.to" in lk["url"] or "webtoons.com" in lk["url"] or "tapas.io" in lk["url"] or "toptoon.com" in lk["url"] or "webnovel.com/comic" in lk["url"]]
                if comic_only_links:
                    root_comic["links"] = comic_only_links

        # Split Tier 3 Anime / Donghua / Fan Motion / Movie / Live-Action from comic text
        if root_comic is not None:
            anime_txt = str(root_comic.get("anime") or "**None**")
            anime_l = anime_txt.lower()
            has_motion_node = any(g.get("media_type") in ("anime", "donghua") for g in group)
            if not anime_txt.startswith("**None**") and "phonetic" not in origin.lower() and not anime_l.startswith("*note:") and not has_motion_node:
                is_donghua = "donghua" in anime_l or "manhua" in origin.lower()
                is_fan = any(k in anime_l for k in ("fan motion", "fan anim", "fan mmv", "unofficial", "teaser", "promo", "animatic"))
                is_prod = "in production" in anime_l
                mtype = "donghua" if is_donghua else "anime"
                if is_prod and not ("s1" in anime_l or "episode" in anime_l):
                    sub_fmt = "Anime (In Production)" if mtype == "anime" else "Donghua (In Production)"
                elif is_fan and "**yes" not in anime_l:
                    sub_fmt = "Official Teaser / Fan Motion" if "teaser" in anime_l or "official" in anime_l else "Fan Motion"
                elif mtype == "donghua":
                    sub_fmt = "3D Donghua" if "3d" in anime_l else "2D Donghua"
                else:
                    sub_fmt = "Anime Series"
                mot_links = extract_markdown_links(anime_txt)
                mot_link = mot_links[0]["url"] if mot_links else f"https://www.youtube.com/results?search_query={urllib.parse.quote(franchise_title + ' anime')}"
                mot_id = _unique_id(f"{fid}-{mtype}", used_ids)
                mot_node = {
                    "id": mot_id,
                    "name": _unique_name(f"{franchise_title} ({sub_fmt})", used_names, sub_fmt),
                    "alt": alt,
                    "media_type": mtype,
                    "tier": "motion",
                    "sub_format": sub_fmt,
                    "source_is_text": has_text,
                    "nsfw": is_nsfw,
                    "link": mot_link,
                    "origin": origin,
                    "anime": anime_txt,
                    "live_action": "**None**",
                    "description": strip_markdown(anime_txt),
                    "poster_url": "",
                    "poster_cached_file": "",
                    "watchlist_status": root_comic.get("watchlist_status", ""),
                    "franchise_id": fid,
                    "franchise_title": franchise_title,
                    "parent_id": root_comic["id"],
                    "links": mot_links,
                    "relations": [],
                }
                group.append(mot_node)
                new_additions.append(mot_node)
                stats["added_subentries"] += 1

            # Also split separate Movie node if anime text explicitly mentions a feature film
            has_movie_node = any(g.get("media_type") == "movie" for g in group)
            if not has_movie_node and any(tok in anime_l for tok in ("film trilogy", "theatrical film", "anime film", "feature film", "movie (")):
                mov_links = extract_markdown_links(anime_txt)
                mov_link = mov_links[0]["url"] if mov_links else f"https://www.imdb.com/find/?q={urllib.parse.quote(franchise_title)}"
                mov_id = _unique_id(f"{fid}-anime-film", used_ids)
                mov_node = {
                    "id": mov_id,
                    "name": _unique_name(f"{franchise_title} (Anime Film)", used_names, "Film"),
                    "alt": alt,
                    "media_type": "movie",
                    "tier": "motion",
                    "sub_format": "Animated Film",
                    "source_is_text": has_text,
                    "nsfw": is_nsfw,
                    "link": mov_link,
                    "origin": origin,
                    "anime": anime_txt,
                    "live_action": "**None**",
                    "description": strip_markdown(anime_txt),
                    "poster_url": "",
                    "poster_cached_file": "",
                    "watchlist_status": "",
                    "franchise_id": fid,
                    "franchise_title": franchise_title,
                    "parent_id": root_comic["id"],
                    "links": mov_links,
                    "relations": [],
                }
                group.append(mov_node)
                new_additions.append(mov_node)
                stats["added_subentries"] += 1

            live_txt = str(root_comic.get("live_action") or "**None**")
            live_l = live_txt.lower()
            has_live_node = any(
                g.get("media_type") == "tv_series"
                or "live-action" in str(g.get("sub_format", "")).lower()
                or "stage" in str(g.get("sub_format", "")).lower()
                for g in group
            )
            if not live_txt.startswith("**None**") and live_txt.strip().upper() != "N/A" and not has_live_node:
                is_movie_live = any(tok in live_l for tok in ("film", "movie")) and not any(tok in live_l for tok in ("series", "drama"))
                ltype = "movie" if is_movie_live and not has_movie_node else "tv_series"
                if "k-drama" in live_l:
                    lfmt = "Live-Action K-Drama"
                elif "c-drama" in live_l:
                    lfmt = "Live-Action C-Drama"
                elif "stage" in live_l:
                    lfmt = "Stage Play"
                elif ltype == "movie":
                    lfmt = "Live-Action Film"
                else:
                    lfmt = "Live-Action Series"
                live_links = extract_markdown_links(live_txt)
                live_link = live_links[0]["url"] if live_links else f"https://www.imdb.com/find/?q={urllib.parse.quote(franchise_title)}"
                live_id = _unique_id(f"{fid}-live", used_ids)
                live_node = {
                    "id": live_id,
                    "name": _unique_name(f"{franchise_title} ({lfmt})", used_names, lfmt),
                    "alt": alt,
                    "media_type": ltype,
                    "tier": "motion",
                    "sub_format": lfmt,
                    "source_is_text": has_text,
                    "nsfw": is_nsfw,
                    "link": live_link,
                    "origin": origin,
                    "anime": "**None**",
                    "live_action": live_txt,
                    "description": strip_markdown(live_txt),
                    "poster_url": "",
                    "poster_cached_file": "",
                    "watchlist_status": "",
                    "franchise_id": fid,
                    "franchise_title": franchise_title,
                    "parent_id": root_comic["id"],
                    "links": live_links,
                    "relations": [],
                }
                group.append(live_node)
                new_additions.append(live_node)
                stats["added_subentries"] += 1

        # Rebuild normalized intra-franchise relations while preserving shared_universe links
        for g in group:
            ext_rels = [r for r in (g.get("relations") or []) if isinstance(r, dict) and r.get("relation") == "shared_universe"]
            intra_rels = []
            for peer in group:
                if peer["id"] == g["id"]:
                    continue
                if g.get("tier") == "source" and peer.get("tier") in ("visual", "motion"):
                    rel_kind = "adapted_to"
                elif g.get("tier") in ("visual", "motion") and peer.get("tier") == "source":
                    rel_kind = "adapted_from"
                elif g.get("tier") == "visual" and peer.get("tier") == "motion":
                    rel_kind = "adapted_to"
                elif g.get("tier") == "motion" and peer.get("tier") == "visual":
                    rel_kind = "adapted_from"
                else:
                    rel_kind = "related"
                intra_rels.append({
                    "relation": rel_kind,
                    "target_id": peer["id"],
                    "target_type": peer.get("media_type", "comic"),
                    "title": peer["name"],
                })
            g["relations"] = intra_rels + ext_rels
            if g.get("tier") == "motion" and not g.get("parent_id"):
                parent = next((x for x in group if x.get("tier") == "visual"), None) or next((x for x in group if x.get("tier") == "source"), None)
                g["parent_id"] = parent["id"] if parent else ""

    items.extend(new_additions)
    # Ensure all newly created items also carry chronological added_at / release_year / updated_at
    today_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    for it in items:
        fid_it = str(it.get("franchise_id") or "")
        if not it.get("added_at"):
            it["added_at"] = "2026-11-26" if fid_it in OBSIDIAN_BATCH_2026_11_26 or str(it.get("media_type")) != "comic" else today_iso
        it.setdefault("updated_at", today_iso)
        if it.get("release_year") is None:
            mt_it = str(it.get("media_type", ""))
            yr = extract_year_from_text(
                it.get("name", ""),
                it.get("description", ""),
                it.get("anime", "") if mt_it in ("anime", "donghua", "movie") else "",
                it.get("live_action", "") if mt_it in ("tv_series", "movie") else "",
            )
            if yr:
                it["release_year"] = yr
    return items, stats


def enrich_single_franchise(
    group: list[dict[str, Any]],
    download_posters: bool = True,
    cache_dir: Path = POSTER_CACHE_DIR,
) -> dict[str, int]:
    """Fetch metadata, synopses, NSFW signals, release years, and local poster cache for one franchise group."""
    stats = {"metadata_updated": 0, "posters_cached": 0}
    if not group:
        return stats
    primary = next((g for g in group if g.get("media_type") == "comic"), None) or group[0]
    title = str(primary.get("franchise_title") or primary.get("name") or "").strip()
    alt = str(primary.get("alt") or "")
    if not title or "phonetic" in str(primary.get("origin", "")).lower():
        return stats

    al = query_anilist_franchise(title, alt=alt)
    mu = query_mangaupdates(title, alt=alt)
    has_live_or_movie = any(g.get("media_type") in ("tv_series", "movie") for g in group)
    has_official_anim = any(
        g.get("media_type") in ("anime", "donghua")
        and not any(k in str(g.get("sub_format", "")).lower() for k in ("fan", "teaser"))
        for g in group
    )
    imdb = query_imdb_suggestion(title, alt=alt) if (has_live_or_movie or has_official_anim) else {}
    needs_tv = any(g.get("media_type") == "tv_series" for g in group)
    tv = query_tvmaze(title, alt=alt) if needs_tv else None
    has_donghua = any(g.get("media_type") == "donghua" for g in group)
    has_novel = any(g.get("media_type") == "light_novel" for g in group)
    bgm_anime = query_bangumi(title, alt=alt, subject_type=2) if (has_donghua or (has_official_anim and not al.get("anime"))) else None
    bgm_book = query_bangumi(title, alt=alt, subject_type=1) if has_novel else None
    wiki = None
    if not al and not mu and not imdb:
        wiki = query_wikipedia_summary(title)

    is_adult_signal = any(bool(v.get("is_adult")) for v in al.values())
    if not al.get("comic") and mu and mu.get("is_adult"):
        is_adult_signal = True

    today_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    for entry in group:
        mt = str(entry.get("media_type", "comic")).lower()
        sub_l = str(entry.get("sub_format", "")).lower()
        is_fan_or_teaser = any(k in sub_l for k in ("fan", "teaser"))
        changed = False
        if is_adult_signal and not entry.get("nsfw"):
            entry["nsfw"] = True
            changed = True

        src_data: dict[str, Any] | None = None
        yt_thumb = extract_youtube_thumbnail(entry.get("links") or [])
        if mt == "light_novel":
            src_data = al.get("light_novel") or bgm_book or (mu if mu and "novel" in mu.get("type", "") else None) or wiki or al.get("comic") or mu
        elif mt == "comic":
            src_data = al.get("comic") or mu or wiki
        elif mt == "donghua":
            if is_fan_or_teaser:
                src_data = ({"poster_url": yt_thumb, "source": "youtube"} if yt_thumb else None) or bgm_anime or al.get("anime") or al.get("comic") or mu
            else:
                src_data = bgm_anime or al.get("anime") or ({"poster_url": yt_thumb, "source": "youtube"} if yt_thumb else None) or al.get("comic") or mu or wiki
        elif mt == "anime":
            if is_fan_or_teaser:
                src_data = ({"poster_url": yt_thumb, "source": "youtube"} if yt_thumb else None) or al.get("anime") or al.get("comic") or mu
            else:
                imdb_anim = imdb.get("tv_series") if (imdb.get("tv_series") and imdb["tv_series"]["score"] >= 0.90) else None
                src_data = al.get("anime") or bgm_anime or imdb_anim or ({"poster_url": yt_thumb, "source": "youtube"} if yt_thumb else None) or al.get("comic") or mu or wiki
        elif mt == "movie":
            src_data = al.get("movie") or imdb.get("movie") or al.get("anime") or bgm_anime or wiki
        elif mt == "tv_series":
            src_data = tv or imdb.get("tv_series") or wiki or imdb.get("movie")

        if not src_data:
            ids = extract_entry_ids(entry)
            al_id = ids["anilist_ids"][0] if ids["anilist_ids"] else None
            mal_id = ids["mal_ids"][0] if ids["mal_ids"] else None
            bgm_id = ids["bangumi_ids"][0] if ids["bangumi_ids"] else None
            if al_id or mal_id or bgm_id:
                cross = resolve_cross_ids(anilist_id=al_id, mal_id=mal_id, bangumi_id=bgm_id)
                if cross.get("found") and (cross.get("poster_url") or cross.get("imdb_id")):
                    src_data = {
                        "poster_url": cross.get("poster_url", ""),
                        "imdb_url": f"https://www.imdb.com/title/{cross['imdb_id']}/" if cross.get("imdb_id") else "",
                        "source": "shared_mappings",
                    }

        if src_data:
            cand_poster = str(src_data.get("poster_url") or "").strip()
            if cand_poster and not entry.get("poster_url"):
                entry["poster_url"] = cand_poster
                changed = True
            cand_desc = str(src_data.get("description") or src_data.get("meta_summary") or "").strip()
            if cand_desc and len(str(entry.get("description") or "")) < 40:
                entry["description"] = cand_desc
                changed = True
            if src_data.get("year") and entry.get("release_year") is None:
                entry["release_year"] = int(src_data["year"])
                changed = True
            if src_data.get("imdb_url") and not is_fan_or_teaser and mt != "donghua" and not any(x.get("url") == src_data["imdb_url"] for x in entry.get("links", [])):
                entry.setdefault("links", []).append({"label": "IMDb", "url": src_data["imdb_url"], "kind": "tracker"})
                changed = True
            if src_data.get("url") and src_data.get("source") in ("anilist", "mangaupdates", "bangumi") and not any(x.get("url") == src_data["url"] for x in entry.get("links", [])):
                lbl = {"anilist": "AniList", "mangaupdates": "MangaUpdates", "bangumi": "Bangumi"}[src_data["source"]]
                entry.setdefault("links", []).append({"label": lbl, "url": src_data["url"], "kind": "tracker"})
                changed = True

        if download_posters and entry.get("poster_url"):
            cached = download_poster_to_cache(entry["id"], str(entry["poster_url"]), cache_dir=cache_dir)
            if cached and entry.get("poster_cached_file") != cached:
                entry["poster_cached_file"] = cached
                stats["posters_cached"] += 1
                changed = True

        if changed:
            entry["updated_at"] = today_iso
            stats["metadata_updated"] += 1
    return stats


def enrich_catalog_metadata(
    catalog: list[dict[str, Any]],
    franchise_filter: str | None = None,
    max_workers: int = 5,
    download_posters: bool = True,
    progress_cb: Any = None,
    cancel_check: Any = None,
) -> dict[str, Any]:
    """Enrich synopses, NSFW flags, tracker links, and local poster cache across franchises."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in catalog:
        fid = str(item.get("franchise_id") or item.get("id") or "")
        if franchise_filter and fid.lower() != franchise_filter.lower():
            continue
        groups.setdefault(fid, []).append(item)

    total_groups = len(groups)
    done = 0
    total_meta = 0
    total_posters = 0
    cancelled = False

    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as pool:
        future_map = {
            pool.submit(enrich_single_franchise, grp, download_posters): fid
            for fid, grp in groups.items()
        }
        for fut in as_completed(future_map):
            if cancel_check and cancel_check():
                cancelled = True
                break
            fid = future_map[fut]
            try:
                res = fut.result()
                total_meta += res["metadata_updated"]
                total_posters += res["posters_cached"]
            except Exception:
                pass
            done += 1
            if progress_cb:
                progress_cb(done, total_groups, fid)

    return {
        "franchises_scanned": done,
        "total_franchises": total_groups,
        "metadata_updated": total_meta,
        "posters_cached": total_posters,
        "cancelled": cancelled,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def rebuild_and_save_catalog(
    catalog_path: Path = CATALOG_JSON_PATH,
    enrich: bool = False,
    download_posters: bool = True,
) -> dict[str, Any]:
    """Run multi-tier expansion/deduplication and optionally enrich & persist catalog JSON."""
    existing = load_catalog(catalog_path)
    expanded, build_stats = build_multi_tier_catalog(existing, include_obsidian_batch=True)
    enrich_stats: dict[str, Any] = {}
    if enrich:
        enrich_stats = enrich_catalog_metadata(expanded, download_posters=download_posters)
    catalog_path.write_text(json.dumps(expanded, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "total_entries": len(expanded),
        "build_stats": build_stats,
        "enrich_stats": enrich_stats,
    }
