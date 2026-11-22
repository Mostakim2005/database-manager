"use strict";
/* ==========================================================================
   GameRank — js/rank.js
   Computes a compatibility verdict for the user's PC against each game.
   v3.0.0 adds:
     - compatScoreFor(game, gpuTier, gpuLabel): scoring against ANY GPU tier
       (powers the GPU-upgrade simulator: GTX 1660 Super / RTX 2060 / RX 6600)
     - upgradeVerdict(game, gpuKey): researched upgradeTiers line + derived
       settings-tier summary + CPU-bound caveat
     - ssdExpectation(game): what an SSD changes (streaming stutter vs load
       times only — the user does not care about load times)
     - spHdd helpers: single-player-on-HDD verdict labels (stutter-focused)
   ========================================================================== */

window.myPC = {
  cpuName: "Ryzen 5 5600GT (6C/12T)",
  gpuName: "Radeon Vega 7 iGPU",
  ramGB: 16,
  disk: "HDD",
  vegaTier: 3
};

/* Discrete-GPU upgrade options for the simulator (tier on the same 0–10 scale) */
window.UPGRADE_GPUS = {
  gtx1660s: { name: "GTX 1660 Super", short: "1660S", tier: 6.5 },
  rtx2060:  { name: "RTX 2060",       short: "2060",  tier: 7 },
  rx6600:   { name: "RX 6600",        short: "6600",  tier: 7.5 }
};

/* Parse a RAM string like "4 GB" or "512 MB" → GB */
window.parseRamGB = function (str) {
  if (!str) return 0;
  var m = /(\d+)\s*GB/i.exec(str);
  if (m) return parseInt(m[1], 10);
  m = /(\d+)\s*MB/i.exec(str);
  if (m) return parseInt(m[1], 10) / 1024;
  return 0;
};

/* Parse a size string like "~50 GB" or "17–23 GB" → numeric GB (max listed value) */
window.parseSizeGB = function (obj) {
  if (!obj || typeof obj.install !== "string") return null;
  var nums = obj.install.match(/(\d+(?:[.,]\d+)?)\s*(GB|TB)/gi) || [];
  var best = 0;
  nums.forEach(function (s) {
    var n = parseFloat(s.replace(",", "."));
    if (/TB/i.test(s)) n *= 1024;
    if (n > best) best = n;
  });
  return best || null;
};

/*
  Core scoring — works for the Vega 7 iGPU (base view) or a simulated GPU.
  Compat tiers:
    "great"    ≈ meets/exceeds minimum comfortably, light on the GPU
    "ok"       ≈ playable with tweaks — near min spec, heavy settings cuts
    "struggle" ≈ struggles / not recommended on this GPU
*/
window.compatScoreFor = function (game, gpuTier, gpuLabel) {
  var m = parseFloat(game.gpuMinTier);
  var r = parseFloat(game.gpuRecTier);
  var notes = [];
  var score;

  /* --- GPU tier vs minimum requirement --- */
  if (m <= 2)        { score = 95; notes.push("iGPU headroom: min GPU (" + game.specs.min.gpu + ") is far below " + gpuLabel); }
  else if (m <= gpuTier) { score = 82; notes.push("Min GPU ≈ " + gpuLabel + " class — playable (low/medium settings)"); }
  else if (m <= 4.5) { score = 45; notes.push("Min GPU (" + game.specs.min.gpu + ") is above " + gpuLabel + " — needs significant settings reductions"); }
  else               { score = 12; notes.push("Min GPU (" + game.specs.min.gpu + ") exceeds " + gpuLabel + " capability — likely not playable"); }

  /* --- Recommended tier: can't be penalised heavily, note it --- */
  if (r >= 6 && r > gpuTier) notes.push("Recommended GPU (" + game.specs.rec.gpu + ") is beyond " + gpuLabel + "; 'recommended' settings not reachable");
  else if (r <= gpuTier) { notes.push(gpuLabel + " meets the recommended GPU tier — recommended settings reachable"); score += 6; }

  /* --- CPU demand (6C/12T Zen 3 is strong, so penalty is small) --- */
  if (game.cpuDemand === "high")  { score -= 5; notes.push("CPU-heavy sim — 5600GT's 6 cores help a lot, big battles may still dip"); }
  else if (game.cpuDemand === "medium") { score -= 1; notes.push("Moderate CPU load — well handled"); }
  else { notes.push("Low CPU load — no worries"); }

  /* --- HDD penalty by install size --- */
  var installGB = game.installGB || window.parseSizeGB(game.size) || 0;
  if (installGB >= 80)      { score -= 18; notes.push("Massive ~" + Math.round(installGB) + " GB install — very slow on HDD, SSD strongly advised"); }
  else if (installGB >= 40) { score -= 10; notes.push("Heavy ~" + Math.round(installGB) + " GB install — slow loads + patching on HDD"); }
  else if (installGB >= 15) { score -= 4;  notes.push("~" + Math.round(installGB) + " GB install — tolerable on HDD"); }
  else                      { notes.push("Light install — HDD fine"); }

  /* --- RAM headroom (16 GB installed) --- */
  var minRam = window.parseRamGB(game.specs.min.ram);
  var recRam = window.parseRamGB(game.specs.rec.ram);
  if (minRam > window.myPC.ramGB)      { score -= 15; notes.push("Minimum RAM (" + game.specs.min.ram + ") exceeds your 16 GB"); }
  else if (recRam > window.myPC.ramGB) { score -= 4;  notes.push("Recommended RAM (" + game.specs.rec.ram + ") exceeds 16 GB — close other apps"); }

  score = Math.max(0, Math.min(100, Math.round(score)));

  var tier = score >= 80 ? "great" : score >= 45 ? "ok" : "struggle";
  return { score: score, tier: tier, notes: notes };
};

