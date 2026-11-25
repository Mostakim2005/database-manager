"use strict";
/* ==========================================================================
   GameRank — js/render.js
   Pure rendering functions: table rows, cards, detail modal, badges.
   No event logic here — see js/app.js.
   v4.0.0:
     - All PC + Steam + RTS genres & settings cleanly labeled (zero undefined)
     - Ownership badges (Owned vs Wishlist)
     - Linked Companions / Test Servers / Friend's Pass badges in modal
     - Null-safe hddSp, quality30, storageAdvice, and sources (string or object)
   ========================================================================== */

var COMPAT_LABEL = {
  great:    "Runs Great \u2705",
  ok:       "Playable w/ tweaks \u26A0\uFE0F",
  struggle: "Struggles on Vega 7 \u274C"
};
var COMPAT_KEY_LABEL = {
  great: "Runs Great",
  ok: "Playable w/ tweaks",
  struggle: "Struggles"
};
var OWNERSHIP_LABEL = {
  owned: "Owned",
  wishlist: "Wishlist"
};
var SETTING_LABEL = {
  "ancient": "Ancient / Historical",
  "realistic-modern": "Realistic / Modern",
  "futuristic": "Futuristic / Sci-Fi",
  "fantasy": "Fantasy",
  "post-apocalyptic": "Post-Apocalyptic",
  "steampunk": "Steampunk"
};
var GENRE_LABEL = {
  "classic-rts": "Classic RTS",
  "4x-grand": "4X / Grand Strategy",
  "hybrid-td": "Hybrid / Tower Defense",
  "army-sim": "Army / Settlement Sim",
  "tactical-rpg": "Tactical RPG / Roguelike",
  "fps-shooter": "FPS & Shooters",
  "action-adventure": "Action & Adventure",
  "rpg": "RPG & MMO",
  "racing-sim": "Racing & Driving Sim",
  "puzzle-platformer": "Puzzle, Co-op & Indie",
  "fighting-arcade": "Fighting & Arcade",
  "vr-utility": "VR & Showcase"
};
var PLAYER_LABEL = {
  "very-active": "Very active \u{1F525}",
  "active": "Active",
  "moderate": "Moderate",
  "small": "Small",
  "inactive": "Inactive / dead",
  "n/a-sp": "N/A (single player)"
};
var CAMPAIGN_LABEL = {
  "free": "Free",
  "paid": "Paid (included)",
  "paid-dlc": "Paid / DLC",
  "n/a": "N/A"
};
function formatCampaignLabel(val) {
  if (!val) return "N/A";
  if (CAMPAIGN_LABEL[val]) return CAMPAIGN_LABEL[val];
  var low = String(val).toLowerCase();
  if (low.indexOf("free") === 0) return "Free";
  if (low.indexOf("paid-dlc") === 0) return "Paid / DLC";
  if (low.indexOf("paid") === 0) return "Paid (included)";
  if (low === "n/a") return "N/A";
  return String(val);
}
var CPU_LABEL = { low: "Low", medium: "Medium", high: "High" };
var DISK_LABEL = {
  "hdd-fine": "HDD OK",
  "ssd-helps": "SSD helps",
  "ssd-strongly-advised": "SSD advised"
};
var PRESET_LABEL = {
  playable:   "Play ~30\u201340 fps preset",
  quality30:  "Best graphics @ ~30 fps",
  sixty:      "Push ~60 fps preset"
};

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}
function bar(val) {
  var pct = Math.max(0, Math.min(100, ((Number(val) || 0) / 10) * 100));
  return '<span class="bar"><span class="bar-fill" style="width:' + pct + '%"></span></span>';
}

/* ---- small badge (cls + text; optional href makes it a link) ---- */
function badge(cls, text, href) {
  var inner = esc(text);
  if (href) inner = '<a href="' + esc(href) + '" target="_blank" rel="noopener noreferrer">' + inner + "</a>";
  return '<span class="badge ' + cls + '">' + inner + "</span>";
}
function storeBadges(game, max) {
  return (game.stores || []).slice(0, max || 2).map(function (s) {
    return badge("g-store", s.name, s.url);
  }).join(" ");
}
function ownershipBadge(game) {
  var own = game.ownership === "owned" ? "owned" : "wishlist";
  return badge("own-" + own, OWNERSHIP_LABEL[own]);
}
function safeStorageVerdict(game) {
  var v = game.storageAdvice && game.storageAdvice.verdict;
  return DISK_LABEL[v] ? v : "hdd-fine";
}
function safeHddSp(game) {
  return game.hddSp && game.hddSp.verdict ? game.hddSp : { verdict: "fine", stutter: "none", loads: "\u2014", fpsEffect: "\u2014", note: "" };
}

