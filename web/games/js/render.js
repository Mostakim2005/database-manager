"use strict";
/* ==========================================================================
   GameRank — js/render.js
   Pure rendering functions: table rows, cards, detail modal, badges.
   No event logic here — see js/app.js.
   v3.0.0:
     - preset-aware FPS columns (playable / 60fps / graphics@30 in 1080p+900p)
     - single-player-on-HDD block (stutter-focused)
     - "If I add an SSD" block (framed around stutter, not load times)
     - GPU-upgrade simulator badges + per-card upgrade expectations
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
var SETTING_LABEL = {
  "ancient": "Ancient / History",
  "realistic-modern": "Realistic / Modern",
  "futuristic": "Futuristic / Sci-Fi",
  "fantasy": "Fantasy"
};
var GENRE_LABEL = {
  "classic-rts": "Classic RTS",
  "4x-grand": "4X / Grand Strategy",
  "hybrid-td": "Hybrid / Tower Defense",
  "army-sim": "Army / Settlement Sim"
};
var PLAYER_LABEL = {
  "very-active": "Very active \u{1F525}",
  "active": "Active",
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
  var pct = Math.max(0, Math.min(100, (val / 10) * 100));
  return '<span class="bar"><span class="bar-fill" style="width:' + pct + '%"></span></span>';
}

/* ---- small badge (cls + text; optional href makes it a link) ---- */
function badge(cls, text, href) {
  var inner = esc(text);
  if (href) inner = '<a href="' + esc(href) + '" target="_blank" rel="noopener noreferrer">' + inner + "</a>";
  return '<span class="badge ' + cls + '">' + inner + "</span>";
}
var storeBadges = function (game, max) {
  return (game.stores || []).slice(0, max || 2).map(function (s) {
    return badge("g-store", s.name, s.url);
  }).join(" ");
};

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
    return '<li><a href="' + esc(u) + '" target="_blank" rel="noopener noreferrer">' + esc(u) + "</a></li>";
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
  var ssd = window.ssdExpectation(game);
  var ssdBlock = blockClear("If I add an SSD \u2014 what changes? (" + DISK_LABEL[game.storageAdvice.verdict] + ")",
    "<p><strong>" + esc(ssd.head) + ".</strong> " + esc(ssd.body) + "</p>" +
    "<p>Base research: " + esc(game.storageAdvice.note) + "</p>");

  /* GPU-upgrade block (all three cards, active one highlighted) */
  var gpuLines = Object.keys(window.UPGRADE_GPUS).map(function (k) {
    var u = window.upgradeVerdict(game, k);
    var isActive = state.gpu === k;
    return "<p" + (isActive ? ' class="gpu-active"' : "") + "><strong>" +
      (window.UPGRADE_GPUS[k].name + (isActive ? " (simulated)" : "")) + ":</strong> " +
      esc(u.lines.join(" ")) + "</p>";
  }).join("");
  var gpuBlock = blockClear("If I add a graphics card \u2014 expectations", gpuLines +
    '<p style="opacity:.7">fps figures are estimates; big RTS battles stay CPU-bound regardless of GPU.</p>');

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
    blockClear("My-PC compatibility breakdown",
      "<ul>" + activeCompat(game).notes.map(function (n) { return "<li>" + esc(n) + "</li>"; }).join("") + "</ul>" +
      "<p>" + esc(game.compatNote) + "</p>");

  var c = activeCompat(game);

  el.innerHTML =
    '<div class="modal" role="dialog" aria-modal="true">' +
      '<div class="modal-inner">' +
        '<button class="modal-close" id="detailClose" type="button" aria-label="Close game details">\u00D7</button>' +
        "<h2>" + esc(game.name) + "</h2>" +
        '<div class="badges-row">' +
          badge("g-" + game.genre, GENRE_LABEL[game.genre]) +
          badge("g-norm", SETTING_LABEL[game.setting]) +
          badge(game.priceModel === "f2p" ? "g-free" : "g-norm", game.priceModel === "f2p" ? "Free to play" : "Paid (" + fmtPrice(game) + ")") +
          badge("compat-" + c.tier, COMPAT_KEY_LABEL[c.tier] + " \u2014 " + c.score + "/100" +
            (state.gpu && state.gpu !== "none" && game.upCompat ? " \u00B7 " + window.UPGRADE_GPUS[state.gpu].short + " sim" : "")) +
          badge("disk-" + game.storageAdvice.verdict, DISK_LABEL[game.storageAdvice.verdict]) +
          badge("g-norm", window.HDDSP_LABEL[game.hddSp.verdict] || "") +
        "</div>" +

        '<div class="detail-grid">' +
          blockClear("Price", game.priceNote || (game.priceUsd ? "$" + game.priceUsd : "Free")) +
          blockClear("Campaign", esc(formatCampaignLabel(game.campaign.freeOrPaid)) +
            (game.campaign.exists === false ? "" : " \u2014 quality " + game.campaign.quality + "/10 " + bar(game.campaign.quality)) +
            "<p>" + esc(game.campaign.notes) + "</p>") +
          blockClear("Campaign / Skirmish AI", game.ai.score + "/10 " + bar(game.ai.score) + "<p>" + esc(game.ai.notes) + "</p>") +
          blockClear("Graphics", game.graphics.score + "/10 " + bar(game.graphics.score) + "<p>" + esc(game.graphics.notes) + "</p>") +
          blockClear("Player base (" + PLAYER_LABEL[game.players.status] + ")", "<p>" + esc(game.players.notes) + "</p>") +
          blockClear("Size", "Download: " + esc(game.size.download) + " <br> Install: " + esc(game.size.install)) +
          spBlock +
          ssdBlock +
          gpuBlock +
          presetBlock +
        "</div>" +

        "<h3>System requirements</h3>" +
        '<table class="specs-table"><thead><tr><th></th><th>Minimum</th><th>Recommended</th></tr></thead><tbody>' +
          specsRow("CPU", game.specs.min.cpu, game.specs.rec.cpu) +
          specsRow("GPU", game.specs.min.gpu, game.specs.rec.gpu) +
          specsRow("RAM", game.specs.min.ram, game.specs.rec.ram) +
          specsRow("Storage", game.specs.min.storage, game.specs.rec.storage) +
          specsRow("OS", game.specs.min.os, game.specs.rec.os) +
        "</tbody></table>" +

        "<h3>CPU / GPU demand on my PC</h3>" +
        "<p>CPU load: <strong>" + (CPU_LABEL[game.cpuDemand] || game.cpuDemand) + "</strong> &nbsp;\u00B7&nbsp; Min GPU tier: <strong>" +
        game.gpuMinTier + "</strong> / 10 \u00B7 Recommended GPU tier: <strong>" + game.gpuRecTier + "</strong> / 10<br>" +
        '<em style="opacity:.7">Vega 7 iGPU \u2248 tier 3 \u00B7 GTX 1660S \u2248 6.5 \u00B7 RTX 2060 \u2248 7 \u00B7 RX 6600 \u2248 7.5. HDD penalty depends on install size and streaming load.</em></p>' +

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
  var v = game.hddSp.verdict;
  if (v === "fine") return "Single-player only, on my HDD \u2014 disruption?";
  if (v === "slower-loads") return "Single-player only, on my HDD \u2014 slower loads (which I don't mind)";
  return "Single-player only, on my HDD \u2014 stutter warning";
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
    "<th>Game</th><th>Price</th><th>Genre</th><th>Setting</th><th>Campaign</th>" +
    "<th>Campaign \u2605</th><th>AI \u2605</th><th>Graphics \u2605</th><th>Players</th>" +
    "<th>Install</th><th>" + esc(PRESET_LABEL[preset] || "1080p \u00B7 Vega 7") + "</th><th>SP on HDD</th><th>My PC</th></tr></thead>";
  var rows = games.map(function (g) {
    var c = activeCompat(g);
    return "<tr class='row' tabindex='0' role='button' data-id='" + esc(g.id) + "' title='Click or press Enter for details'>" +
      "<td class='strong'>" + esc(g.name) + "</td>" +
      "<td>" + (g.priceModel === "f2p" ? badge("g-free", "F2P") : "$" + g.priceUsd) + "</td>" +
      "<td>" + esc(GENRE_LABEL[g.genre]) + "</td>" +
      "<td>" + esc(SETTING_LABEL[g.setting]) + "</td>" +
      "<td>" + (g.campaign.exists ? esc(formatCampaignLabel(g.campaign.freeOrPaid)) : "None") + "</td>" +
      "<td>" + g.campaign.quality + bar(g.campaign.quality) + "</td>" +
      "<td>" + g.ai.score + bar(g.ai.score) + "</td>" +
      "<td>" + g.graphics.score + bar(g.graphics.score) + "</td>" +
      "<td>" + esc(PLAYER_LABEL[g.players.status]) + "</td>" +
      "<td>" + esc(g.size.install) + " " + badge("disk-" + g.storageAdvice.verdict, DISK_LABEL[g.storageAdvice.verdict]) + "</td>" +
      "<td class='fps-cell'>" + esc(presetLine(g, preset)) + "</td>" +
      "<td class='fps-cell'>" + esc(window.HDDSP_LABEL[g.hddSp.verdict].replace("SP on HDD: ", "")) +
        (g.hddSp.stutter !== "none" ? " \u00B7 " + esc(g.hddSp.stutter) + " stutter" : "") + "</td>" +
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
    return "<div class='card compat-border-" + c.tier + " row' tabindex='0' role='button' data-id='" + esc(g.id) + "'>" +
      "<div class='card-h'>" +
        "<h3>" + esc(g.name) + "</h3>" +
        compatBadge(g) +
      "</div>" +
      "<div class='badges-row'>" +
        badge("g-" + g.genre, GENRE_LABEL[g.genre]) +
        badge("g-norm", SETTING_LABEL[g.setting]) +
        badge(g.priceModel === "f2p" ? "g-free" : "g-norm", g.priceModel === "f2p" ? "F2P" : "$" + g.priceUsd) +
        badge("disk-" + g.storageAdvice.verdict, DISK_LABEL[g.storageAdvice.verdict]) +
        (g.hddSp.stutter !== "none" ? badge("g-warn", window.STUTTER_LABEL[g.hddSp.stutter]) : "") +
      "</div>" +
      "<div class='card-meta'>" +
        "<div><span>Campaign</span>" + (g.campaign.exists ? esc(formatCampaignLabel(g.campaign.freeOrPaid)) + " \u2014 " + g.campaign.quality + "/10" : "None") + "</div>" +
        "<div><span>AI</span>" + g.ai.score + "/10 &nbsp;<span>Graphics</span>" + g.graphics.score + "/10</div>" +
        "<div><span>" + esc(PRESET_LABEL[preset] || "1080p") + "</span>" + esc(presetLine(g, preset)) + "</div>" +
        "<div><span>SP on HDD</span>" + esc(window.HDDSP_LABEL[g.hddSp.verdict].replace("SP on HDD: ", "")) + "</div>" +
        "<div><span>Players</span>" + esc(PLAYER_LABEL[g.players.status]) + "</div>" +
        "<div><span>Install</span>" + esc(g.size.install) + "</div>" +
        "<div class='stores-row'>" + storeBadges(g) + "</div>" +
      "</div>" +
    "</div>";
  }).join("") + "</div>";
}