/* Base verdict on the actual PC (Vega 7 + HDD) */
window.computeCompat = function (game) {
  return window.compatScoreFor(game, window.myPC.vegaTier, "Vega 7");
};

/*
  GPU-upgrade simulator: re-score the game as if a discrete card were installed.
  Disk (HDD) and CPU penalties intentionally remain — an SSD/GPU upgrade only
  fixes what it can.
*/
window.computeUpgradedCompat = function (game, gpuKey) {
  var gpu = window.UPGRADE_GPUS[gpuKey];
  if (!gpu) return null;
  return window.compatScoreFor(game, gpu.tier, gpu.name);
};

/*
  Upgrade expectation per game + card. Prefers the hand-researched
  game.upgradeTiers[gpuKey] line; adds a derived settings summary and the
  CPU-bound caveat (RTS sim stutter does not vanish with a better GPU).
*/
window.upgradeVerdict = function (game, gpuKey) {
  var gpu = window.UPGRADE_GPUS[gpuKey];
  if (!gpu) return null;
  var r = parseFloat(game.gpuRecTier);
  var m = parseFloat(game.gpuMinTier);
  var lines = [];

  if (game.upgradeTiers && game.upgradeTiers[gpuKey]) {
    lines.push(game.upgradeTiers[gpuKey]);
  } else if (gpu.tier >= r) {
    lines.push("Recommended settings (" + game.specs.rec.gpu + " class) become comfortable (est.)");
  } else if (gpu.tier >= m) {
    lines.push("Meets minimum with headroom — low/medium settings smooth; recommended needs more GPU (est.)");
  } else {
    lines.push("Still below this game's minimum GPU tier (est.)");
  }
  if (game.cpuDemand === "high") {
    lines.push("CPU-bound caveat: max-population battles / late-game sim stutter is CPU-side and mostly unchanged.");
  }
  return { gpu: gpu, lines: lines };
};

/*
  What an SSD changes for THIS game. The user explicitly does not care about
  load times — so the verdict is framed around streaming stutter / pop-in.
*/
window.ssdExpectation = function (game) {
  var v = game.storageAdvice ? game.storageAdvice.verdict : "hdd-fine";
  var installGB = game.installGB || window.parseSizeGB(game.size) || 0;
  var head, body;
  if (v === "ssd-strongly-advised") {
    head = "SSD = night and day";
    body = "Streaming engine: on an HDD it hitches and pops textures in; an SSD largely removes that stutter and pop-in during play. fps itself recovers to the game's normal behavior.";
  } else if (v === "ssd-helps") {
    head = "SSD = smoother streaming";
    body = "Removes most texture pop-in / streaming hitches; fps is roughly unchanged (GPU/CPU-bound). Loads (which you don't mind) also drop a lot.";
  } else {
    head = "SSD adds little here";
    body = "This game loads everything upfront and streams nothing — an SSD only shortens the loads you said you don't care about. fps identical.";
  }
  if (installGB >= 40) body += " Bonus: ~" + Math.round(installGB) + " GB of patches/updates land far faster on an SSD.";
  return { head: head, body: body, verdict: v };
};

/* Single-player-on-HDD labels (stutter-focused, not load-time-focused) */
window.HDDSP_LABEL = {
  "fine": "SP on HDD: fine",
  "slower-loads": "SP on HDD: loads only",
  "stutter-risk": "SP on HDD: stutter risk"
};
window.STUTTER_LABEL = {
  "none": "No streaming stutter",
  "moderate": "Occasional streaming stutter",
  "high": "Frequent streaming stutter"
};
window.SP_HDD_LINE = function (game) {
  var h = game.hddSp || {};
  return {
    verdictLabel: window.HDDSP_LABEL[h.verdict] || h.verdict || "—",
    stutterLabel: window.STUTTER_LABEL[h.stutter] || h.stutter || "—",
    loads: h.loads || "—",
    fpsEffect: h.fpsEffect || "—",
    note: h.note || ""
  };
};

/* Normalize the quality30 preset location (old records: record-level; new: inside bench) */
window.getQuality30 = function (game) {
  return (game.bench && game.bench.quality30) || game.quality30 || null;
};

/* Decorate every game once at boot */
window.applyCompat = function (games) {
  games.forEach(function (g) {
    g.compat = window.computeCompat(g);
  });
};