/* ---- active-compat helpers (upgrades the view when the simulator is on) ---- */
function activeCompat(g) {
  return (state.gpu && state.gpu !== "none" && g.upCompat) ? g.upCompat : g.compat;
}
function compatBadge(g) {
  var c = activeCompat(g);
  var suffix = "";
  if (state.gpu && state.gpu !== "none" && g.upCompat) {
    suffix = " \u00B7 + " + (window.UPGRADE_GPUS[state.gpu] ? window.UPGRADE_GPUS[state.gpu].short : "?");
  }
  return badge("compat-" + c.tier, COMPAT_KEY_LABEL[c.tier] + " (" + c.score + ")" + suffix);
}
/* Preset-aware FPS line for table/cards */
function presetLine(g, preset) {
  var b = g.bench || {};
  if (preset === "sixty") {
    return b.sixty ? b.sixty.fps : "\u2014";
  }
  if (preset === "quality30") {
    var q = window.getQuality30(g);
    return q ? q.fps1080 : "\u2014";
  }
  return b.playable ? b.playable.fps : "\u2014";
}

/* ---- detail modal ---- */
var _lastDetailTrigger = null;
function showDetail(game, triggerEl) {
  _lastDetailTrigger = triggerEl || document.activeElement;
  var el = document.getElementById("detail");
  var specsRow = function (label, min, rec) {
    return "<tr><th>" + esc(label) + "</th><td>" + esc(min) + "</td><td>" + esc(rec) + "</td></tr>";
  };
  var b = game.bench || {};
  var q30 = window.getQuality30(game);
  var sources = (game.sources || []).map(function (u) {
    var url = typeof u === "string" ? u : (u && u.url ? u.url : "");
    var label = typeof u === "string" ? u : (u && (u.source || u.url) ? (u.source || u.url) : "");
    if (!url) return "";
    return '<li><a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + esc(label) + "</a></li>";
  }).join("");
  var benchSrc = (b.source || []).map(function (u) {
    return '<li><a href="' + esc(u) + '" target="_blank" rel="noopener noreferrer">' + esc(u) + "</a></li>";
  }).join("");

  /* SP-on-HDD block */
  var sp = window.SP_HDD_LINE(game);
  var spBlock = blockClear(SP_LABEL_TITLE(game),
    "<p><strong>" + esc(sp.verdictLabel) + "</strong> &nbsp;\u00B7&nbsp; " + esc(sp.stutterLabel) + "</p>" +
    "<p>Load penalty: " + esc(sp.loads) + "</p>" +
    "<p>FPS effect: " + esc(sp.fpsEffect) + "</p>" +
    (sp.note ? "<p>" + esc(sp.note) + "</p>" : ""));

  /* SSD block */
  var diskVerdict = safeStorageVerdict(game);
  var ssd = window.ssdExpectation(game);
  var ssdBlock = blockClear("If I add an SSD \u2014 what changes? (" + DISK_LABEL[diskVerdict] + ")",
    "<p><strong>" + esc(ssd.head) + ".</strong> " + esc(ssd.body) + "</p>" +
    "<p>Base research: " + esc((game.storageAdvice && game.storageAdvice.note) || "") + "</p>");

  /* GPU-upgrade block */
  var gpuLines = Object.keys(window.UPGRADE_GPUS).map(function (k) {
    var u = window.upgradeVerdict(game, k);
    var isActive = state.gpu === k;
    return "<p" + (isActive ? ' class="gpu-active"' : "") + "><strong>" +
      esc(window.UPGRADE_GPUS[k].name + (isActive ? " (simulated)" : "")) + ":</strong> " +
      esc(u.lines.join(" ")) + "</p>";
  }).join("");
  var gpuBlock = blockClear("If I add a graphics card \u2014 expectations", gpuLines +
    '<p style="opacity:.7">fps figures are estimates; CPU-bound scenes remain limited by CPU speed.</p>');

  /* Progressive GPU Benchmark Scaling table (wired live to /api/games/benchmarks) */
  var benchRows = (window.GAME_BENCHMARKS_BY_ID && window.GAME_BENCHMARKS_BY_ID[game.id]) || [];
  var benchTableBlock = "";
  if (benchRows.length > 0) {
    var gpuOrder = ["vega-7-igpu", "rx-580-8gb", "gtx-1660-super", "rtx-2060-super", "rx-6600", "rtx-2070", "rtx-3060", "rtx-2070-super", "rtx-4060"];
    var orderedRows = benchRows.slice().sort(function (a, b) {
      var ia = gpuOrder.indexOf(a.gpu_id);
      var ib = gpuOrder.indexOf(b.gpu_id);
      if (ia !== -1 && ib !== -1 && ia !== ib) return ia - ib;
      return (a.avg_fps || 0) - (b.avg_fps || 0);
    });
    var tRows = orderedRows.map(function (r) {
      var meta = (window.GPU_META_BY_ID && window.GPU_META_BY_ID[r.gpu_id]) || window.UPGRADE_GPUS[r.gpu_id] || {};
      var gpuLabel = r.gpu_id === "vega-7-igpu" ? "Radeon Vega 7 iGPU (My PC)" : (meta.name || r.gpu_id);
      var psu = meta.psu_550w_verdict || meta.psuVerdict || "pass";
      var rowCls = r.gpu_id === state.gpu ? ' class="gpu-bench-active"' : (r.gpu_id === "vega-7-igpu" ? ' class="gpu-bench-base"' : "");
      var psuCls = psu === "fail" ? "compat-struggle" : (psu === "warn" ? "compat-ok" : "compat-great");
      var srcHtml = r.source_url ? '<a href="' + esc(r.source_url) + '" target="_blank" rel="noopener noreferrer">Ref</a>' : "\u2014";
      return "<tr" + rowCls + ">" +
        "<td><strong>" + esc(gpuLabel) + "</strong></td>" +
        "<td>" + esc(r.resolution) + "</td>" +
        "<td>" + esc(r.preset) + "</td>" +
        "<td class='fps-cell'><strong>" + esc(r.avg_fps) + " FPS</strong></td>" +
        "<td>" + esc(r.low_1pct_fps) + "</td>" +
        "<td>" + esc(r.low_01pct_fps) + "</td>" +
        "<td>" + badge(psuCls, psu.toUpperCase()) + "</td>" +
        "<td>" + srcHtml + "</td>" +
      "</tr>";
    }).join("");
    benchTableBlock =
      "<h3>Progressive GPU FPS Scaling (Ryzen 5 5600GT · 16 GB DDR4)</h3>" +
      "<div class='table-scroll' style='padding:0'><table class='specs-table'>" +
      "<thead><tr><th>GPU Configuration</th><th>Res</th><th>Preset</th><th>Avg FPS</th><th>1% Low</th><th>0.1% Low</th><th>550W PSU</th><th>Source</th></tr></thead>" +
      "<tbody>" + tRows + "</tbody></table></div>";
  }

  /* Companion / Test Server block */
  var companionsBlock = "";
  if (Array.isArray(game.companions) && game.companions.length > 0) {
    var compList = game.companions.map(function (cp) {
      return "<li><strong>" + esc(cp.name) + "</strong> (" + esc(cp.kind || "companion") + "): " + esc(cp.note || "Shares base requirements.") + "</li>";
    }).join("");
    companionsBlock = blockClear("Linked Test Servers &amp; Companion Entries", "<ul>" + compList + "</ul>");
  }

  /* Preset blocks */
  var presetBlock =
    blockClear("1080p on my Vega 7 \u2014 playable preset (~30\u201340 fps)",
      "<p><strong>" + esc(b.playable ? b.playable.fps : "\u2014") + "</strong></p><p>" + esc(b.playable ? b.playable.settings : "") + "</p>") +
    blockClear("Best graphics while holding ~30 fps",
      (q30 ?
        "<p><strong>1080p:</strong> " + esc(q30.fps1080) + "</p><p>" + esc(q30.settings1080) + "</p>" +
        "<p><strong>1600\u00D7900:</strong> " + esc(q30.fps900) + "</p><p>" + esc(q30.settings900) + "</p>"
        : "<p>\u2014</p>")) +
    blockClear("1080p on my Vega 7 \u2014 pushing ~60 fps",
      "<p><strong>" + esc(b.sixty ? b.sixty.fps : "\u2014") + "</strong></p><p>" + esc(b.sixty ? b.sixty.settings : "") + "</p>") +
    (benchSrc ? blockClear("FPS benchmark sources", "<ul class='sources'>" + benchSrc + "</ul>") : "") +
    blockClear("Buy / play on",
      "<div style='display:flex;flex-wrap:wrap;gap:6px'>" + storeBadges(game, 8) + "</div>" +
      "<p>" + esc(game.storeNote || "") + "</p>") +
    companionsBlock +
    blockClear("My-PC compatibility breakdown",
      "<ul>" + activeCompat(game).notes.map(function (n) { return "<li>" + esc(n) + "</li>"; }).join("") + "</ul>" +
      "<p>" + esc(game.compatNote || "") + "</p>");

  var c = activeCompat(game);
  var hddSp = safeHddSp(game);
  var camp = game.campaign || {};
  var ai = game.ai || {};
  var gfx = game.graphics || {};
  var pl = game.players || {};
  var sz = game.size || {};
  var specs = game.specs || { min: {}, rec: {} };

  el.innerHTML =
    '<div class="modal" role="dialog" aria-modal="true">' +
      '<div class="modal-inner">' +
        '<button class="modal-close" id="detailClose" type="button" aria-label="Close game details">\u00D7</button>' +
        "<h2>" + esc(game.name) + "</h2>" +
        '<div class="badges-row">' +
          ownershipBadge(game) +
          badge("g-" + game.genre, GENRE_LABEL[game.genre] || game.genre) +
          badge("g-norm", SETTING_LABEL[game.setting] || game.setting) +
          badge(game.priceModel === "f2p" ? "g-free" : "g-norm", game.priceModel === "f2p" ? "Free to play" : "Paid (" + fmtPrice(game) + ")") +
          badge("compat-" + c.tier, COMPAT_KEY_LABEL[c.tier] + " \u2014 " + c.score + "/100" +
            (state.gpu && state.gpu !== "none" && game.upCompat ? " \u00B7 " + window.UPGRADE_GPUS[state.gpu].short + " sim" : "")) +
          badge("disk-" + diskVerdict, DISK_LABEL[diskVerdict]) +
          badge("g-norm", window.HDDSP_LABEL[hddSp.verdict] || "") +
        "</div>" +

        '<div class="detail-grid">' +
          blockClear("Price", esc(game.priceNote || (game.priceUsd ? "$" + game.priceUsd : "Free"))) +
          blockClear("Campaign / Story", esc(formatCampaignLabel(camp.freeOrPaid)) +
            (camp.exists === false ? "" : " \u2014 quality " + (camp.quality || 0) + "/10 " + bar(camp.quality || 0)) +
            "<p>" + esc(camp.notes || "") + "</p>") +
          blockClear("AI / Bots / Enemies", (ai.score || 0) + "/10 " + bar(ai.score || 0) + "<p>" + esc(ai.notes || "") + "</p>") +
          blockClear("Graphics", (gfx.score || 0) + "/10 " + bar(gfx.score || 0) + "<p>" + esc(gfx.notes || "") + "</p>") +
          blockClear("Player base (" + (PLAYER_LABEL[pl.status] || pl.status || "Active") + ")", "<p>" + esc(pl.notes || "") + "</p>") +
          blockClear("Size", "Download: " + esc(sz.download || "\u2014") + " <br> Install: " + esc(sz.install || "\u2014")) +
          spBlock +
          ssdBlock +
          gpuBlock +
          presetBlock +
        "</div>" +

        "<h3>System requirements</h3>" +
        '<table class="specs-table"><thead><tr><th></th><th>Minimum</th><th>Recommended</th></tr></thead><tbody>' +
          specsRow("CPU", specs.min.cpu, specs.rec.cpu) +
          specsRow("GPU", specs.min.gpu, specs.rec.gpu) +
          specsRow("RAM", specs.min.ram, specs.rec.ram) +
          specsRow("Storage", specs.min.storage, specs.rec.storage) +
          specsRow("OS", specs.min.os, specs.rec.os) +
        "</tbody></table>" +

        benchTableBlock +

        "<h3>CPU / GPU demand on my PC</h3>" +
        "<p>CPU load: <strong>" + esc(CPU_LABEL[game.cpuDemand] || game.cpuDemand) + "</strong> &nbsp;\u00B7&nbsp; Min GPU tier: <strong>" +
        esc(game.gpuMinTier) + "</strong> / 10 \u00B7 Recommended GPU tier: <strong>" + esc(game.gpuRecTier) + "</strong> / 10<br>" +
        '<em style="opacity:.7">Vega 7 iGPU \u2248 tier 3 \u00B7 GTX 1060 / RX 580 \u2248 5.2 \u00B7 GTX 1660S \u2248 6.5 \u00B7 RTX 2060 \u2248 7 \u00B7 RX 6600 \u2248 7.5. HDD penalty depends on install size and streaming load.</em></p>' +

        "<h3>Sources</h3><ul class='sources'>" + sources + "</ul>" +
      "</div>" +
    "</div>";
  el.classList.add("open");
  var closeBtn = document.getElementById("detailClose");
  closeBtn.onclick = hideDetail;
  closeBtn.focus();
  el.onclick = function (e) { if (!e.target.closest(".modal-inner")) hideDetail(); };
}
function SP_LABEL_TITLE(game) {
  var v = safeHddSp(game).verdict;
  if (v === "fine") return "Single-player on my HDD \u2014 disruption?";
  if (v === "slower-loads") return "Single-player on my HDD \u2014 slower loads (which I don't mind)";
  return "Single-player on my HDD \u2014 stutter warning";
}
function hideDetail() {
  var el = document.getElementById("detail");
  if (!el.classList.contains("open")) return;
  el.classList.remove("open");
  el.innerHTML = "";
  if (_lastDetailTrigger && typeof _lastDetailTrigger.focus === "function") {
    _lastDetailTrigger.focus();
  }
  _lastDetailTrigger = null;
}
function renderEmptyState() {
  return '<div class="empty-state" role="status"><p>No games match your current filters.</p><button id="emptyReset" type="button">Reset filters</button></div>';
}
function blockClear(label, inner) {
  return '<div class="block"><strong>' + esc(label) + "</strong><div>" + inner + "</div></div>";
}
function fmtPrice(game) {
  return game.priceUsd ? "$" + game.priceUsd : "Free";
}

