# GameRank — data/games/schema.md (v4.0.0)

## Purpose
Defines every field in `data/games/games.json` and the synchronized `games.js` mirrors (`web/games/data/games.js`, `data/games/games.js`) so any future game additions via `src/scrapers/multi_site_games.py --add-steam` follow one unified structure.

## A record (each object in `window.GAMES` / `games.json`)

| Field | Type | Values / meaning |
|---|---|---|
| `id` | string | stable slug used for lookups + `data-id` in the UI **(never change once saved)** |
| `name` | string | display name |
| `steamAppId` | number \| null | official Steam Store AppID when available (`null` for Battle.net / standalone) |
| `ownership` | enum | `owned` (Steam library) / `wishlist` (researched candidates) |
| `genre` | enum | `classic-rts` / `4x-grand` / `hybrid-td` / `army-sim` / `tactical-rpg` / `fps-shooter` / `action-adventure` / `rpg` / `racing-sim` / `puzzle-platformer` / `fighting-arcade` / `vr-utility` |
| `priceModel` | enum | `f2p` / `paid` |
| `priceUsd` | number | 0 when free or bundled |
| `priceNote` | string | pricing nuance (DLC situation, sales, bundle/delisted status) |
| `campaign` | object | `exists` (bool) · `freeOrPaid` (`free`/`paid`/`paid-dlc`/`n/a`) · `quality` 0–10 · `notes` |
| `ai` | object | `score` 0–10 for AI/bots/enemies · `notes` captures behavior |
| `setting` | enum | `ancient` / `realistic-modern` / `futuristic` / `fantasy` / `post-apocalyptic` / `steampunk` |
| `graphics` | object | `score` 0–10 · `notes` |
| `players` | object | `status` (`very-active` / `active` / `moderate` / `small` / `inactive` / `n/a-sp`) · `notes` |
| `companions` | array | optional linked `{ name, kind, note }` for Test Servers, Friend's Pass, expansions, or duplicates |
| `specs` | object | `min`/`rec` objects with verbatim store-page `cpu` / `gpu` / `ram` / `storage` / `os` |
| `size` | object | `download` and `install` strings as published/estimated (`~` marks estimate) |
| `installGB` | number | numeric install size used for sorting + HDD scoring (max value if a range) |
| `gpuMinTier` / `gpuRecTier` | number | **0–10 GPU class scale** (below). Drives compatibility scoring. |
| `cpuDemand` | enum | `low` / `medium` / `high` — simulation load of the game engine |
| `compatNote` | string | researcher's hand-written verdict for the target PC |
| `compat` | object | **added at runtime** by `js/rank.js` — `{ score 0–100, tier, notes[] }` |
| `bench` | object | `playable` / `sixty` sub-objects `{ fps, settings }` — real-world 1080p frames + concrete preset on a Vega 7/8-class iGPU. `playable` targets a stable ~30–40 fps; `sixty` targets ~60 fps (often 720p / reduced scale / Lowest). `source[]` = performance citations (NotebookCheck, GameGPU, FPSGauge, iGPU YouTube tests, Steam/reddit threads). `(est.)` prefixes mark reasoned estimates. |
| `stores` | array | `{ name, url }` of every storefront/launcher selling it in 2026 (Steam / Battle.net / Epic / GOG / MS Store / EA app / official site) |
| `storeNote` | string | launcher/client nuances (crossplay, subscription availability, exclusivity) |
| `storageAdvice` | object | `{ verdict, note }` — **SSD vs HDD for this game, and how disk affects it**. `verdict` enum: `hdd-fine` (HDD no real cost) / `ssd-helps` (HDD = slower loads/boots only, SSD is a comfort upgrade) / `ssd-strongly-advised` (HDD = long loads + streaming pop-in/patch pain; FPS may worsen indirectly). The `note` spells out the *actual effect* (load/boot times, asset streaming, patch re-downloads, pagefile/swap). FPS is graphics/CPU-bound — storage advice never claims an FPS fix unless streaming is the cause. |
| `quality30` | object | **v3** — the best-LOOKING settings preset that still holds ~30 fps on a Vega 7/8-class iGPU, in **two resolutions**: `fps1080` / `settings1080` (1080p) and `fps900` / `settings900` (1600×900). Distinct from "Lowest". Location varies by record vintage: v1–v2 records carry it **at record level**; v3 records carry it **inside `bench`** — `getQuality30(game)` in `js/rank.js` handles both. If 30 fps isn't achievable, the fields say so explicitly. |
| `hddSp` | object | **v3** — single-player-HDD penalty (the user does not mind long loads, so this is **stutter-focused**): `loads` (load delta in seconds/×multiplier), `fpsEffect`, `stutter` (`none`/`moderate`/`high`), `verdict` (`fine`/`slower-loads`/`stutter-risk`), `note`. Rendered as a modal block + table column by `SP_HDD_LINE()` / `HDDSP_LABEL` in `js/rank.js`. |
| `upgradeTiers` | object | **v3** — hand-researched expectations per GPU-upgrade card, keys `gtx1660s` / `rtx2060` / `rx6600`, one short line each (settings tier comfortable + rough 1080p fps, `(est.)` when inferred). Consumed by `upgradeVerdict()` in `js/rank.js`; the upgrade-simulator re-scores games independently via `computeUpgradedCompat()`. |
| `upCompat` | object | **added at runtime** when the GPU simulator is active — result of `computeUpgradedCompat(game, gpuKey)` |
| `sources` | string[] | URLs actually consulted (general dataset: store pages, charts, reviews) |

