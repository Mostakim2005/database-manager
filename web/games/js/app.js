"use strict";
/* ==========================================================================
   GameRank — js/app.js
   Boot + all UI event logic (filters, sorting, view toggle, stats, modal).
   Rendering helpers live in js/render.js.
   v3.0.0 adds:
     - state.gpu  : GPU-upgrade simulator ('none' | 'gtx1660s' | 'rtx2060' | 'rx6600')
     - state.preset : which settings preset the FPS columns show
       ('playable' | 'quality30' | 'sixty')
     - compat filtering/sorting/stats use the ACTIVE (simulated) verdict
   ========================================================================== */

window.state = {
  search: "",
  genre: "all",
  setting: "all",
  price: "all",
  campaign: "all",
  compat: "all",
  players: "all",
  preset: "playable",
  gpu: "none",
  sort: "compat",
  dir: "desc",
  view: "cards"
};

document.addEventListener("DOMContentLoaded", function () {
  applyCompat(window.GAMES);
  wireFilters();
  update();
});

function wireFilters() {
  var $ = function (id) { return document.getElementById(id); };
  $("search").addEventListener("input", function (e) { state.search = e.target.value; update(); });
  ["genre", "setting", "price", "campaign", "compat", "players", "preset", "gpu", "sort", "view"].forEach(function (k) {
    $(k).addEventListener("change", function (e) {
      state[k] = e.target.value;
      if (k === "sort") {
        /* keep current dir; sensible default direction switch */
        state.dir = ["name", "size", "price"].indexOf(state.sort) >= 0 ? "asc" : "desc";
      }
      if (k === "gpu") {
        /* recompute simulated verdicts for when the simulator is on */
        window.GAMES.forEach(function (g) {
          g.upCompat = state.gpu === "none" ? null : window.computeUpgradedCompat(g, state.gpu);
        });
      }
      update();
    });
  });
  $("dirBtn").addEventListener("click", function () {
    state.dir = state.dir === "asc" ? "desc" : "asc";
    update();
  });
  $("reset").addEventListener("click", function () {
    Object.assign(state, { search: "", genre: "all", setting: "all", price: "all",
      campaign: "all", compat: "all", players: "all", preset: "playable", gpu: "none",
      sort: "compat", dir: "desc" });
    window.GAMES.forEach(function (g) { g.upCompat = null; });
    $("search").value = "";
    ["genre", "setting", "price", "campaign", "compat", "players", "preset", "gpu", "sort", "view"]
      .forEach(function (k) { $(k).value = state[k]; });
    update();
  });
  /* table / card click -> detail modal */
  document.getElementById("results").addEventListener("click", function (e) {
    var row = e.target.closest(".row");
    if (!row) return;
    var g = window.GAMES.find(function (x) { return x.id === row.getAttribute("data-id"); });
    if (g) showDetail(g);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hideDetail();
  });
}

/* Verdict actually shown (base, or simulated-when-a-GPU-is-selected) */
function activeTier(g) {
  return (state.gpu !== "none" && g.upCompat) ? g.upCompat : g.compat;
}

/* Filtering + sorting */
function currentGames() {
  var q = state.search.trim().toLowerCase();
  var out = window.GAMES.filter(function (g) {
    if (q && (g.name.toLowerCase().indexOf(q) < 0)) return false;
    if (state.genre !== "all" && g.genre !== state.genre) return false;
    if (state.setting !== "all" && g.setting !== state.setting) return false;
    if (state.price !== "all") {
      if (state.price === "f2p" && g.priceModel !== "f2p") return false;
      if (state.price === "cheap" && (g.priceModel === "f2p" || g.priceUsd > 15)) return false;
      if (state.price === "any" && g.priceModel === "f2p") return false;
    }
    if (state.campaign !== "all") {
      if (state.campaign === "yes" && !g.campaign.exists) return false;
      if (state.campaign === "free" && g.campaign.freeOrPaid !== "free") return false;
      if (state.campaign === "none" && g.campaign.exists) return false;
    }
    if (state.compat !== "all" && activeTier(g).tier !== state.compat) return false;
    if (state.players !== "all") {
      var s = g.players.status;
      if (state.players === "mp-active" && ["very-active", "active"].indexOf(s) < 0) return false;
      if (state.players === "mp-any" && s === "n/a-sp") return false;
      if (state.players === "sp-only" && s !== "n/a-sp") return false;
    }
    return true;
  });

  var sorters = {
    compat:   function (a, b) { return activeTier(a).score - activeTier(b).score; },
    campaign: function (a, b) { return a.campaign.quality - b.campaign.quality; },
    ai:       function (a, b) { return a.ai.score - b.ai.score; },
    graphics: function (a, b) { return a.graphics.score - b.graphics.score; },
    name:     function (a, b) { return a.name.localeCompare(b.name); },
    size:     function (a, b) { return (a.installGB || 0) - (b.installGB || 0); },
    price:    function (a, b) { return a.priceUsd - b.priceUsd; },
    players:  function (a, b) {
      var order = ["very-active", "active", "small", "inactive", "n/a-sp"];
      return order.indexOf(b.players.status) - order.indexOf(a.players.status);
    }
  };
  var cmp = sorters[state.sort] || sorters.compat;
  out.sort(function (a, b) { return state.dir === "asc" ? cmp(a, b) : -cmp(a, b); });
  return out;
}

function update() {
  var games = currentGames();
  var $ = function (id) { return document.getElementById(id); };

  /* board header stats — uses the ACTIVE (simulated) verdict */
  var total = window.GAMES.length;
  var great = window.GAMES.filter(function (g) { return activeTier(g).tier === "great"; }).length;
  var f2p   = window.GAMES.filter(function (g) { return g.priceModel === "f2p"; }).length;
  var gpuTxt = state.gpu !== "none" && window.UPGRADE_GPUS[state.gpu]
    ? " \u00B7 simulating <strong>" + window.UPGRADE_GPUS[state.gpu].name + "</strong>"
    : "";
  $("stats").innerHTML =
    "<strong>" + great + "</strong> of <strong>" + total + "</strong> games run great on your PC" + gpuTxt +
    " \u00B7 <strong>v3.0.0</strong> \u00B7 " +
    "<strong>" + f2p + "</strong> are free \u00B7 showing <strong>" + games.length + "</strong> result(s)";

  $("results").innerHTML =
    state.view === "table" ? renderTable(games) : renderCards(games);

  /* result count label in toolbar */
  $("count").textContent = games.length + " / " + total + " games";
}