/* ---- table view ---- */
function renderTable(games) {
  if (!games || games.length === 0) return renderEmptyState();
  var preset = (typeof state !== "undefined" && state.preset) || "playable";
  var head = "<thead><tr>" +
    "<th>Game</th><th>Status</th><th>Price</th><th>Genre</th><th>Setting</th><th>Campaign</th>" +
    "<th>Campaign \u2605</th><th>AI \u2605</th><th>Graphics \u2605</th><th>Players</th>" +
    "<th>Install</th><th>" + esc(PRESET_LABEL[preset] || "1080p \u00B7 Vega 7") + "</th><th>SP on HDD</th><th>My PC</th></tr></thead>";
  var rows = games.map(function (g) {
    var diskVerdict = safeStorageVerdict(g);
    var hddSp = safeHddSp(g);
    var camp = g.campaign || {};
    var ai = g.ai || {};
    var gfx = g.graphics || {};
    var pl = g.players || {};
    var sz = g.size || {};
    return "<tr class='row' tabindex='0' role='button' data-id='" + esc(g.id) + "' title='Click or press Enter for details'>" +
      "<td class='strong'>" + esc(g.name) + "</td>" +
      "<td>" + ownershipBadge(g) + "</td>" +
      "<td>" + (g.priceModel === "f2p" ? badge("g-free", "F2P") : "$" + esc(g.priceUsd)) + "</td>" +
      "<td>" + esc(GENRE_LABEL[g.genre] || g.genre) + "</td>" +
      "<td>" + esc(SETTING_LABEL[g.setting] || g.setting) + "</td>" +
      "<td>" + (camp.exists ? esc(formatCampaignLabel(camp.freeOrPaid)) : "None") + "</td>" +
      "<td>" + (camp.quality || 0) + bar(camp.quality || 0) + "</td>" +
      "<td>" + (ai.score || 0) + bar(ai.score || 0) + "</td>" +
      "<td>" + (gfx.score || 0) + bar(gfx.score || 0) + "</td>" +
      "<td>" + esc(PLAYER_LABEL[pl.status] || pl.status || "Active") + "</td>" +
      "<td>" + esc(sz.install || (g.installGB + " GB")) + " " + badge("disk-" + diskVerdict, DISK_LABEL[diskVerdict]) + "</td>" +
      "<td class='fps-cell'>" + esc(presetLine(g, preset)) + "</td>" +
      "<td class='fps-cell'>" + esc((window.HDDSP_LABEL[hddSp.verdict] || "").replace("SP on HDD: ", "")) +
        (hddSp.stutter !== "none" ? " \u00B7 " + esc(hddSp.stutter) + " stutter" : "") + "</td>" +
      "<td>" + compatBadge(g) + "</td>" +
    "</tr>";
  }).join("");
  return "<div class='table-scroll'><table class='games-table'>" + head + "<tbody>" + rows + "</tbody></table></div>";
}