### GPU tier scale (0–10, relative)

- 0.5–1 → GeForce 6600/8600 class, Intel HD 3000–4000, any modern iGPU floor
- 1.5–2 → Intel HD 520/HD 4600, GT 420/8800 GTS, HD 5750 class
- 2.5–3 → **Vega 7 iGPU lives here (≈3, GTX 750 Ti / HD 6850 class)**, GTS 450, GT 660
- 4–4.5 → GTX 660/770/950/960 class
- 5–5.5 → GTX 1060 / 970 class
- 6.5–7 → GTX 1660 Ti / RTX 2060 class
- 8+ → RTX 3060/4060 class and above

**v3 simulator anchor points:** Vega 7 ≈ 3 · GTX 1660 Super ≈ 6.5 · RTX 2060 ≈ 7 · RX 6600 ≈ 7.5 (see `UPGRADE_GPUS` in `js/rank.js`).

## Compatibility scoring — `js/rank.js`

Core: `compatScoreFor(game, gpuTier, gpuLabel)` — works for the real iGPU **or** a simulated card.

Starts the score at the GPU margin vs minimum, then adjusts:
- GPU margin vs min tier: `min ≤ 2 → 95`, `min ≤ gpuTier → 82`, `min ≤ 4.5 → 45`, else `12`
- Recommended tier: if the simulated GPU reaches `gpuRecTier` → **+6** (records it in notes too)
- CPU demand: `high` −5, `medium` −1, `low` 0 (5600GT's 6 cores absorb most of it)
- HDD: install ≥80 GB −18, ≥40 GB −10, ≥15 GB −4
- RAM: min > 16 GB −15, recommended > 16 GB −4
- clamp 0–100 → `great ≥ 80` / `ok ≥ 45` / `struggle < 45`

`computeCompat` = `compatScoreFor` with Vega 7 (tier 3); `computeUpgradedCompat(game, gpuKey)` runs the
same scoring with the simulator's card. Disk and CPU penalties intentionally survive a GPU upgrade.
Base (Vega 7) distribution Oct 2026: 23 great · 8 ok · 12 struggle (43 games).
Simulated: 1660S → 31 great/12 ok; 2060 → 33/10; 6600 → 33/10 (CPU/HDD walls keep the rest).

Target machine (also in `js/rank.js`): **Ryzen 5 5600GT (6C/12T Zen 3), Radeon Vega 7 iGPU (tier ≈3), 16 GB dual-channel (2×8), HDD**.

## Adding a game
Copy any existing record, fill every field (no exceptions — UI tabs rely on enums), assign
`gpuMinTier`/`gpuRecTier`/`cpuDemand`/`installGB` using the scale above, research a Vega-class iGPU
fps test for `bench` (all THREE presets: ~30–40 fps playable *and* best-graphics-@30 (1080p **and**
1600×900) *and* the ~60-fps attempt), fill `hddSp` + `upgradeTiers`, list every live
`stores` entry + `storeNote`, pick `storageAdvice.verdict` using the effect ladder above, then cite
at least one source per claim group (`sources` + `bench.source`).

**Versioning policy:** every change set ships as `major.medium.minor` (see `CHANGELOG.md`); a git tag
`vX.Y.Z` is created so the previous version can always be restored from the repo.