/* ---- cards view ---- */
function renderCards(games) {
  if (!games || games.length === 0) return renderEmptyState();
  var preset = (typeof state !== "undefined" && state.preset) || "playable";
  return "<div class='cards'>" + games.map(function (g) {
    var c = activeCompat(g);
    var diskVerdict = safeStorageVerdict(g);
    var hddSp = safeHddSp(g);
    var camp = g.campaign || {};
    var ai = g.ai || {};
    var gfx = g.graphics || {};
    var pl = g.players || {};
    var sz = g.size || {};
    return "<div class='card compat-border-" + c.tier + " row' tabindex='0' role='button' data-id='" + esc(g.id) + "'>" +
      "<div class='card-h'>" +
        "<h3>" + esc(g.name) + "</h3>" +
        compatBadge(g) +
      "</div>" +
      "<div class='badges-row'>" +
        ownershipBadge(g) +
        badge("g-" + g.genre, GENRE_LABEL[g.genre] || g.genre) +
        badge("g-norm", SETTING_LABEL[g.setting] || g.setting) +
        badge(g.priceModel === "f2p" ? "g-free" : "g-norm", g.priceModel === "f2p" ? "F2P" : (g.priceUsd ? "$" + g.priceUsd : "Included")) +
        badge("disk-" + diskVerdict, DISK_LABEL[diskVerdict]) +
        (hddSp.stutter !== "none" ? badge("g-warn", window.STUTTER_LABEL[hddSp.stutter] || hddSp.stutter) : "") +
        (Array.isArray(g.companions) && g.companions.length ? badge("g-norm", "+" + g.companions.length + " Test/Pass") : "") +
      "</div>" +
      "<div class='card-meta'>" +
        "<div><span>Campaign</span>" + (camp.exists ? esc(formatCampaignLabel(camp.freeOrPaid)) + " \u2014 " + (camp.quality || 0) + "/10" : "None") + "</div>" +
        "<div><span>AI</span>" + (ai.score || 0) + "/10 &nbsp;<span>Graphics</span>" + (gfx.score || 0) + "/10</div>" +
        "<div><span>" + esc(PRESET_LABEL[preset] || "1080p") + "</span>" + esc(presetLine(g, preset)) + "</div>" +
        "<div><span>SP on HDD</span>" + esc((window.HDDSP_LABEL[hddSp.verdict] || "").replace("SP on HDD: ", "")) + "</div>" +
        "<div><span>Players</span>" + esc(PLAYER_LABEL[pl.status] || pl.status || "Active") + "</div>" +
        "<div><span>Install</span>" + esc(sz.install || (g.installGB + " GB")) + "</div>" +
        "<div class='stores-row'>" + storeBadges(g) + "</div>" +
      "</div>" +
    "</div>";
  }).join("") + "</div>";
}
